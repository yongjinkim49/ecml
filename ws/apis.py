import traceback
import atexit
import inspect

import validators as valid

from ws.shared.logger import *
from ws.ws_mgr import WebServiceManager
from ws.shared.register import NameServerConnector


DEFAULT_DEBUG_MODE = False
JOB_MANAGER = None
API_SERVER = None


####################################################################
# Job request awaiting APIs
def create_name_server(hp_cfg,
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=5000,
                    threaded=False):
    
    from ws.hpo.node_mgr import ParallelHPOManager
    
    global JOB_MANAGER
    global API_SERVER
    JOB_MANAGER = ParallelHPOManager(hp_cfg)
    API_SERVER = WebServiceManager(JOB_MANAGER, hp_cfg)
    API_SERVER.run_service(port, debug_mode, threaded)    


def wait_hpo_request(run_cfg, hp_cfg,
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=5001, 
                    enable_surrogate=False,
                    register_url=None,
                    threaded=False):
    
    from ws.hpo.job_mgr import HPOJobManager

    global JOB_MANAGER
    global API_SERVER

    if JOB_MANAGER == None:
        JOB_MANAGER = HPOJobManager(run_cfg, hp_cfg, port, use_surrogate=enable_surrogate)
        if register_url != None and valid.url(register_url):
            try:
                ns = NameServerConnector(register_url, JOB_MANAGER.get_credential())
                ns.register(port, "HPO_runner")
            except Exception as ex:
                warn("Registering myself to name server failed: {}".format(ex))

        API_SERVER = WebServiceManager(JOB_MANAGER, hp_cfg)
        API_SERVER.run_service(port, debug_mode, threaded)
    else:
        warn("Job manager already initialized.")
        return


def wait_train_request(eval_job, hp_cfg,
                    debug_mode=DEFAULT_DEBUG_MODE,
                    port=6000,
                    device_type="cpu",
                    device_index=0,
                    retrieve_func=None, 
                    enable_surrogate=False,
                    register_url=None,
                    processed=True
                    ):
    
    from ws.wot.job_mgr import TrainingJobManager

    global JOB_MANAGER
    global API_SERVER

    if JOB_MANAGER == None:
        ej = eval_job()
        ej.set_device_id(device_type, device_index)        
        JOB_MANAGER = TrainingJobManager(ej, 
                                        use_surrogate=enable_surrogate, 
                                        retrieve_func=retrieve_func)
        if register_url != None and valid.url(register_url):
            try:
                ns = NameServerConnector(register_url, JOB_MANAGER.get_credential())
                ns.register(port, "ML_trainer")
            except Exception as ex:
                warn("Registering myself to name server failed: {}".format(ex))

        API_SERVER = WebServiceManager(JOB_MANAGER, hp_cfg)
        API_SERVER.run_service(port, debug_mode, with_process=processed)
    else:
        warn("Job manager already initialized.")
        return


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
        from ws.wot.workers.evaluator import IterativeFunctionEvaluator

        argspec = inspect.getargspec(eval_func)
        fe = IterativeFunctionEvaluator("{}_evaluator".format(eval_func.__name__))
        fe.set_exec_func(eval_func, argspec.args)
        return fe
        
    return wrapper_function


def progressive_eval_task(eval_func):
    def wrapper_function():
        from ws.wot.workers.evaluator import IterativeFunctionEvaluator

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
