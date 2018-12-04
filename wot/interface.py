
import traceback
import threading
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

DEFAULT_DEBUG_MODE = False

job_manager = None


def wait_job_request(eval_job,  
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=5000, 
                    enable_surrogate=False):
    
    global job_manager

    if debug_mode:
        set_log_level('debug')

    ej = eval_job()
    job_manager = JobManager(ej, use_surrogate=enable_surrogate)

    app = Flask(__name__)
    api = Api(app)

    api.add_resource(Billboard, "/", 
                    resource_class_kwargs={'job_manager': job_manager})
    api.add_resource(Config, "/config", 
                    resource_class_kwargs={'job_manager': job_manager})
    api.add_resource(Jobs, "/jobs", 
                    resource_class_kwargs={'job_manager': job_manager})
    api.add_resource(Job, "/jobs/<string:job_id>", 
                    resource_class_kwargs={'job_manager': job_manager})

    app.run(host='0.0.0.0', port=port, debug=debug_mode)


def eval_task(eval_func):
    def wrapper_function():
        
        argspec = inspect.getargspec(eval_func)
        fe = FunctionEvaluator(eval_func.__name__)
        fe.set_exec_func(eval_func, argspec.args)
        return fe
        
    return wrapper_function


def update_working_result(cur_epoch, cur_loss, run_time):
    if job_manager != None:
        job_manager.update_epoch_result(cur_epoch, cur_loss, run_time)
    else:
        warn("Job manager is not ready to serve.")


def stop_working_job():
    if job_manager != None:
        job_manager.stop_working_job()
    else:
        warn("Job manager is not ready to serve.")    


@atexit.register
def exit():
    global job_manager
    if job_manager:
        print("cleanup processing...")
        job_manager.__del__()
