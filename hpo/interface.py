
import traceback
import threading
import atexit
import inspect

from flask import Flask
from flask_restful import Api

from hpo.resources.billboard import Billboard
from hpo.resources.config import Config
from hpo.resources.jobs import Jobs
from hpo.resources.job import Job
from hpo.resources.space import Space
from hpo.resources.candidates import Candidates
from hpo.resources.completes import Completes
from hpo.resources.grid import Grid
from hpo.resources.hparams import HyperparamVector
from hpo.resources.error import ObservedError 

from hpo.workers.seq_opt import *
from hpo.workers.job_mgr import JobManager

from hpo.utils.logger import set_log_level
import hpo.hp_config as hp_cfg


DEFAULT_DEBUG_MODE = True
WORKING_JOB_MGRS = []

def wait_seq_opt_request(run_cfg, hp_cfg,
                    hp_dir="hp_conf/", 
                    enable_debug=DEFAULT_DEBUG_MODE,
                    port=5000, 
                    enable_surrogate=False,
                    threaded=False):
    
    global WORKING_JOB_MGRS

    if enable_debug:
        set_log_level('debug')

    w = SequentialOptimizer(run_cfg, hp_cfg, "seq_opt_{}".format(port))
    jm = JobManager(w, use_surrogate=enable_surrogate)
    cred = jm.credential
    WORKING_JOB_MGRS.append(jm)
    

    app = Flask(__name__)
    api = Api(app)

    # For profile
    api.add_resource(Billboard, "/", # for node spec and resources
                    resource_class_kwargs={'job_manager': jm})
    api.add_resource(Config, "/config", # for run spec
                    resource_class_kwargs={'job_manager': jm, "hp_config": hp_cfg})
    
    # For job handling
    api.add_resource(Jobs, "/jobs", 
                    resource_class_kwargs={'job_manager': jm})
    api.add_resource(Job, "/jobs/<string:job_id>", 
                    resource_class_kwargs={'job_manager': jm})
    
    # For sampling space and history sharing
    api.add_resource(Space, "/space", 
                    resource_class_kwargs={'worker': w, 'credential': cred})
    api.add_resource(Completes, "/space/completes", 
                    resource_class_kwargs={'worker': w, 'credential': cred})
    api.add_resource(Candidates, "/space/candidates", 
                    resource_class_kwargs={'worker': w, 'credential': cred})                                         
    api.add_resource(Grid, "/space/grids/<string:id>", 
                    resource_class_kwargs={'worker': w, 'credential': cred})
    api.add_resource(HyperparamVector, "/space/vectors/<string:id>", 
                    resource_class_kwargs={'worker': w, 'credential': cred})
    api.add_resource(ObservedError, "/space/errors/<string:id>", 
                    resource_class_kwargs={'worker': w, 'credential': cred})


    app.run(host='0.0.0.0', port=port, debug=enable_debug, threaded=threaded)


@atexit.register
def exit():
    global WORKING_JOB_MGRS
    if len(WORKING_JOB_MGRS) > 0:
        print("cleanup processing...")
        for wjm in WORKING_JOB_MGRS:
            wjm.__del__()
