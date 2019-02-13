import os
import sys
import datetime as dt

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import ws.hpo.bandit as bandit
import ws.hpo.bandit_config as rconf

import ws.shared.hp_cfg as hconf
import ws.hpo.space_mgr as space

from ws.shared.logger import *
import argparse

def test_run_main(surrogate, port, trials, duration):
    
    start_date = dt.datetime.now()
    log("{} trial(s) of each {} run start(s) at {}".format(trials, duration, start_date))

    set_log_level('debug')
    print_trace()

    # XXX: prerequisite: training worker service should be executed before running.
    trainer_url = 'http://147.47.120.82:{}'.format(port)
    
    hp_cfg_path = './hp_conf/{}.json'.format(surrogate)
    hp_cfg = hconf.read_config(hp_cfg_path)
    
    if hp_cfg is None:
        print("Invalid hyperparameter configuration file: {}".format(hp_cfg_path))
        return  

    run_cfg = rconf.read('arms-pure.json')
    
    samples = space.create_grid_space(hp_cfg.get_dict())
    runner = bandit.create_runner(trainer_url, samples,
                                'TIME', 0.999, duration,
                                run_cfg, hp_cfg
                                )

    runner.all_in('GP', 'UCB', trials, save_results=True)
    runner.temp_saver.remove()    
    end_date = dt.datetime.now()
    log("HPO ends at {} ({})".format(end_date, end_date - start_date))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, default=6000, help='Port number.')
    parser.add_argument('-t', '--trials', type=int, default=1, help='number of trials.')
    parser.add_argument('-d', '--duration', type=str, default="12h", help='The walltime to optimize.')
    args = parser.parse_args()
    
    test_run_main("data2", args.port, args.trials, args.duration)