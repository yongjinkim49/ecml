import numpy as np
import pandas as pd

import json
import os
import sys
import traceback

from collections import namedtuple
from wot.utils.logger import *


class DictObject(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [DictObject(x) 
                    if isinstance(
                        x, dict) else x for x in b])
            else:
                setattr(self, a, DictObject(b) 
                    if isinstance(b, dict) else b)


class HyperparameterConfiguration(DictObject):
    def __init__(self, d):
        self._dict = d
        super(HyperparameterConfiguration, self).__init__(d)
        
    def get_hyperparams(self):
        return self._dict['param_order']


def read_config(cfg_file):
    if os.path.exists(cfg_file):
        cfg = read(cfg_file)
        if validate(cfg):
            return cfg
    return None


def read(cfg_file_name):
    with open(cfg_file_name) as json_cfg:
        json_dict = json.load(json_cfg)
        cfg = HyperparameterConfiguration(json_dict)
        return cfg


def validate(cfg):
    if not hasattr(cfg, 'hyperparams'):
        error('json object does not contain hyperparams attribute.')
        return False

    for hyperparam, conf in cfg.hyperparams.__dict__.items():

        # attribute existence test
        if not hasattr(conf, 'type'):
            error(hyperparam + " has not type attribute.")
            return False
        else:
            supported_types = ['int', 'float', 'str', 'bool', 'unicode']
            if not conf.type in supported_types:
                return False

        if not hasattr(conf, 'value_type'):
            error(hyperparam + " has not value_type attribute.")
            return False
        else:
            supported_value_types = ['discrete', 'continuous', 'preordered', 'categorical']
            if not conf.value_type in supported_value_types:
                return False

        if not hasattr(conf, 'range'):
            error(hyperparam + " has not range attribute.")
            return False
        else:
            range_list = conf.range
            if len(range_list) is 0:
                error(hyperparam + " has no range values")
                return False

            for value in range_list:
                value_type_name = type(value).__name__
                if value_type_name == 'unicode':
                    value_type_name = 'str'
                
                if value_type_name != conf.type:
                    if conf.type == "float" and type(value) == int:
                        # type can be convertible
                        pass
                    elif not hasattr(conf, 'power_of'):
                        warn(hyperparam + " has invalid type item.")
                        # check value has convertible to it's own type
    return True


def get_hyperparam_type(cfg, name):
    range = []
    hyperparams = cfg.hyperparams
    if name in hyperparams.__dict__.keys():
        hyperparam = getattr(hyperparams, name)
        if hyperparam.type == 'unicode':
            return "str"
        else:
            return hyperparam.type
    
    return range


def get_hyperparam_range(cfg, name):
    range = []
    hyperparams = cfg.hyperparams
    if name in hyperparams.__dict__.keys():
        hyperparam = getattr(hyperparams, name)
        range = hyperparam.range
        
        if hasattr(hyperparam, 'power_of'):
            base = hyperparam.power_of
            range = []
            for power in hyperparam.range:
                range.append(base**power)

        if hyperparam.type == 'unicode':
            range = []
            for item in hyperparam.range:
                range.append(item.encode('ascii', 'ignore'))
            
    return range


def test_main():
    cfg = read('lookup/data2.json')
    log(validate(cfg))
    params = sorted(cfg.hyperparams.__dict__.keys())
    log(params)    
    for param in params:
        log(get_hyperparam_range(cfg, param))

if __name__ == '__main__':
    test_main()
