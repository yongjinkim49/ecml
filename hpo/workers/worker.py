import os
import threading
import time
import traceback
import copy

import numpy as np

from commons.logger import *

class Worker(object):
    def __init__(self):
        self.thread = None
        
        self.busy = False
        self.stop_flag = False
        self.thread_cond = threading.Condition(threading.Lock())
        self.paused = False
        self.pause_cond = threading.Condition(threading.Lock())
        self.timer = None
        self.timeout = None
        self.type = 'prototype'
        self.config = {}
        self.id = 'worker_proto'
                
        self.reset()

    def reset(self):
        self.results = []
 
    def set_params(self, params, index=None):
        if params:
            self.params = params
            
            return True
        else:
            debug("invalid params: {}".format(params))
            return False

    def get_cur_result(self):
        if len(self.results) > 0:
            latest = self.results[-1]
            result = copy.copy(latest)
            
            return result

        else:
            return None

    def get_cur_status(self):
        if self.busy:
            if self.paused:
                return 'pending'
            else:
                return 'processing'
        else:
            if self.paused:
                return 'error'
            else:
                return 'idle'

    def start(self):
        with self.thread_cond:
            while self.busy:
                self.thread_cond.wait()
            self.busy = True

        if not self.timeout is None and not self.timer is None:
            self.timer.cancel()
        
        self.stop_flag = False
        self.id += str(threading.current_thread().ident)
        self.thread = threading.Thread(
            target=self.execute, name='worker {} thread'.format(self.id))
        self.thread.daemon = True
        self.thread.start()

        if not self.timeout is None:
            self.timer = threading.Timer(self.timeout, self.stop)
            self.timer.daemon = True
            self.timer.start()

    def pause(self):
        self.paused = True
        self.pause_cond.acquire()
        #debug("Pause requested.")

    def resume(self):
        self.paused = False
        self.pause_cond.notify()
        self.pause_cond.release()
        #debug("Resume requested.")

    def stop(self):
        if not self.thread is None:
            #debug("Stop requested.")
            self.stop_flag = True
            self.thread.join()

    def execute(self):
        ''' Execute target function and append an intermidiate result per epoch to self.results.
        The result is a dictionary object which has following attributes: 
          - "run_time" : float, run time (elapsed time for the given epoch) 
          - "cur_loss": float, current loss value
          - "cur_epoch": integer, number of current epochs
        '''
        raise NotImplementedError('execute() should be overrided.')

