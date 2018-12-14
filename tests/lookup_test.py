import os
import sys

# For path arrangement (set the parent directory as the root folder)
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from hpo.utils.lookup import *

if __name__ == '__main__':
    l = load('data207', data_folder='./lookup/')
    print(l.num_hyperparams)
    print(list([int(t) for t in l.get_elapsed_times()]))