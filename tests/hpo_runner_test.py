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

def data2_test(etr):
    hp_cfg = hconf.read_config("hp_conf/data3.json")
    samples = space.create_surrogate_space('data3')
    
    #set_log_level('debug')
    
    run_cfg = bconf.read("arms-w6h.json", path="run_conf/")
    m = bandit.create_emulator(samples, 
                'TIME', 0.9999, '1d',
                early_term_rule=etr,
                run_config=run_cfg)
    results = m.mix('SEQ', 10)
    for i in range(len(results)):
        result = results[i]
        log("At trial {}, {} iterations by {}".format(i, len(result["select_trace"]), Counter(result["select_trace"])))

if __name__ == "__main__":
    #data2_test("None")
    #data2_test("Gradient")
    #data2_test("VizMedian")
    #data2_test("Interval")
    #data2_test("Knock")
    data2_test("IntervalKnock")
    #data2_test("KickStarter")
    

