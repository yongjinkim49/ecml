from __future__ import division
from __future__ import print_function

import copy
import math

import pandas as pd
import numpy as np
from util import *

from hyperopt import hp, fmin, tpe, base, rand, Trials, STATUS_OK, JOB_STATE_DONE

import ws.shared.hp_cfg as hp_cfg
from ws.shared.logger import *
from ws.shared.resp_shape import *
from ws.hpo.utils.converter import VectorGridConverter

def init(samples, arg_string):
    args = unpack_args(arg_string)
    ssc = HyperOptSearchSpaceConfig(samples.get_hp_config())    
    return HyperOptChooser(ssc, **args)


class HyperOptChooser(object):

    def __init__(self, space_cfg,
                 response_shaping=False,
                 shaping_func="log_err"):
        self.space_cfg = space_cfg
        self.hyperparams = space_cfg.get_params()
        self.hyperopt_space = space_cfg.get_hyperopt_space()
        self.acq_funcs = ['EI', 'RANDOM']
        self.mean_value = None
        self.estimates = None
        self.last_params = None
        self.response_shaping = bool(response_shaping)
        self.shaping_func = shaping_func

    def set_eval_time_penalty(self, est_eval_time):
        # TODO:We can not apply the evaluation time penalty now. 
        pass

    def next(self, samples, acq_func, use_interim=True):
        algo = tpe.suggest
        if acq_func == 'RANDOM':
            algo = rand.suggest
        elif acq_func != 'EI':
            debug("Unsupported acquisition function: {}".format(acq_func))

        helper = HyperoptTrialMaker(samples.get_hpv(), self.hyperparams)
        #history = objective.create_history(samples.get_completes())
        t = helper.create_trials(samples.get_completes(), 
                                samples.get_errors("completes", use_interim))
        
        debug("number of items in history: {}".format(len(t.trials)))
        num_iters = len(t.trials) + 1
        fmin(self.fake_evaluate, self.hyperopt_space, algo, num_iters,
                        trials=t, return_argmin=False) 

        hpv = self.get_last_hpv()
        idx = samples.expand(hpv)
        return idx

    def get_last_hpv(self):
        hpv = []
        if self.last_params != None:
            for p in self.hyperparams:
                hpv.append(self.last_params[p])
        
        return np.array(hpv)

    def fake_evaluate(self, params):
        # XXX: replace index value of categorical string type to original string 
        params = self.space_cfg.replace_string_values(params)
        debug("Selected by HyperOpt: {}".format(params))
        
        est_loss = 0.5 # XXX:meaningless loss value
        self.last_params = params
        
        return create_ok_result(est_loss)                 


class HyperOptSearchSpaceConfig(object):
    
    def __init__(self, config):
        self.config = config

    def get_hyperopt_space(self):
        space = {}
        
        for param, setting in self.config.hyperparams.__dict__.items():
            range_distribution = None
            if setting.value_type == 'discrete' and setting.type == 'int':
                if hasattr(setting, 'power_of'):
                    base = setting.power_of
                    log_range = []
                    # transform setting.range values to log
                    for value in setting.range:
                        log_range.append(int(math.log(base**value)))                    
                    range_distribution = hp.qloguniform(param, log_range[0], log_range[-1], 1)                     
                else:
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
            elif setting.value_type == 'categorical' or setting.value_type == 'preordered':
                options = []
                str_index = 0
                for c in setting.range:
                    if isinstance(c, (str, unicode)):
                        # XXX: To avoid binning error
                        c = str_index #str(c)
                        str_index += 1
                    options.append(c)

                range_distribution = hp.choice(param, options)
            else:
                error('invalid configuration: %s, %s' % (setting.value_type, setting.value))
            space[param] = range_distribution

        return space

    def get_params(self):
        return self.config.param_order

    def replace_string_values(self, param_values):
        for param, setting in self.config.hyperparams.__dict__.items():
            if setting.type == "str":
                if setting.value_type == 'categorical':
                    index_value = param_values[param]
                    str_value = setting.range[index_value]
                    param_values[param] = str_value
                else:
                    warn("Unknown case: {} - {}".format(param, setting.value_type))
        return param_values

def create_ok_result(loss, index=None):
    ok_result = {
        'loss': loss,
        'status': STATUS_OK
    }
    if index != None:
        ok_result['idx'] = index

    return ok_result


class HyperoptTrialMaker(object):
    def __init__(self, hpvs, param_order):
        self.hpvs = hpvs
        self.param_order = param_order

    def create_history(self, complete):
        history = []
        if len(complete) > 0:
            for ci in complete:
                hpv = self.hpvs[ci]
                if len(self.param_order) == len(hpv):
                    h = {}
                    for i in range(len(self.param_order)):
                        str_index = 0
                        val = hpv[i]
                        if isinstance(val, (int, long)):
                            val = int(val)
                        elif isinstance(val, (str, unicode)):
                            #XXX: String value raises binning error. To avoid this error, we replace it an index
                            val = str_index #str(val)
                            str_index += 1
                        h[str(self.param_order[i])] = val
                    history.append(h)
                else:
                    error("size mismatch: {} != {}".format(hpv, self.param_order))
                
        return history

    def create_trials(self, complete, losses):
        if len(complete) > 0:
            trials = Trials()
            hist = self.create_history(complete)
            index = 0
            for c in complete:
                loss = losses[c]
                rval_specs = [None]
                new_id = index
                rval_results = [ ]
                rval_results.append(create_ok_result(loss, c))
                rval_miscs = [  ]
                rval_miscs.append(self.create_misc(index, hist))
                
                hyperopt_trial = trials.new_trial_docs([new_id], rval_specs, rval_results, rval_miscs)[0]
                index += 1
                if self.response_shaping is True:
                    # transform log applied loss for enhancing optimization performance
                    if self.shaping_func == "log_err":
                        debug("before scaling: {}".format(loss))
                        loss = apply_log_err(loss)
                    elif self.shaping_func == "hybrid_log":
                        loss = apply_hybrid_log(loss)
                    else:
                        debug("Invalid shaping function: {}".format(self.shaping_func))                    
                hyperopt_trial['result'] = {'loss': loss, 'status': STATUS_OK}
                hyperopt_trial['state'] = JOB_STATE_DONE
                
                trials.insert_trial_doc(hyperopt_trial)
            trials.refresh()
            return trials
        else:        
            return Trials()

    def create_misc(self, index, history):
        misc = {'tid': index, 
                'cmd': ('domain_attachment', 'FMinIter_Domain'), 
                'idxs': {}, 'vals': {} }
        result = history[index]
        for key in result.keys():
            misc['idxs'][key] = [ index ] 
            misc['vals'][key] = [ result[key] ] 
        
        return misc

