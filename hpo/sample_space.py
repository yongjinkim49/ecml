import numpy as np
import time
from commons.logger import *
from hpo.utils.grid_gen import *
from hpo.connectors.remote_ctrl import RemoteSampleSpaceConnector
from hpo.utils.converter import VectorGridConverter


def get_remote_samples(name, space_url):
    try:
        connector = RemoteSampleSpaceConnector(space_url)
        return RemoteSamplingSpace(name, connector)
    except Exception as ex:
        warn("Fail to get remote samples: {}".format(ex))
        return None
  

class SearchHistory(object):
    def __init__(self, num_samples):
        self.num_samples = num_samples
        self.reset()       

    def reset(self):
        self.complete = np.arange(0)
        self.candidates = np.setdiff1d(np.arange(self.num_samples), self.complete)
        
        self.observed_errors = np.ones(self.num_samples)

    def get_candidates(self):
        return self.candidates

    def get_completes(self):
        return self.complete

    def update(self, model_index, test_error):
        if not model_index in self.complete:
            self.candidates = np.setdiff1d(self.candidates, model_index)
            self.complete = np.append(self.complete, model_index)
        self.observed_errors[model_index] = test_error

    def get_errors(self, type_or_id):
        if type_or_id == "completes":
            return self.observed_errors[self.complete]
        else:
            return self.observed_errors[type_or_id]

    def append(self):
        # TODO: check hyperparams are existed
        model_index = self.num_samples # assign new model index
        self.complete = np.append(self.complete, model_index)
        self.observed_errors = np.append(self.observed_errors, 0.0) 
        
        self.num_samples += 1
        return model_index

class GridSamplingSpace(SearchHistory):

    def __init__(self, name, grid, hpv, hp_config):
        self.name = name
        self.hp_config = hp_config

        self.grid = np.asarray(grid)
        self.hpv = hpv

        super(GridSamplingSpace, self).__init__(len(hpv))

    def get_name(self):
        return self.name

    def get_hp_config(self):
        return self.hp_config

    def get_params(self):
        return self.hp_config.param_order

    def get_grid(self, index=None):
        if index == "completes":
            completes = self.get_completes()
            #debug("index of completes: {}".format(completes))
            return self.grid[completes, :]
        elif index == "candidates":
            candidates = self.get_candidates()
            #debug("index of candidates: {}".format(candidates))
            return self.grid[candidates, :]        
        elif index != None:
            return self.grid[index]
        else:
            return self.grid

    def get_hpv(self, index=None):
        if index != None:
            params = self.hp_config.param_order
            args = self.hpv[index]
            hpv = {}
            for i in range(len(params)):
                p = params[i]
                hpv[p] = args[i]
            return hpv
        else:
            return self.hpv

    def append(self, hpv):
        cvt = VectorGridConverter(self.hpv, self.get_candidates(), self.hp_config)
        grid_vec = cvt.to_grid_vector(hpv)
        
        self.hpv = np.append(self.hpv, hpv)
        self.grid = np.append(self.grid, grid_vec) 
        return super(GridSamplingSpace, self).append()


class SurrogateSamplingSpace(GridSamplingSpace):

    def __init__(self, lookup):

        self.grid = lookup.get_sobol_grid()
        self.hpv = lookup.get_hyperparam_vectors()

        super(SurrogateSamplingSpace, self).__init__(lookup.data_type, self.grid, self.hpv, 
                                                    lookup.hp_config)
        # preloaded results
        self.test_errors = lookup.get_test_errors()
        self.exec_times = lookup.get_elapsed_times()
        self.lookup = lookup

    # For search history 

    def update(self, model_index, test_error=None):
        if test_error is None:
            test_error = self.test_errors[model_index]
        super(GridSamplingSpace, self).update(model_index, test_error)

    def get_test_error(self, index=None):
        if index != None:
            return self.test_errors[index]
        else:
            return self.test_errors

    def get_exec_time(self, index=None):
        if index != None:
            return self.exec_times[index]
        else:
            return self.exec_times

    def append(self, hpv):
        # return approximated index instead of newly created index
        cvt = VectorGridConverter(self.hpv, self.get_candidates(), self.hp_config)
        idx, err_distance = cvt.get_nearby_index(hpv)

        debug("Distance btw selection and surrogate: {}".format(err_distance))
        return idx


class RemoteSamplingSpace(SearchHistory):
    def __init__(self, name, proxy):
        self.space = proxy
        
        num_samples = proxy.get_num_samples()
        self.name = "remote_{}".format(name)

        return super(RemoteSamplingSpace, self).__init__(num_samples)

    def get_name(self):
        return self.name

    def get_hp_config(self):
        return self.space.hp_config

    def get_params(self):
        return self.space.hp_config["param_order"]

    def get_grid(self, index=None):
        
        if index == None:
            return np.asarray(self.space.get_grid('all'))
        else:
            return np.asarray(self.space.get_grid(index))

    def get_hpv(self, index=None):
        if index == None:
            return self.space.get_vector('all')
        else:
            return self.space.get_vector(index)

    # For history
    def get_candidates(self):
        return np.asarray(self.space.get_candidates())

    def get_completes(self):
        return np.asarray(self.space.get_completes())

    def update(self, model_index, test_error):
        self.space.update_error(model_index, test_error)

    def get_errors(self, type_or_id):
        return np.asarray(self.space.get_error(type_or_id))

