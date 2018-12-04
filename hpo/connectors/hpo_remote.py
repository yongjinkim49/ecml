import json
import time
import sys

import numpy as np
import math

from hpo.utils.logger import *

from hpo.connectors.remote_ctrl import RemoteJobConnector


class RemoteOptimizerConnector(RemoteJobConnector):
    
    def __init__(self, ip_addr="127.0.0.1", port=5000, **kwargs):
        url = "http://{}:{}".format(ip_addr, port)
        self.ip_addr = ip_addr
        self.port = port
        super(RemoteOptimizerConnector, self).__init__(url, **kwargs)

    def validate(self):
        try:
            profile = self.get_profile()
            if profile and "spec" in profile and "job_type" in profile["spec"]:
                if profile["spec"]["job_type"] == "HPO runner":
                    config = self.get_config()
                    if config and "arms" in config and len(config["arms"]) > 0:
                        # TODO: parameter validation process                  
                        return True       

        except Exception as ex:
            warn("Validation failed: {}".format(ex))
            
        return False


class RemoteSequentialOptimizer(object):
    def __init__(self, connector, 
                hp_config=None, surrogate=None, polling_interval=1, worker_url=None):

        self.hp_config = hp_config
        self.connector = connector
        self.surrogate = surrogate
        self.worker_url = worker_url

        self.jobs = []
        self.polling_interval = polling_interval
        self.in_progress = False

    def create_job_description(self, mode="DIV", spec="RANDOM", 
                    exp_crt="TIME", exp_time="24h", exp_goal=0.9999, num_trials=1):
        job_desc = {}
        job_desc['exp_crt'] = exp_crt
        job_desc['exp_time'] = exp_time
        job_desc['exp_goal'] = exp_goal
        job_desc['num_trials'] = num_trials
        job_desc['mode'] = mode
        job_desc['spec'] = spec

        if self.worker_url:
            job_desc['worker_url'] = self.worker_url

        if self.surrogate:
            job_desc['surrogate'] = self.surrogate
        elif self.hp_config:
            job_desc['hp_cfg'] = self.hp_config
        else:
            raise ValueError("Invalid setting: surrogate or hp_config must be set properly.")
        
        return job_desc

    def wait_until_done(self, method='polling'):
        if method == 'polling':
            try:
                while True: # XXX: infinite loop
                    self.in_progress = True
                    j = self.connector.get_job("active")
                    if j != None:
                        if "result" in j:
                            #debug("{}".format(j['result']))
                            pass
                        else:
                            raise ValueError("Invalid job description: {}".format(j))
                    elif j == None:
                        break 
                    time.sleep(self.polling_interval)

            except Exception as ex:
                warn("Something goes wrong in remote worker: {}".format(ex))
            finally:
                self.in_progress = False
                
        else:
            raise NotImplementedError("No such waiting method implemented")

    def optimize(self, options):
        
        if self.connector.validate():
            #debug("RemoteSequentialOptimizer tries to create a HPO job")
            job_id = self.connector.create_job(options)
            if job_id is not None:                
                if self.connector.start(job_id):
                                        
                    self.jobs.append({"id": job_id, "options" : options, "status" : "run"}) 
                    
                    self.wait_until_done()

                    result = self.get_current_result(job_id)
                    for job in self.jobs:
                        if job['id'] == job_id:
                            job["result"] = result
                            job["status"] = "done"
                    
                    return result

                else:
                    error("Starting HPO job failed.")
            else:
                error("Creating job failed")        
    
    def get_results(self):
        results = []
        try:
            debug("trying to getting all results from {}".format(self.jobs))
            for job in self.jobs:
                if job["status"] == "done":
                    results.append({ "job_id": job["id"], "result": job["result"]})

        except Exception as ex:
            error("getting the results failed")
        return results
    
    def get_current_result(self, job_id):
        try:
            j = self.connector.get_job(job_id)
            if "result" in j:
                return j["result"]
            else:
                return None
        except Exception as ex:
            warn("Something goes wrong in remote worker: {}".format(ex))
            return None
