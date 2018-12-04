import math
import numpy as np

from hyperopt import hp

import hp_cfg as hp_cfg
from logger import *

def init(config):
    return SearchSpace(config)

class SearchSpace(object):

    def __init__(self, config):
        self.config = config

    def get_hyperopt_space(self):
        space = {}
        
        for param, setting in self.config.hyperparams.__dict__.items():
            range_distribution = None
            if setting.value_type == 'discrete' and setting.type == 'int':
                range_distribution = hp.quniform(param, setting.range[0], setting.range[-1], 1)
            elif setting.value_type == 'continuous' and setting.type == 'float':
                if hasattr(setting, 'power_of'):
                    base = setting.power_of
                    log_range = []
                    # transform setting.range values to log
                    for value in setting.range:
                        log_range.append(math.log(base**value))                    
                    range_distribution = hp.loguniform(param, log_range[0], log_range[-1])                     
                else:
                    range_distribution = hp.uniform(param, setting.range[0], setting.range[-1])
            elif setting.value_type == 'categorical':
                range_distribution = hp.choice(param, setting.range)
            else:
                error('invalid configuration: %s, %s' % (setting.value_type, setting.value))
            space[param] = range_distribution

        return space, self.config.param_order


if __name__ == "__main__":
    cfg = hp_cfg.read('lookup/data2.json')
    space = SearchSpace(cfg)
    tpe_space, param_order = space.get_hyperopt_space()
    log(str(tpe_space))
    log(param_order)
    pass