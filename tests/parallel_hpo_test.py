import os
import sys
from collections import Counter
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
                        "24h",                         
                        run_cfg,
                        early_term_rule=etr)
    results = c.run(4)
    for i in range(len(results)):
        result = results[i]
        attempts = []
        for st in result["select_trace"]:
            for t in st:
                attempts.append(t)
        log("At trial {}, {} HPO attempts: {}".format(i, len(attempts), Counter(attempts)))

if __name__ == "__main__":
    data207_test("None")
#    data207_test("Gradient")
#    data207_test("VizMedian")
#    data207_test("Interval")
#    data207_test("Knock")
#    data207_test("IntervalKnock")
#    data207_test("IntervalMultiKnock")
