import os
import threading
import time
import traceback
import copy

import numpy as np

from wot.utils.logger import *
from wot.workers.worker import Worker


class FunctionEvaluator(Worker):
    def __init__(self, name):
        super(FunctionEvaluator, self).__init__()

        self.type = 'obj_func'
        self.eval_func = None
        
        self.id = "obj_func-{}".format(name)
        self.device_id = 'cpu0'
        self.max_iters = 1

    def set_max_iters(self, max_epoch):
        self.max_iters = max_epoch

    def set_exec_func(self, eval_func, args):
        self.eval_func = eval_func
        self.config = {"obj_func": eval_func.__name__,
                        "param_order" : args}

    def get_cur_result(self):
        if len(self.results) > 0:
            latest = self.results[-1]
            result = copy.copy(latest)

            result['losses'] = [copy.copy(r['cur_loss']) for r in self.results]
            result['times'] = [copy.copy(r['run_time']) for r in self.results]
            
            return result

        else:
            return None

    def start(self):
        if self.params is None:
            error('Set configuration properly before starting.')
            return
        else:
            super(FunctionEvaluator, self).start()

    def execute(self):
        try:
            self.reset() # XXX:self.results should be empty here
            debug("max iteraions: {}".format(self.max_iters))
            
            base_time = time.time()
            for i in range(self.max_iters):
                
                with self.pause_cond:
                    while self.paused:
                        self.pause_cond.wait()
                debug("params: {}".format(self.params))
                
                cur_loss = self.eval_func(**self.params)
                if cur_loss != None:
                    cur_epoch = i + 1
                    
                    cur_dur = time.time() - base_time
                        
                    result = {"run_time": cur_dur,
                            "cur_loss": cur_loss, 
                            "cur_epoch": cur_epoch}
                    
                    self.results.append(result)
                else:
                    # wait until terminated
                    while self.stop_flag == False:
                        time.sleep(1)

        except Exception as ex:
            warn("exception occurs: {}".format(traceback.format_exc()))
            self.paused = True

        finally:
            with self.thread_cond:
                self.busy = False
                self.params = None
                self.thread_cond.notify()