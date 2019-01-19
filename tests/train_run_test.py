import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import ws.hpo.bandit as bandit
import ws.hpo.bandit_config as rconf
import ws.shared.hp_cfg as hconf
import ws.hpo.space_mgr as space

from ws.shared.logger import *


def test_run_main(surrogate):

    set_log_level('debug')
    print_trace()

    # XXX: prerequisite: training worker service should be executed before running.
    trainer_url = 'http://147.47.120.82:6001'
    #trainer_url = 'http://127.0.0.1:6001'
    hp_cfg_path = './hp_conf/{}.json'.format(surrogate)
    hp_cfg = hconf.read_config(hp_cfg_path)
    
    if hp_cfg is None:
        print("Invalid hyperparameter configuration file: {}".format(hp_cfg_path))
        return  

    run_cfg = rconf.read('p6div-etr.json')
    samples = space.create_surrogate_space(surrogate)
    #samples = space.create_grid_space(hp_cfg.get_dict())
    runner = bandit.create_runner(trainer_url, samples,
                                'TIME', 0.999, "1h",
                                #use_surrogate=surrogate, 
                                run_cfg, hp_cfg
                                )
    #runner.with_pkl = True

#    runner.all_in('HO', 'TPE', 1, save_results=False)
#    runner.all_in('RF', 'UCB', 1, save_results=True)
#    runner.mix('BO-HEDGE', 1, save_results=False)
    runner.mix('SEQ', 2, save_results=True)

    runner.temp_saver.remove()    


if __name__ == '__main__':
    test_run_main("data2")
