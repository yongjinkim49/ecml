import os
import sys
import threading
import time
import traceback

import numpy as np

from ws.shared.logger import *
import ws.shared.lookup as lookup

from ws.wot.workers.evaluator import IterativeFunctionEvaluator

class SurrogateEvaluator(IterativeFunctionEvaluator):
    def __init__(self, name, lookup, **kwargs):
        self.lookup = lookup
        id = "surrogate_{}-".format(name)        
        super(SurrogateEvaluator, self).__init__(id)

        self.type = 'surrogate'

        self.cur_model_index = None
        self.time_slip_rate = None

        if 'time_slip_rate' in kwargs:
            self.time_slip_rate = kwargs['time_slip_rate']
        
        init_loss = 0.9
        if 'init_loss' in kwargs:
            init_loss = kwargs['init_loss']
        else:
            if name == 'data30':
                init_loss = 0.99
            elif name == 'data10':
                init_loss = 1.0             
            
        self.init_results(init_loss)

    def init_results(self, init_loss):
        # TODO: do something for initial condition setting
        result = {"run_time": 0.0, "cur_loss": init_loss, "cur_iter": 0, "iter_unit": "epoch"}

        self.results.append(result)

    def set_job_description(self, hpv, index=None, job_id=None):
        if job_id != None:
            self.job_id = job_id

        # skip hpv matching with index value
        if index is not None:
            debug("Parameter lookup using given index: {}".format(index))
            self.params = hpv
            self.cur_model_index = index
            
            return True
        else:
            model_index = self.find(hpv)
            if model_index < 0:
                error("invalid hyperparameter setting: {}".format(hpv))
                return False
            else:
                self.cur_model_index = model_index
            self.params = hpv
            return True

    def execute(self):
        if self.cur_model_index is None:
            raise ValueError('hyperparameters are not initialized')

        try:            
            total_epoches = self.lookup.num_epochs
            if self.max_iters is not None:
                if self.iter_unit == "epoch" and self.max_iters < total_epoches:
                    total_epoches = self.max_iters
                else:
                    raise ValueError("Invalid max iteration setting: {}{}".format(self.max_iters, self.iter_unit))
            durations = self.lookup.get_elapsed_times()
            total_samples = len(durations)
            if self.cur_model_index > total_samples:
                raise ValueError("Invalid surrogate vector index")
            duration = durations[self.cur_model_index]
            dur_per_epoch = float(duration / total_epoches)

            for ep in range(total_epoches):
                with self.pause_cond:
                    while self.paused:
                        self.pause_cond.wait()
                    num_epoch = ep + 1
                    cur_dur = dur_per_epoch * num_epoch
                    lcs = self.lookup.get_accuracies_per_epoch(num_epoch)
                    lc = lcs.values.tolist()[self.cur_model_index]
                    #debug("learning curve of index {}: {}".format(self.cur_model_index, lc))
                    cur_loss = 1.0 - lc[-1]
                    if self.time_slip_rate:
                        time.sleep(dur_per_epoch / self.time_slip_rate)
                    if self.stop_flag:
                        break
                    debug("training {} complete with loss {:.4f} at {} epoches".format(self.id, cur_loss, num_epoch)) # for debugging
                    result = {
                        "run_time": cur_dur, 
                        "cur_loss": cur_loss, 
                        "cur_iter": num_epoch,
                        "iter_unit" : "epoch"
                    }
                    
                    self.results.append(result)
                    

        except Exception as ex:
            warn("Exception occurs: {}".format(sys.exc_info()[0]))
        finally:
            with self.thread_cond:
                self.busy = False
                self.cur_model_index = None
                self.thread_cond.notify()

    def find(self, hpv):
        ''' find appropriate index of surrogate function in lookup, if not found, return -1 '''
        model_idx = 0
        hpvs = self.lookup.get_hyperparam_vectors()
        tv = self.vectorize(hpv)
        for v in hpvs:
            if np.array_equal(v.tolist(), tv.tolist()):
                return model_idx
            else:
                model_idx += 1

        return -1

    def vectorize(self, hpv):
        cfg = self.lookup.config
        l = []
        for k in cfg.param_order:
            l.append(hpv[k])

        return np.asarray(l)
    
