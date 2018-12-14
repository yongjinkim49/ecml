import traceback

import atexit
import inspect

from flask import Flask
from flask_restful import Api

from wot.resources.billboard import Billboard
from wot.resources.config import Config
from wot.resources.jobs import Jobs
from wot.resources.job import Job 

from wot.workers.job_mgr import JobManager
from wot.workers.evaluator import *

from wot.utils.logger import *
import multiprocessing as mp

DEFAULT_DEBUG_MODE = False
JOB_MANAGER = None
API_SERVER_PROCESS = None

# Job handling APIs
def wait_job_request(eval_worker, hp_cfg,
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=5000,
                    device_type="cpu",
                    device_id=0,
                    retrieve_func=None, 
                    enable_surrogate=False
                    ):
    
    global JOB_MANAGER
    global API_SERVER_PROCESS

    if debug_mode:
        set_log_level('debug')

    ej = eval_worker()
    ej.set_device_id(device_type, device_id)
    if JOB_MANAGER == None:
        JOB_MANAGER = JobManager(ej, 
                                use_surrogate=enable_surrogate, 
                                retrieve_func=retrieve_func)
    else:
        warn("Job manager already initialized.")
        return

    app = Flask(__name__)
    api = Api(app)

    api.add_resource(Billboard, "/", 
                    resource_class_kwargs={'job_manager': JOB_MANAGER})
    api.add_resource(Config, "/config", 
                    resource_class_kwargs={'job_manager': JOB_MANAGER, "hp_config": hp_cfg})
    api.add_resource(Jobs, "/jobs", 
                    resource_class_kwargs={'job_manager': JOB_MANAGER})
    api.add_resource(Job, "/jobs/<string:job_id>", 
                    resource_class_kwargs={'job_manager': JOB_MANAGER})
    kwargs = { 
                'host': '0.0.0.0', 
                'port':port, 
                'debug' :debug_mode
            }
            
    API_SERVER_PROCESS = mp.Process(target=app.run, kwargs=kwargs)
    API_SERVER_PROCESS.start()
    API_SERVER_PROCESS.join()


def stop_job_working():
    global JOB_MANAGER

    if JOB_MANAGER != None:
        JOB_MANAGER.stop_working_job()
    else:
        warn("Job manager is not ready to serve.")    


def update_result_per_epoch(cur_epoch, cur_loss, run_time):
    global JOB_MANAGER

    if JOB_MANAGER != None:
        JOB_MANAGER.update_result(cur_epoch, "epoch", cur_loss, run_time)
    else:
        warn("Job manager is not ready to serve.")


def update_result_per_steps(cur_steps, cur_loss, run_time):
    global JOB_MANAGER

    if JOB_MANAGER != None:
        JOB_MANAGER.update_result(cur_steps, "step", cur_loss, run_time)
    else:
        warn("Job manager is not ready to serve.")


# Decorator functions 
# (Do NOT invoke it directly)
def eval_task(eval_func):
    def wrapper_function():        
        argspec = inspect.getargspec(eval_func)
        fe = IterativeFunctionEvaluator("{}_evaluator".format(eval_func.__name__))
        fe.set_exec_func(eval_func, argspec.args)
        return fe
        
    return wrapper_function


def progressive_eval_task(eval_func):
    def wrapper_function():        
        argspec = inspect.getargspec(eval_func)
        fe = IterativeFunctionEvaluator("{}_evaluator".format(eval_func.__name__), progressive=True)
        fe.set_exec_func(eval_func, argspec.args)
        return fe
        
    return wrapper_function


@atexit.register
def exit():
    global JOB_MANAGER
    global API_SERVER_PROCESS

    if API_SERVER_PROCESS != None:
        
        API_SERVER_PROCESS.terminate()
        API_SERVER_PROCESS.join()
        debug("API server terminated properly.")
        JOB_MANAGER.__del__()
        API_SERVER_PROCESS = None            
        JOB_MANAGER = None

    
