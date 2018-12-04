import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from hpo.interface import *
import hpo.bandit_config as run_config

def main():
    run_cfg = run_config.read('parallel-test.json')
    wait_seq_opt_request(run_cfg, True)

if __name__ == "__main__":
    main()
    