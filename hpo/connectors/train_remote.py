import json
import time
import sys
import copy

import numpy as np
import math

from commons.logger import *

from commons.proto import TrainerPrototype
from hpo.connectors.remote_ctrl import RemoteJobConnector


def init(url, run_config, hp_config, hpvs, **kwargs):
    try:
        cred = run_config["credential"]
        rtc = RemoteTrainConnector(url, hp_config, cred, **kwargs)
        if run_config and "auto_early_stop" in run_config:
            shaping_func = None
            if "log" in run_config and run_config["log"]["log_err"]:
                if "log_err_func" in run_config["log"]:
                    shaping_func = run_config["log"]["log_err_func"]
                    return LogErrorGradientEarlyStopTrainer(rtc, hpvs, shaping_func)  
            
            return GradientEarlyStopTrainer(rtc, hpvs, shaping_func)

        return NoEarlyStopTrainer(rtc, hpvs)

    except Exception as ex:
        warn("early stop trainer creation failed: {}".format(ex))
        raise ValueError("Invalid trainer implementation")


class RemoteTrainConnector(RemoteJobConnector):
    
    def __init__(self, url, hp_config, cred, **kwargs):

        super(RemoteTrainConnector, self).__init__(url, cred, **kwargs)
        
        self.hp_config = hp_config
 
    def validate(self):
        try:
            profile = self.get_profile()
            
            if "spec" in profile and "job_type" in profile["spec"]:
                debug("Remote worker profile: {}".format(profile["spec"]))
                if profile["spec"]["job_type"] == "ML_trainer":
                    config = self.get_config()
                    if "run_config" in config and "target_func" in config["run_config"]:                
                        if config["run_config"]["target_func"] == 'surrogate':
                            return True  # skip parameter validation process
                    if "hp_config" in config:        
                        return self.compare_config(self.hp_config.get_dict(), 
                                                config["hp_config"]) 

        except Exception as ex:
            warn("Validation failed: {}".format(ex))
            
        return False

    def compare_config(self, origin, target):
        try:
            if "hyperparams" in origin and "hyperparams" in target:
                hps = origin["hyperparams"]
                ths = target["hyperparams"]
                # XXX:Check hyperparameter name only
                for k in hps.keys():
                    if not k in ths:
                        return False
                
                return True
        except Exception as ex:
            warn("Configuration comparision failed: {}\n{}\n{}".format(ex, origin, target))

        return False

    def create_job(self, hyperparams, config=None):
        try:
            #debug("RemoteTrainConnector tries to create a training job.")
            job_desc = copy.copy(self.hp_config._dict)
            # update body by hyperparams
            for hp in hyperparams.keys():
                value = hyperparams[hp]
                if hp in job_desc['hyperparams']: 
                    job_desc['hyperparams'][hp] = value
                else:
                    warn("{} is not the valid parameter of the given objective function".format(hp))
                    return None
            
            if config is not None:
                for key in config.keys():
                    job_desc['config'][key] = config[key]

            return super(RemoteTrainConnector, self).create_job(job_desc)

        except Exception as ex:
            warn("Create job failed: {}".format(ex))
            return None


class RemoteTrainer(TrainerPrototype):
    def __init__(self, connector, hpvs, 
                base_error=0.9, polling_interval=5, max_timeout= 100, min_train_epoch=1):

        self.hpvs = hpvs
        self.hp_config = connector.hp_config

        self.controller = connector
        self.base_error = base_error

        self.jobs = {}
        self.history = []
        self.early_stopped = []
        self.min_train_epoch = min_train_epoch
        self.max_timeout = max_timeout
        self.polling_interval = polling_interval
    
    def reset(self):
        self.jobs = {}
        self.history = []
        self.early_stopped = []

    def stop_early(self, curve, est):
        raise NotImplementedError("Stopping mechanism should be implemented. Returns True or False here.")

    def wait_until_done(self, job_id, model_index, estimates, space):

        acc_curve = None
        prev_interim_err = None
        time_out_count = 0
        while True: # XXX: infinite loop
            try:
                j = self.controller.get_job("active")
                if j != None:
                    if "losses" in j and len(j["losses"]) > 0:
                        acc_curve = [ 1.0 - loss for loss in j["losses"] ]
                        
                        # Interim error update
                        interim_err = j["losses"][-1]
                        if prev_interim_err == None or prev_interim_err != interim_err:
                            debug("Interim error {} will be updated".format(interim_err))
                            space.update(model_index, interim_err)
                        
                        prev_interim_err = interim_err
                        
                        # Early stopping check
                        if self.min_train_epoch < len(acc_curve) and \
                            self.stop_early(acc_curve, estimates):                        
                            job_id = j['job_id']
                            debug("This job will be early stopped")
                            self.controller.stop(job_id)
                            break

                    elif "losses" in j and len(j["losses"]) == 0:
                        pass
                    else:
                        warn("Invalid job result: {}".format(j))
                elif j == None:
                    # cross check 
                    r = self.controller.get_job(job_id)
                    if "losses" in r:
                        num_losses = len(r["losses"])
                        debug("Current working job finished with {} losses.".format(num_losses))
                        break 
                
                #debug("Waiting {} sec...".format(self.polling_interval)) 
                time.sleep(self.polling_interval)
            
            except Exception as ex:
                if str(ex) == 'timed out':
                    time_out_count += 1                    
                    if time_out_count < self.max_timeout:
                        debug("Timeout occurred. Retry {}/{}...".format(time_out_count, self.max_timeout))
                        continue

                warn("Something goes wrong in remote worker: {}".format(ex))
                break


    def train(self, space, cand_index, estimates=None):
        hpv = {}
        cfg = { 'cand_index' : cand_index }
        param_names = self.hp_config.get_hyperparams()
        debug("Training HPV: {}".format(self.hpvs[cand_index]))
        for param in param_names:
            value = self.hpvs[cand_index][param]
            hpv[param] = value

        if self.controller.validate():
            job_id = self.controller.create_job(hpv, cfg)
            if job_id is not None:                
                if self.controller.start(job_id):
                    
                    self.jobs[job_id] = {"cand_index" : cand_index, "status" : "run"}
                    
                    self.wait_until_done(job_id, cand_index, estimates, space)

                    result = self.controller.get_job(job_id)
                   
                    self.jobs[job_id]["result"] = result
                    self.jobs[job_id]["status"] = "done"
                    
                    acc_curve = [ 1.0 - loss for loss in result["losses"] ]
                    if acc_curve != None:
                        self.history.append(acc_curve) 

                    return result['cur_loss'], result['run_time']

                else:
                    error("Starting training job failed.")
            else:
                error("Creating job failed")
            
        else:
            error("Invalid setting: configurations between controller and worker are not same.")
        
        raise ValueError("Remote training failed")       

    def find_job_id(self, cand_index):
        for j in self.jobs.keys():
            if cand_index == self.jobs[j]['cand_index']:
                return j
        else:
            return None

    def get_interim_error(self, model_index, cur_dur):
        job_id = self.find_job_id(model_index)
        if job_id is not None:
            if self.controller.get_job("active") != None:
                result = self.controller.get_job(job_id)
                self.jobs[job_id]["result"] = result

                return result['cur_loss']
            else:
                debug("This job {} may be already finished.".format(job_id))
                return self.jobs[job_id]["result"]['cur_loss']
        
        return self.base_error


class NoEarlyStopTrainer(RemoteTrainer):
    def __init__(self, controller, hpvs):
        super(NoEarlyStopTrainer, self).__init__(controller, hpvs)

    def stop_early(self, acc_curve, estimates):
        return False


class GradientEarlyStopTrainer(NoEarlyStopTrainer):
    
    def __init__(self, controller, hpvs, shaping_func=None):

        if shaping_func:
            self.shaping_func = shaping_func
        else:
            self.shaping_func = self.no_shaping
        super(GradientEarlyStopTrainer, self).__init__(controller, hpvs)

    def no_shaping(self, means):
        return means

    def get_gradient_average(self, acc_curve, num_step):

        acc_delta = []
        num_grads = len(acc_curve) - 1
        
        if num_grads < 2:
            return acc_curve[0]
        
        for j in range(num_grads):
            delta = acc_curve[j+1] - acc_curve[j]
            acc_delta.append(delta)
        avg_deltas =  sum(acc_delta) / num_grads
        #debug("delta average: {:.5f}, delta list: {}".format(avg_deltas, [round(d, 5) for d in acc_delta]))         
        return avg_deltas

    def stop_early(self, acc_curve, estimates):
        if estimates is None:
            self.early_stopped.append(False)
            return False
        else:
            candidates = estimates['candidates']
            acq_funcs = estimates['acq_funcs']
            means = estimates['means']
            vars = estimates['vars']        
        
            i_max = np.argmax(acq_funcs)
            v_max = acq_funcs[i_max]
            #print("max {} ({})".format(v_max, i_max))
            m = means[i_max]
            s = math.sqrt(vars[i_max])
        
            est_acc_mean = 1 - self.shaping_func(m)
            #debug("estimated mean: {:.4f}, stdev: {:.4f}".format(est_acc_mean, s))        
            acc_delta = 0
            cur_max_acc = 0
            
            max_epoch = 100
            try:
                max_epoch = self.hp_config.config.max_epoch
            except Exception as ex:
                pass

            for i in range(len(acc_curve)):
                acc = acc_curve[i]
                obs_n = i - 1
                if acc > cur_max_acc:
                    cur_max_acc = acc

                reduced_s = (s - s / max_epoch * i)
                lower_bound = est_acc_mean # - self.coefficient * reduced_s
                # dynamic stdev decrease
                
                min_delta = (est_acc_mean - acc) / (max_epoch - i)
                #debug("current accuracy: {:.4f}, lower bound: {:.4f}".format(acc, lower_bound))
                #debug("est. mean acc: {:.4f}, min delta: {:.4f}".format(est_acc_mean - acc, min_delta))
                if acc < lower_bound and min_delta > self.get_gradient_average(acc_curve, i):
                    debug("Early stopped curve: {}".format( [round(acc, 5) for acc in acc_curve]))
                    self.early_stopped.append(True)
                    return True
        
        self.early_stopped.append(False)
        return False                     


class LogErrorGradientEarlyStopTrainer(GradientEarlyStopTrainer):

    def __init__(self, controller, hpvs, log_func_type):
        if log_func_type == "ada_log_3":
            log_func = self.transform_hybrid_log
            super(LogErrorGradientEarlyStopTrainer, self).__init__(controller, hpvs, log_func)
        else:
            raise NotImplementedError()


    def transform_hybrid_log(self, err, threshold=0.3):
        if err > threshold:
            return err
        else:
            moved = err - (threshold - math.log10(threshold))
            unscaled = 10**(moved)
            return unscaled



