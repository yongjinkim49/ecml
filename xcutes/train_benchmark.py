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

def test_run_main(surrogate, ip, port, trials, duration, log_level='log'):
    
    start_date = dt.datetime.now()
    log("{} trial(s) of each {} start(s) at {}".format(trials, duration, start_date))

    set_log_level(log_level)
    print_trace()

    # XXX: prerequisite: training worker service should be executed before running.
    trainer_url = 'http://{}:{}'.format(ip, port)  # 147.47.120.82
    
    hp_cfg_path = './hp_conf/{}.json'.format(surrogate)
    hp_cfg = hconf.read_config(hp_cfg_path)
    
    if hp_cfg is None:
        print("Invalid hyperparameter configuration file: {}".format(hp_cfg_path))
        return  

    run_cfg = rconf.read('p6div-etr.json') # p6div-etr.json arms.json
    
    samples = space.create_grid_space(hp_cfg.get_dict())
    runner = bandit.create_runner(trainer_url, samples,
                                'TIME', 0.999, duration,
                                run_cfg, hp_cfg
                                )

    runner.mix('SEQ', trials, save_results=True)
    runner.temp_saver.remove()    
    end_date = dt.datetime.now()
    log("HPO ends at {} ({})".format(end_date, end_date - start_date))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, default="bm1", help='hyperparameter configuration.')
    parser.add_argument('-ip', '--ip_addr', type=str, default="147.47.120.82", help='IP address.')
    parser.add_argument('-t', '--trials', type=int, default=1, help='number of trials.')
    parser.add_argument('-d', '--duration', type=str, default="2h", help='The walltime to optimize.')
    parser.add_argument('-l', '--log', type=str, default="log", help='The log level.')
    
    parser.add_argument('port', type=int, default=6001, help='Port number.')
    
    args = parser.parse_args()
    
    test_run_main(args.config, args.ip_addr, args.port, args.trials, args.duration, args.log)

if __name__ == '__main__':
    #test_run_main("data2", '127.0.0.1', 6001, 40, "12h")
    main()
