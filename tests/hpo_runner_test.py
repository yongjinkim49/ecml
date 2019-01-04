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
import ws.hpo.space_mgr as space

def data207_test(etr):
    hp_cfg = hconf.read_config("hp_conf/data207.json")
    samples = space.create_surrogate_space('data207')
    
    #set_log_level('debug')
    
    run_cfg = bconf.read("arms.json", path="run_conf/")
    m = bandit.create_emulator(samples, 
                'TIME', 0.9999, '3d',
                early_term_rule=etr,
                run_config=run_cfg)
    results = m.mix('RANDOM', 1)
    for i in range(len(results)):
        result = results[i]
        log("At trial {}, {} iterations by {}".format(i, len(result["select_trace"]), Counter(result["select_trace"])))

if __name__ == "__main__":
    data207_test("None")
    data207_test("Gradient")
    data207_test("VizMedian")
    data207_test("Interval")
    data207_test("Knock")
    data207_test("IntervalKnock")
    data207_test("IntervalMultiKnock")

