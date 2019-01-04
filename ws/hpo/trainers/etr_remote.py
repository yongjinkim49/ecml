from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import time
import sys
import copy

import numpy as np
import math

from ws.shared.logger import *
from ws.shared.proto import TrainerPrototype

class RemoteTrainer(TrainerPrototype):
    def __init__(self, connector, hpvs, 
                base_error=0.9, polling_interval=5, max_timeout= 100, min_train_epoch=1):

        self.hpvs = hpvs
        self.hp_config = connector.hp_config

        self.controller = connector
        self.base_error = base_error

        self.jobs = {}
        self.history = []

        self.min_train_epoch = min_train_epoch
        self.max_timeout = max_timeout
        self.polling_interval = polling_interval

        super(RemoteTrainer, self).__init__()
    
    def reset(self):
        self.jobs = {}
        self.history = []

    def stop_early(self, acc_curve, estimates):
        return False
        
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
                            if space != None:
                                space.update(model_index, interim_err)
                        
                        prev_interim_err = interim_err
                        time_out_count = 0 # XXX:reset time out count
                        
                        # Early termination check
                        if self.min_train_epoch < len(acc_curve) and \
                            self.check_termination_condition(acc_curve, estimates):                        
                            job_id = j['job_id']
                            debug("This job will be terminated early as expected")
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

    def train(self, cand_index, estimates=None, space=None):
        hpv = {}
        cfg = {'cand_index' : cand_index}
        param_names = self.hp_config.get_hyperparams()
        param_values = self.hpvs[cand_index]
        debug("Training HPV: {}".format(param_values))
        
        if type(param_values) == dict:
            for param in param_names:
                value = param_values[param]
                hpv[param] = value
        elif type(param_values) == list and len(param_names) == len(param_values):
            for i in range(len(param_names)):
                param = param_names[i]
                value = param_values[i]
                hpv[param] = value
        else:
            raise TypeError("Invalid hyperparams: {}/{}".format(param_names, param_values))

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


class EarlyTerminateTrainer(RemoteTrainer):
    
    def __init__(self, controller, hpvs):
        self.early_terminated = []
        super(EarlyTerminateTrainer, self).__init__(controller, hpvs)

        self.history = []
        self.early_terminated = []

    def reset(self):
        # reset history
        self.history = []
        self.early_terminated = []

