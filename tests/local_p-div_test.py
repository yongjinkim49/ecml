import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from multiprocessing import Process, current_process

from ws.shared.logger import *

from ws.hpo.connectors.multi_ctrl import *

import ws.hpo.bandit_config as bconf
import ws.shared.hp_cfg as hconf

if __name__ == '__main__':    
    set_log_level('debug')

    run_cfg = bconf.read('data207_tv4.json')
    hp_cfg = hconf.read_config('./hp_conf/data207.json')    
    r = LocalParallelOptimizerController(run_cfg, hp_cfg)    
    #r.fork_daemons() # FIXME: forking daemons makes some issues.
    r.run("24h")
    log("Final results: {}".format(r.get_results()))     

