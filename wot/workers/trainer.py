import os
import threading
import time
import traceback
import copy

from commons.logger import *
from wot.workers.worker import Worker

class Trainer(Worker):

    def __init__(self, name=None):
        self.config = {}
        self.reset()
        if name == None:
            name = 'trainer_proto'

        return super(Trainer, self).__init__(name)

    def reset(self):
        self.results = []
        #self.params = None

    def update_result(self, retrieve_func):
        result = retrieve_func()
        # TODO: validate result contents
        if type(result) == list:
            if len(result) > 0:            
                self.results = result
            else:
                debug("No result found yet.")
        elif type(result) == dict:
            self.results.append(result)
        else:
            warn("Invalid result: {}".format(result))

    def set_job_description(self, params, index=None, job_id=None):
        if job_id != None:
            self.job_id = job_id

        if params:
            debug("Assigned parameters: {}".format(params))
            self.params = params
            return True
        else:
            debug("Invalid params: {}".format(params))
            return False

    def get_cur_result(self):
        if len(self.results) > 0:
            latest = self.results[-1]
            result = copy.copy(latest)
            
            return result

        else:
            return None

    def add_result(self, cur_iter, cur_loss, run_time, iter_unit="epoch"):
        result = {"cur_iter": cur_iter, "iter_unit": iter_unit,
            "cur_loss": cur_loss, "run_time": run_time}
        
        self.results.append(result)

    def execute(self):
        ''' Execute target function and append an intermidiate result per epoch to self.results.
        The result is a dictionary object which has following attributes: 
          - "run_time" : float, run time (elapsed time for the given epoch) 
          - "cur_loss": float, current loss value
          - "cur_iter": integer, number of current iterations
          - "iter_unit" : string, epoch or steps will be accepted
        '''
        raise NotImplementedError('execute() should be overrided.')