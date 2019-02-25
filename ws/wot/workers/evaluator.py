import os
import signal
import sys
import time
import traceback
import copy

import multiprocessing as mp
import numpy as np

from ws.shared.logger import *
from ws.wot.workers.trainer import Trainer


class IterativeFunctionEvaluator(Trainer):
    def __init__(self, name, progressive=False, forked=True):
        
        super(IterativeFunctionEvaluator, self).__init__(name, fork=forked)

        self.type = 'eval_func'
        self.eval_func = None
        
        self.max_iters = 1
        self.iter_unit = "epoch"
        self.progressive = progressive
        self.config = {}
        self.eval_process = None

    def get_config(self):
        return self.config

    def set_max_iters(self, num_max_iters, iter_unit="epoch"):
        self.max_iters = num_max_iters

    def set_exec_func(self, eval_func, args):
        self.eval_func = eval_func
        self.config = {"target_func": eval_func.__name__,
                        "arguments" : args}

    def start(self):
        if self.params is None:
            error('Set configuration properly before starting.')
            return False
        else:
            super(IterativeFunctionEvaluator, self).start()
            return True

    def stop(self):
        if self.eval_process != None:
            try:
                while self.eval_process.is_alive():
                    os.kill(self.eval_process._popen.pid, signal.SIGKILL)
                    time.sleep(1)
            except Exception as ex:
                pass
            self.eval_process = None
            self.stop_flag = True
        else:            
            super(IterativeFunctionEvaluator, self).stop()
            while self.stop_flag == False:
                time.sleep(1)
    def execute(self):
        try:
            self.reset() # XXX:self.results should be empty here
            debug("Max iterations: {}{}".format(self.max_iters, self.iter_unit))
            
            max_iters = self.max_iters
            num_iters = 1
            
            if self.progressive == True:
                num_iters = max_iters                

            for i in range(num_iters):
                base_time = time.time()
                with self.pause_cond:
                    while self.paused:
                        self.pause_cond.wait()
                debug("Assigned params: {}".format(self.params))

                
                # check stop request before long time evaluation
                if self.stop_flag == True:
                    break

                if self.progressive == True:
                    max_iters = i + 1

                                
                result = None   
                    # if objective function does not return any result,
                    # wait until terminated by calling stop()

                if self.is_forked() == True:
                    self.eval_process = mp.Process(target=self.eval_func, 
                        args=(self.params,), kwargs={"max_epoch": max_iters})
                    
                    self.eval_process.start()
                    
                    self.eval_process.join()
                    self.stop_flag = True

                    result = self.get_cur_result(self.get_device_id())
                else:
                    result = self.eval_func(self.params, 
                        cur_iter=i, max_iters=max_iters, iter_unit=self.iter_unit,
                        job_id=self.job_id)
                    if result == None:
                        # if objective function does not return any result,
                        # wait until terminated by calling stop()
                        debug("Waiting stop signal")
                        while self.stop_flag == False:
                            time.sleep(1)
                
                self.update_result(result, i+1, base_time)
                

        except Exception as ex:
            warn("Exception occurs: {}".format(sys.exc_info()[0]))

        finally:
            with self.thread_cond:
                self.busy = False
                self.params = None
                self.thread_cond.notify()
                debug("Evaluation {} finished properly.".format(self.job_id))

    def update_result(self, result, cur_iter, base_time):
        if type(result) == dict and "cur_loss" in result:
            cur_loss = result["cur_loss"]
            cur_acc = None
            cur_dur = None                    
            if "run_time" in result and result["run_time"] > 0:                        
                cur_dur = result["run_time"]
            else:
                cur_dur = time.time() - base_time
            if "cur_acc" in result:
                cur_acc = result['cur_acc']
            else:
                cur_acc = 1.0 - cur_loss
				
            if "cur_iter" in result:
                cur_iter = result["cur_iter"]

            if "iter_unit" in result:
                iter_unit = result["iter_unit"]

            result = { 
                "run_time": cur_dur,
                "cur_loss": cur_loss,
                "cur_acc" : cur_acc, 
                "cur_iter": cur_iter,
                "iter_unit": self.iter_unit 
            }
            self.results.append(result)
        elif type(result) == list and len(result) > 0:
            self.results = result # update all results            
        elif type(result) == float:
            result = { 
                "run_time": time.time() - base_time,
                "cur_loss": result,
                "cur_acc" : 1.0 - cur_loss, 
                "cur_iter": cur_iter,
                "iter_unit": self.iter_unit 
            }
            self.results.append(result)
        else:
            warn("Invalid result format: {}".format(result))
            raise ValueError("Invalid result")        