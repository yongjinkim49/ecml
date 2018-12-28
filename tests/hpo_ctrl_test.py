import os
import sys
import time

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from commons.logger import *

import commons.hp_cfg as hp_cfg
from hpo.connectors.hpo_remote import *

def test_hpo_main():
    worker_url = None
    ip_addr = "127.0.0.1" #"147.47.123.249"
    surrogate = None #"data10"            
    # XXX: If you want to uncomment below, you firstly start add_task.py of worker with port 6000.
    worker_url = "http://147.47.120.182:6001"

    set_log_level('debug')

    rtc = RemoteOptimizerConnector(ip_addr, 5000, "jo2fulwkq")
    ro = RemoteSequentialOptimizer(rtc, surrogate="data10", worker_url=worker_url, polling_interval=10)
    
    opts = ro.create_job_description(exp_time='12h', spec="SEQ", num_trials=100)
    ro.optimize(opts)
    for j in ro.jobs:
        print("Result of job {}:\n{}".format(j['id'], j['result']))

if __name__ == '__main__':    
    test_hpo_main()
