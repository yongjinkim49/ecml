import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from multiprocessing import Process, current_process

from hpo.workers.parallel_opt import *
from hpo.utils.logger import *
import hpo.bandit_config as run_config

if __name__ == '__main__':    
    set_log_level('debug')

    run_cfg = run_config.read('data201_tv4.json')    
    r = LocalParallelOptimizer(run_cfg)    
    #r.fork_daemons() # FIXME: forking daemons makes some issues.
    r.run("24h")
    log("Final results: {}".format(r.get_results()))     

