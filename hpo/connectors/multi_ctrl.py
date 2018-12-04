import json
import time
import sys

import numpy as np
import math

from hpo.utils.logger import *


class DiversifiedHPOManager(object):
    def __init__(self):
        return super(DiversifiedHPOManager, self).__init__()

    def request_job(self, worker_id, job_desc):
        # TODO:send the job to a worker
        pass

        
class ParallelHPOManager(object):
    def __init__(self):
        self.tasks = {}

    def register(self, controller, cfg):
        task_desc = {"controller" : controller, "cfg": cfg}
        # TODO: make task id from worker id and url
        task_id = ""
        self.tasks[task_id] = task_desc