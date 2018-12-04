import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import hpo.bandit as bandit
import hpo.bandit_config as run_config

from hpo.utils.logger import *

def test_emul_main():

    conf = run_config.read('pairing/2fools.json')
    emul = bandit.create_emulator('data3', 'TIME', 0.999, '6h', 
                run_config=conf)
    #emul.with_pkl = True
    set_log_level('debug')
    print_trace()

    emul.all_in('HO', 'RANDOM', 1, save_results=False)

#    emul.mix('SEQ', 1, save_results=False)

    emul.temp_saver.remove()


if __name__ == '__main__':
    test_emul_main()