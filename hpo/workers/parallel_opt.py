import os
import time
from multiprocessing import Process, current_process

import hpo.hp_config as hp_cfg

from hpo.utils.logger import *
from hpo.connectors.hpo_remote import *

from hpo.interface import *


def create_local_daemon(run_config, port=5000, log_level="debug"):

    set_log_level(log_level)

    debug("HPO daemon will be working in port {}.\n".format(port))
    wait_seq_opt_request(run_config, 
        enable_debug=True, port=port)


def run_seq_hpo(connector, run_time, mode, spec, surrogate=None, log_level="debug"):

    set_log_level(log_level)

    ro = RemoteSequentialOptimizer(connector, surrogate=surrogate)

    desc = ro.create_job_description(mode=mode, spec=spec, exp_time=run_time)
    debug("Run HPO through http://{}:{}...\n".format(connector.ip_addr, connector.port))
    
    ro.optimize(desc)


class LocalParallelOptimizer(object):
    def __init__(self, run_config, 
            ip_addr="127.0.0.1", surrogate=None, base_port=5000):

        self.run_config = run_config
        self.ip_addr = ip_addr
        self.base_port = base_port
        self.connectors = []
        self.surrogate = surrogate

    def get_results(self):
        results = []
        for c in self.connectors:
            jobs = c.get_all_jobs()
            for j in jobs:
                if "result" in j:
                    results.append(j["result"])
                else:
                    debug("No result in job: {}".format(j)) 
        
        return results

    def get_ports(self):
        ports = []
        port = self.base_port
        for bf in self.run_config['bandits']:
            if "port" in bf:
                ports.append(bf["port"])
            else:
                ports.append(port)
                port += 1
        return ports

    def prepare(self):
        if not 'bandits' in self.run_config:
            print("No bandits setting in run configuration.")
            return 
    
    def fork_daemons(self):
        try:
            debug("Forking daemons for serving HPO...")
            daemons = []    

            for port in self.get_ports():                
                sp = Process(target=create_local_daemon, 
                    args=(self.run_config, port))
                daemons.append(sp)

            # run services
            for sp in daemons:
                sp.start()            
                time.sleep(5)
      

        except Exception as ex:
            print("Creating process failed: {}".format(ex))

    def run(self, run_time):
        if not 'bandits' in self.run_config:
            print("No bandits setting in run configuration.")
            return 
        bandit_configs = self.run_config['bandits']  

        try:
            debug("Running parallel HPO for {}".format(run_time))
            controllers = []    
            for cfg in bandit_configs:
                
                port = cfg["port"]
                mode = cfg["mode"]
                spec = cfg["spec"]

                rtc = RemoteOptimizerConnector(self.ip_addr, port)
                self.connectors.append(rtc)

                # create controller with multiprocessing
                cp = Process(target=run_seq_hpo, 
                    args=(rtc, run_time, mode, spec, self.surrogate))                
                controllers.append(cp)

            # run controllers
            for cp in controllers:
                cp.start()

            # wait until all controllers are done    
            for cp in controllers:
                cp.join()
        
        except Exception as ex:
            print("Running process failed: {}".format(ex))

