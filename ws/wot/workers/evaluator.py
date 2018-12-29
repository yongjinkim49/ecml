import os
import sys
import time
import traceback
import copy

import numpy as np

from ws.shared.logger import *
from ws.wot.workers.trainer import Trainer


class IterativeFunctionEvaluator(Trainer):
    def __init__(self, name, progressive=False):
        
        super(IterativeFunctionEvaluator, self).__init__(name)

        self.type = 'eval_func'
        self.eval_func = None
        
        self.device_id = 'cpu0'
        self.max_iters = 1
        self.iter_unit = "epoch"
        self.progressive = progressive
        self.config = {}

    def get_config(self):
        return self.config

    def set_max_iters(self, num_max_iters, iter_unit="epoch"):
        self.max_iters = num_max_iters

    def set_exec_func(self, eval_func, args):
        self.eval_func = eval_func
        self.config = {"target_func": eval_func.__name__,
                        "arguments" : args}

    def set_device_id(self, device_type, device_index):
        self.device_id = "{}{}".format(device_type, device_index)

    def get_device_id(self):
        return self.device_id

    def get_cur_result(self):
        if len(self.results) > 0:
            latest = self.results[-1]
            result = copy.copy(latest)

            result['losses'] = [copy.copy(r['cur_loss']) for r in self.results]
            result['times'] = [copy.copy(r['run_time']) for r in self.results]
            
            result['cur_loss'] = min(result['losses'])
            result['run_time'] = sum(result['times'])
            return result

        else:
            return None

    def start(self):
        if self.params is None:
            error('Set configuration properly before starting.')
            return
        else:
            super(IterativeFunctionEvaluator, self).start()

    def execute(self):
        try:
            self.reset() # XXX:self.results should be empty here
            debug("Max iterations: {}{}".format(self.max_iters, self.iter_unit))
            
            base_time = time.time()
            num_iters = 1
            max_iters = self.max_iters
            
            if self.progressive == True:
                num_iters = self.max_iters                

            for i in range(num_iters):
                
                with self.pause_cond:
                    while self.paused:
                        self.pause_cond.wait()
                debug("Assigned params: {}".format(self.params))

                cur_loss = None
                cur_iter = i + 1
                cur_dur = time.time() - base_time
                
                # check stop request before long time evaluation
                if self.stop_flag == True:
                    break

                if self.progressive == True:
                    max_iters = i + 1

                result = self.eval_func(self.params, 
                    cur_iter=i, max_iters=max_iters, iter_unit=self.iter_unit,
                    job_id=self.job_id)
                                
                if result == None:
                    # if objective function does not return any result,
                    # wait until terminated by calling stop()
                    debug("Waiting stop signal")
                    while self.stop_flag == False:
                        time.sleep(1)

                elif type(result) == dict and "cur_loss" in result:
                    cur_loss = result["cur_loss"]                    
                    if "run_time" in result and result["run_time"] > 0:                        
                        cur_dur = result["run_time"]
                    
                    if "cur_iter" in result:
                        cur_iter = result["cur_iter"]
                    
                    if "iter_unit" in result:
                        iter_unit = result["iter_unit"]
                elif type(result) == float:
                    cur_loss = result
                    cur_iter = i + 1
                    cur_dur = time.time() - base_time
                else:
                    warn("Invalid result format: {}".format(result))

                if cur_loss != None:                    
                    result = {"run_time": cur_dur,
                            "cur_loss": cur_loss, 
                            "cur_iter": cur_iter,
                            "iter_unit": self.iter_unit}
                    self.results.append(result)
                
                elif type(result) == list and len(result) > 0:
                    self.results = result # update all results
                

        except Exception as ex:
            warn("Exception occurs: {}".format(sys.exc_info()[0]))

        finally:
            with self.thread_cond:
                self.busy = False
                self.params = None
                self.thread_cond.notify()
                debug("Evaluation {} finished properly.".format(self.job_id))

