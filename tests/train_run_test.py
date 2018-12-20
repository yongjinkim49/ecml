import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import hpo.bandit as bandit
import hpo.bandit_config as run_config
import hpo.hp_config as hp_config

from commons.logger import *


def test_run_main():
    # XXX: prerequisite: training worker service should be executed before running.
    trainer_url = 'http://147.47.120.182:6001'
    hp_cfg_path = './hp_conf/data207.json'
    hp_cfg = hp_config.read_config(hp_cfg_path)
    
    if hp_cfg is None:
        print("Invalid hyperparameter configuration file: {}".format(hp_cfg_path))
        return  

    conf = run_config.read('arms.json')
    space = bandit.create_surrogate_space('data207', conf)
    runner = bandit.create_runner(trainer_url, space,
                                'TIME', 0.999, 4 * 60 * 60, 
                                run_config=conf, hp_config=hp_cfg)
    #runner.with_pkl = True
    set_log_level('debug')
    print_trace()

#    runner.all_in('HO', 'TPE', 1, save_results=False)
#    runner.all_in('RF', 'UCB', 1, save_results=True)
#    runner.mix('BO-HEDGE', 1, save_results=False)
    runner.mix('SEQ', 1, save_results=False)

    runner.temp_saver.remove()    


if __name__ == '__main__':
    test_run_main()
