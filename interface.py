import multiprocessing as mp
import traceback
import atexit
import inspect

from commons.logger import *
from commons.ws_mgr import WebServiceManager

from wot.job_mgr import TrainingJobManager
from hpo.job_mgr import HPOJobManager
from hpo.node_mgr import ParallelHPOManager

DEFAULT_DEBUG_MODE = False
JOB_MANAGER = None
API_SERVER = None


####################################################################
# Job request awaiting APIs
def create_name_server(hp_cfg,
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=5000,
                    threaded=False):
    global JOB_MANAGER
    global API_SERVER
    JOB_MANAGER = ParallelHPOManager(hp_cfg)
    API_SERVER = WebServiceManager(JOB_MANAGER, hp_cfg)
    API_SERVER.run_service(port, debug_mode, threaded)    

def wait_hpo_request(run_cfg, hp_cfg,
                    hp_dir="hp_conf/", 
                    enable_debug=DEFAULT_DEBUG_MODE,
                    port=5001, 
                    enable_surrogate=False,
                    threaded=False):
    
    global JOB_MANAGER
    global API_SERVER

    JOB_MANAGER = HPOJobManager(run_cfg, hp_cfg, port, use_surrogate=enable_surrogate)
    
    API_SERVER = WebServiceManager(JOB_MANAGER, hp_cfg)
    API_SERVER.run_service(port, debug_mode, threaded)


def wait_train_request(eval_job, hp_cfg,
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=6000,
                    device_type="cpu",
                    device_id=0,
                    retrieve_func=None, 
                    enable_surrogate=False,
                    processed=True
                    ):
    
    global JOB_MANAGER
    global API_SERVER

    ej = eval_job()
    ej.set_device_id(device_type, device_id)
    if JOB_MANAGER == None:
        JOB_MANAGER = TrainingJobManager(ej, 
                                use_surrogate=enable_surrogate, 
                                retrieve_func=retrieve_func)
    else:
        warn("Job manager already initialized.")
        return
    API_SERVER = WebServiceManager(JOB_MANAGER, hp_cfg)
    API_SERVER.run_service(port, debug_mode, with_process=processed)


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


#########################################################################
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
    global API_SERVER
    if JOB_MANAGER != None:
        JOB_MANAGER.__del__()
        JOB_MANAGER = None

    if API_SERVER != None:
        
        API_SERVER.stop_service()
        debug("API server terminated properly.")
        
        API_SERVER = None            
