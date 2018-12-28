import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import hpo.bandit as bandit
import hpo.connectors.remote_space as remote
import hpo.bandit_config as run_config

from commons.logger import *


def test_run_main():
    # XXX: prerequisite: surrogate.py of training worker service should be executed before running.
    trainer_url = 'http://127.0.0.1:5000'
    space_url = 'http://127.0.0.1:5000'
    conf = run_config.read('arms-alet.json')
    samples = remote.connect_remote_space(space_url, "jo2fulwkq")
    runner = bandit.create_runner(trainer_url, samples,
                                'TIME', 0.999, '4h', 
                                run_config=conf)
    #runner.with_pkl = True
    set_log_level('debug')
    print_trace()

#    runner.all_in('HO', 'TPE', 1, save_results=False)
#    runner.all_in('RF', 'UCB', 1, save_results=True)
#    runner.mix('BO-HEDGE', 1, save_results=False)
    runner.mix('SEQ', 1, save_results=True)

    runner.temp_saver.remove()    


if __name__ == '__main__':
    test_run_main()
