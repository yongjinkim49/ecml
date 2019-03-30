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

#def data207_test(etr):
#    hp_cfg = hconf.read_config("hp_conf/data207.json")
#    samples = space.create_surrogate_space('data207')
#    
#    #set_log_level('debug')
#    
#    run_cfg = bconf.read("arms.json", path="run_conf/")
#    run_cfg["early_term_rule"] = etr
#    m = bandit.create_emulator(samples, 
#                'TIME', 0.935, '5d',
#                run_config=run_cfg)
#    results = m.mix('SEQ', 1, save_results=False)
#    for i in range(len(results)):
#        result = results[i]
#        log("At trial {}, {} iterations by {}".format(i, len(result["select_trace"]), Counter(result["select_trace"])))
#
#def data20_test(etr):
#    hp_cfg = hconf.read_config("hp_conf/data20.json")
#    samples = space.create_surrogate_space('data20')
#    
#    set_log_level('debug')
#    
#    run_cfg = bconf.read("arms.json", path="run_conf/")
#    run_cfg["early_term_rule"] = etr
#    m = bandit.create_emulator(samples, 
#                'TIME', 0.9999, '1d',
#                run_config=run_cfg)
#    results = m.mix('SEQ', 1, save_results=False)
#    for i in range(len(results)):
#        result = results[i]
#        log("At trial {}, {} iterations by {}".format(i, len(result["select_trace"]), Counter(result["select_trace"])))
#
#def data3_test(etr):
#    hp_cfg = hconf.read_config("hp_conf/data3.json")
#    samples = space.create_surrogate_space('data3')
#    
#    set_log_level('debug')
#    
#    run_cfg = bconf.read("arms.json", path="run_conf/")
#    run_cfg["early_term_rule"] = etr
#    m = bandit.create_emulator(samples, 
#                'TIME', 0.9999, '1d',
#                run_config=run_cfg)
#    results = m.mix('SEQ', 1, save_results=False)
#    for i in range(len(results)):
#        result = results[i]
#        log("At trial {}, {} iterations by {}".format(i, len(result["select_trace"]), Counter(result["select_trace"])))

def data_test(etr, scope_start, scope_end, threshold, degree):
    for model in ['GP','RF']:
        for data_name in ['data2','data3','data10','data20','data30','data207']:
            for i in range(51,52):
                hp_cfg = hconf.read_config("hp_conf/{}.json".format(data_name))
                samples = space.create_surrogate_space('{}'.format(data_name))

                #set_log_level('debug')

                time = '12h'
                if data_name == 'data2':
                    goal = 0.9933
                if data_name == 'data3':
                    goal = 0.9922 
                if data_name == 'data10':
                    goal = 0.8994
                if data_name == 'data20':
                    goal = 0.784
                if data_name == 'data30':
                    goal = 0.4596
                if data_name == 'data207':
                    time = '5d'
                    goal = 0.9334

                run_cfg = bconf.read("arms.json", path="run_conf/")
                run_cfg["early_term_rule"] = etr
                m = bandit.create_emulator(samples, 
                            'TIME', 0.9999, time,
                            run_config=run_cfg,
                            scope_start = scope_start, scope_end = scope_end,
                            threshold = threshold, degree = degree)

                for acq in ['EI']:
                    results = m.all_in(model, acq, i)
                    for n in range(len(results)):
                        result = results[n]
                        log("At trial {}, {} iterations by {}".format(n, len(result["select_trace"]), Counter(result["select_trace"])))


if __name__ == "__main__":
    #early_term_test = data20_test
    #early_term_test("None")
    #early_term_test("Donham15")
    #early_term_test("Donham15Fantasy")
    #early_term_test("Interval")
    #early_term_test("Knock")
    #early_term_test("PentaTercet")

#### THE COMPOUND RULE WITH FANTASY
    data_test("BETA90fan1", 0.0, 0.0, 90.0, 1)
    data_test("BETA90fan2", 0.0, 0.0, 90.0, 2)
    data_test("BETA90fan3", 0.0, 0.0, 90.0, 3)
    data_test("BETA85fan1", 0.0, 0.0, 85.0, 1)
    data_test("BETA85fan2", 0.0, 0.0, 85.0, 2)
    data_test("BETA85fan3", 0.0, 0.0, 85.0, 3)
    data_test("BETA80fan1", 0.0, 0.0, 80.0, 1)
    data_test("BETA80fan2", 0.0, 0.0, 80.0, 2)
    data_test("BETA80fan3", 0.0, 0.0, 80.0, 3)
    data_test("BETA75fan1", 0.0, 0.0, 75.0, 1)
    data_test("BETA75fan2", 0.0, 0.0, 75.0, 2)
    data_test("BETA75fan3", 0.0, 0.0, 75.0, 3)

