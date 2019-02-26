from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import time
import copy

import numpy as np
import math

from ws.shared.logger import *
from ws.shared.proto import TrainerPrototype

class RemoteTrainer(TrainerPrototype):
    def __init__(self, connector, space, **kwargs):


        self.space = space
        self.hp_config = connector.hp_config

        self.controller = connector

        self.jobs = {}
        self.history = []

        if "base_error" in kwargs:
            self.base_error = float(kwargs["base_error"])
        else:
            self.base_error = 0.9
        if "polling_interval" in kwargs:
            self.polling_interval = int(kwargs["polling_interval"])
        else:
            self.polling_interval = 5
        
        if "max_timeout" in kwargs:
            self.max_timeout = int(kwargs["max_timeout"])
        else:
            self.max_timeout = 100

        if "min_train_epoch" in kwargs:
            self.min_train_epoch = int(kwargs["min_train_epoch"])
        else:
            self.min_train_epoch = 1
        
        self.max_train_epoch = None
        
        if hasattr(self.hp_config, "config") and hasattr(self.hp_config.config, "max_epoch"):
            self.max_train_epoch = self.hp_config.config.max_epoch

        super(RemoteTrainer, self).__init__()
    
    def reset(self):
        self.jobs = {}
        self.history = []

    def check_termination_condition(self, acc_curve, estimates):
        # No termination check
        return False

    def wait_until_done(self, job_id, model_index, estimates, space):

        acc_curve = None
        prev_interim_err = None
        time_out_count = 0
        early_terminated = False
        while True: # XXX: infinite loop
            try:
                j = self.controller.get_job("active")
                if j != None:
                    if "lr" in j and len(j["lr"]) > 0:
                        acc_curve = [ acc for acc in j["lr"] ]
                        
                        # Interim error update
                        interim_err = j["lr"][-1]
                        if prev_interim_err == None or prev_interim_err != interim_err:
                            #debug("Interim error {} will be updated".format(interim_err))
                            if space != None:
                                space.update_error(model_index, interim_err, True)
                        
                        prev_interim_err = interim_err
                        if prev_interim_err != interim_err:
                            # XXX:reset time out count
                            time_out_count = 0 
                        else:
                            time_out_count += 1
                            if time_out_count > self.max_timeout:
                                log("Force to stop due to no update for {} sec".format(self.polling_interval * self.max_timeout * 10))
                                self.controller.stop(job_id)
                                early_terminated = True
                                break                                
                        
                        # Early termination check
                        if self.min_train_epoch < len(acc_curve) and \
                            self.check_termination_condition(acc_curve, estimates):                        
                            job_id = j['job_id']
                            #debug("This job will be terminated")
                            self.controller.stop(job_id)
                            early_terminated = True
                            break

                    elif "lr" in j and len(j["lr"]) == 0:
                        pass
                    else:
                        warn("Invalid job result: {}".format(j))
                elif j == None:
                    # cross check 
                    r = self.controller.get_job(job_id)
                    if "lr" in r:
                        num_accs = len(r["lr"])
                        if num_accs > 0:
                            debug("Current working job finished with accuracy {:.4f}.".format(max(r["lr"])))
                            break
                        else:
                            debug("Result of finished job: {}".format(r)) 
                
                #debug("Waiting {} sec...".format(self.polling_interval)) 
                time.sleep(self.polling_interval)
            
            except Exception as ex:
                if str(ex) == 'timed out':
                    time_out_count += 1                    
                    if time_out_count < self.max_timeout:
                        debug("Timeout occurred. Retry {}/{}...".format(time_out_count, self.max_timeout))
                        continue

                warn("Something goes wrong in remote worker: {}".format(ex))
                early_terminated = True
                break
        
        return early_terminated

    def train(self, cand_index, estimates=None, space=None):
        hpv = {}
        cfg = {'cand_index' : cand_index}
        param_names = self.hp_config.get_hyperparams()
        param_values = self.space.get_hpv(cand_index)
        if type(param_values) == np.ndarray:
             param_values = param_values.tolist()
        
        early_terminated = False
        #debug("Training using hyperparameters: {}".format(param_values))
        
        if type(param_values) == dict:
            for param in param_names:
                value = param_values[param]
                if self.hp_config.get_type(param) != 'str':
                    value = float(value)
                    if self.hp_config.get_type(param) == 'int':
                        value = int(value)
                hpv[param] = value
        elif type(param_values) == list and len(param_names) == len(param_values):
            for i in range(len(param_names)):
                param = param_names[i]
                value = param_values[i]
                if self.hp_config.get_type(param) != 'str':
                    value = float(value)
                    if self.hp_config.get_type(param) == 'int':
                        value = int(value)
                hpv[param] = value
        else:
            raise TypeError("Invalid hyperparams: {}/{}".format(param_names, param_values))

        if self.controller.validate():
            job_id = self.controller.create_job(hpv, cfg)
            if job_id is not None:                
                if self.controller.start(job_id):
                    
                    self.jobs[job_id] = {"cand_index" : cand_index, "status" : "run"}
                    
                    early_terminated = self.wait_until_done(job_id, cand_index, estimates, space)

                    result = self.controller.get_job(job_id)
                   
                    self.jobs[job_id]["result"] = result
                    self.jobs[job_id]["status"] = "done"
                    
                    acc_curve = result["lr"]
                    test_err = result['cur_loss']
                    best_epoch = len(acc_curve) + 1
                    if acc_curve != None and len(acc_curve) > 0:
                        max_i = np.argmax(acc_curve)
                        test_err = 1.0 - acc_curve[max_i]
                        best_epoch = max_i + 1
                        self.history.append({
                            "curve": acc_curve, 
                            "train_time": result['run_time'], 
                            "train_epoch": len(acc_curve)}
                            ) 
                                            
                    return {
                            "test_error": test_err,
                            "train_epoch": len(acc_curve),
                            "best_epoch" : best_epoch, 
                            "train_time" : result['run_time'], 
                            'early_terminated' : early_terminated
                    }  
                else:
                    error("Starting training job failed.")
            else:
                error("Creating job failed")
            
        else:
            error("Connection error: handshaking with trainer failed.")
        
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


class EarlyTerminateTrainer(RemoteTrainer):
    
    def __init__(self, controller, hpvs, **kwargs):
        self.early_terminated_history = []
        super(EarlyTerminateTrainer, self).__init__(controller, hpvs, **kwargs)

        self.history = []
        self.early_terminated_history = []
        self.etr_checked = False

    def reset(self):
        # reset history
        self.history = []
        self.early_terminated_history = []

    def train(self, cand_index, estimates=None, space=None):
        self.etr_checked = False
        early_terminated = False
        train_result = super(EarlyTerminateTrainer, self).train(cand_index, estimates, space)
        if 'early_terminated' in train_result:
            early_terminated = train_result['early_terminated']
        self.early_terminated_history.append(early_terminated)

        return train_result  