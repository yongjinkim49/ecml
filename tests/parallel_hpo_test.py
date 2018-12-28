import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from multiprocessing import Process, current_process
from commons.logger import *

from hpo.connectors.multi_ctrl import LocalParallelOptimizerController
import hpo.bandit_config as bconf
import commons.hp_cfg as hconf

if __name__ == '__main__':    
    set_log_level('debug')

    run_cfg = bconf.read('parallel-test.json') 
    hp_cfg = hconf.read_config('./hp_conf/data2.json')     
    r = LocalParallelOptimizerController(run_cfg, surrogate="data2")    
    
    # FIXME: forking daemons makes some issues.
    r.fork_daemons() 
    
    r.run("1h")
    log("Final results: {}".format(r.get_results()))     

