import os
import time
import json
import copy

from commons.logger import * 
from commons.proto import ManagerPrototype 

import hpo.utils.lookup as lookup

from hpo.sample_space import *
from hpo.connectors.remote_ctrl import RemoteSampleSpaceConnector


def create_surrogate_space(surrogate, grid_order=None):
    l = lookup.load(surrogate, grid_order=grid_order)
    s = SurrogateSamplingSpace(l)
    debug("Surrogate sampling space created: {}".format(surrogate))
    return s


def create_grid_space(hp_cfg_dict, num_samples=20000, grid_seed=1):
    if 'config' in hp_cfg_dict:
        if 'num_samples' in hp_cfg_dict['config']:
            num_samples = hp_cfg_dict['config']['num_samples']

        if 'grid_seed' in hp_cfg_dict['config']:
            grid_seed = hp_cfg_dict['config']['grid_seed']
    
    name = "grid_sample-{}".format(time.strftime('%Y%m%dT%H:%M:%SZ',time.gmtime()))
    hvg = HyperparameterVectorGenerator(hp_cfg_dict, num_samples, grid_seed)
    s = GridSamplingSpace(name, hvg.get_grid(), hvg.get_hpv(), hp_cfg_dict)
    debug("Grid sampling space created: {}".format(name))
    return s


def connect_remote_space(space_url):
    try:
        name = "grid-{}".format(space_url)
        connector = RemoteSampleSpaceConnector(space_url)
        return RemoteSamplingSpace(name, connector)
    except Exception as ex:
        warn("Fail to get remote samples: {}".format(ex))
        return None   


class SamplingSpaceManager(ManagerPrototype):

    def __init__(self, *args, **kwargs):
        super(SamplingSpaceManager, self).__init__("space_manager")
        self.spaces = {} 

    def create(self, space_spec):
        if "surrogate" in space_spec:
            surrogate = space_spec["surrogate"]
            grid_order = None        
            if "grid_order" in space_spec:
                grid_order = space_spec["grid_order"]

            s = create_surrogate_space(surrogate, grid_order)

        else:
            if not "hp_config" in space_spec:
                raise ValueError("No hp_config in sampling space spec: {}".format(space_spec))
            
            hp_cfg = space_spec['hp_config']
            num_samples = 20000
            grid_seed = 1               
            if "num_samples" in space_spec:
                num_samples = space_spec["num_samples"]
            if "grid_seed" in space_spec:
                grid_seed = space_spec["grid_seed"]

            s = create_grid_space(hp_cfg, num_samples, grid_seed)
        
        space_id = s.name
        space_obj = {"id" : space_id, "space": s }
        space_obj["created"] = time.strftime('%Y%m%dT%H:%M:%SZ',time.gmtime())
        space_obj["status"] = "created"    
        
        self.spaces[space_id] = space_obj

        return space_id

    def get_available_spaces(self):
        return list(self.spaces.keys())

    def set_space_status(self, space_id, status):
        if space_id in self.spaces:
            self.spaces['space_id']['status'] = status
            return True
        else:
            debug("No such space {} existed".format(space_id))
            return False

    def get_space(self, space_id):
        if space_id == "active":
            for s in self.spaces:
                if self.spaces[s]['status'] == "active":
                    return self.spaces[s]
            return None
        elif space_id in self.spaces:
            return self.spaces[space_id]
        else:
            debug("No such named space {} existed".format(space_id))
            return None

