import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from ws.apis import *
from ws.shared.logger import *
import ws.hpo.bandit_config as bconf
import ws.shared.hp_cfg as hconf

import ws.hpo.bandit as bandit
import ws.hpo.batch_sim as batch
import ws.hpo.space_mgr as space

def data207_test(etr):
    hp_cfg = hconf.read_config("hp_conf/data207.json")
    samples = space.create_surrogate_space('data207')
    
    set_log_level('debug')
    
    run_cfg = bconf.read("arms.json", path="run_conf/")

    c = batch.get_simulator("ASYNC", "data207",
                        "TIME", 0.9999, 
                        "4h", run_cfg)
    results = c.run(1)
    for i in range(len(results)):
        result = results[i]
        log("At trial {}, {} iterations by {}".format(i, len(result["select_trace"]), result["select_trace"]))

if __name__ == "__main__":
    data207_test("None")
