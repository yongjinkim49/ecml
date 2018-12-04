from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import math
import random
import json

import hpo.choosers.gp_chooser as gpc
import hpo.choosers.rf_chooser as rfc
import hpo.choosers.hyperopt_chooser as hoc
import hpo.choosers.random_chooser as RandomChooser

from hpo.strategies import *
from hpo.utils.logger import *
from hpo.eval_time import * 


def read(cfg_file_name, path='run_conf/'):
    try:
        #debug(path + cfg_file_name)
        with open(path + cfg_file_name) as json_cfg:
            json_dict = json.load(json_cfg)
            return json_dict   
    except Exception as ex:
        error('Exception on read json'.format(ex))
        raise ValueError('config file not found.')


def validate(config):
    # validate config schema
    try:
        if type(config) is not dict:
            return False

        #if not "title" in config.keys():
        #    return False

        if "arms" in config.keys():
            if len(config["arms"]) == 0:
                error("no arm is listed.")
                return False
            else:
                for arm in config["arms"]:
                    if not "model" in arm.keys():
                        raise ValueError("no mode attribute in bandit")
                    if not "acq_func" in arm.keys():
                        raise ValueError("no spec attribute  in bandit")
                    # TODO: validate value
                return True
        if "bandits" in config.keys():
            if len(config["bandits"]) == 0:
                error("no bandit is listed.")
                return False
            else:
                for bandit in config["bandits"]:
                    if not "mode" in bandit.keys():
                        raise ValueError("no model attribute in bandit")
                    if not "spec" in bandit.keys():
                        raise ValueError("no strategy attribute  in bandit")
                    # TODO: validate value
                return True            
    except:
        error("invalid configuration: {}".format(config))
        return False


class BanditConfigurator(object):

    def __init__(self, samples, config, time_penalties=[]):
        self.config = config
        self.samples = samples

        self.time_acq_funcs = get_time_acq_funcs(time_penalties)
        self.choosers = self.init_choosers(config)

    def init_choosers(self, config):
        
        opts = list(set([a['model'] for a in config['arms']]))
        choosers = {}

        # Add default modeling methods
        if not 'RANDOM' in opts:
            opts.append('RANDOM')

        if not 'GP' in opts:
            opts.append('GP')

        if not 'RF' in opts:
            opts.append('RF')

        log_options = ''
        if self.config is not None and 'log' in self.config:
            for key in self.config['log'].keys():
                val = self.config['log'][key]
                log_options += ',{}={}'.format(key, val)

        # for global GP options
        gp_options = 'noiseless=0' + log_options

        if self.config is not None and 'gp' in self.config:
            for gk in self.config['gp'].keys():
                gv = self.config['gp'][gk]
                gp_options += ',{}={}'.format(gk, gv)

        if 'GP' in opts:
            gp = gpc.init('.', gp_options)
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP'] = gp
 
        if 'GP0' in opts:
            gp = gpc.init('.', gp_options+',trade_off=0.01,v=0.2')
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP0'] = gp

        if 'GP1' in opts:
            gp = gpc.init('.', gp_options+',trade_off=0.1,v=1.0')
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP1'] = gp
        
        if 'GP2' in opts:
            gp = gpc.init('.', gp_options+',trade_off=1.0,v=0.1')
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP2'] = gp

        if 'GP-NM' in opts:
            gp = gpc.init('.', 'noiseless=1,mcmc_iters=1')
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP-NM'] = gp

        if 'GP-LE' in opts:
            gp_options = 'noiseless=0,log_err=True'
            gp = gpc.init('.', gp_options)
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP-LE'] = gp

        if 'GP-HLE' in opts:
            gp_options = 'noiseless=0,log_err=True,log_err_func=ada_log_3'
            gp = gpc.init('.', gp_options)
            if len(self.time_acq_funcs) > 0:
                gp.add_time_acq_funcs(self.time_acq_funcs)
            choosers['GP-HLE'] = gp

        if 'RANDOM' in opts:
            choosers['RANDOM'] = RandomChooser.init('.', '')

        # for global RF options
        rf_options = "max_features=auto" + log_options
        if self.config is not None and 'rf' in self.config:
            for rk in self.config['rf'].keys():
                rv = self.config['rf'][rk]
                if rf_options != "":
                    rf_options += ','
                rf_options += '{}={}'.format(rk, rv)

        if 'RF' in opts:
            choosers['RF'] = rfc.init('.', rf_options)

        if 'RF-LE' in opts:
            rf_options = 'log_err=True'
            choosers['RF-LE'] = rfc.init('.', rf_options)

        if 'RF-HLE' in opts:
            rf_options = 'log_err=True,log_err_func=ada_log_3'
            choosers['RF-HLE'] = rfc.init('.', rf_options)

        if 'HO' in opts:
            # XXX: This TPE is a suspicious optimizer due to using lookup. carefully use it.
            choosers['HO'] = hoc.init(self.samples)

        if 'HO-HLE' in opts:
            # XXX: This TPE is a suspicious optimizer due to using lookup. carefully use it.
            choosers['HO-HLE'] = hoc.init(self.samples)
        return choosers

    def get_arm(self, spec, ):
        return ArmSelector(spec, self.config, self.samples, self.choosers)
         

class ArmSelector(object):
    def __init__(self, spec, config, samples, choosers):
                
        self.config = config

        self.arms = config['arms']        
        self.num_arms = len(self.arms)
        self.cur_arm_index = None

        self.init_rewards()   

        self.spec = spec
        self.samples = samples
        self.choosers = choosers

        self.strategy = self.register(spec)
        self.num_skip = 0

    def init_rewards(self):
        self.values = []
        self.counts = []

        for arm in range(self.num_arms):
            self.values.append(0.0)
            self.counts.append(0)   

    def update(self, step, curr_acc, estimates):
        '''reward update'''
        if self.cur_arm_index is not None and step >= self.num_skip:
            self.strategy.update(self.cur_arm_index, curr_acc, estimates)
            arm = self.arms[self.cur_arm_index]
            debug("At step {}, HPO by {}-{} will be proceeded.".format(
                step, arm['model'], arm['acq_func']))
            if self.spec != 'SEQ' and self.spec != 'RANDOM':
                debug("Arm selection ratio: {}, Current epsilon: {}".format(
                    [round(v, 2) for v in self.values], self.strategy.epsilon))                 

    def select(self, step):
        if step < self.num_skip:
            next_index = np.random.randint(0, self.num_arms)
            debug('random sampling before step {} passes'.format(self.num_skip)) 
        else:
            next_index = self.strategy.next(step)
        arm = self.arms[next_index]
        self.cur_arm_index = next_index
        
        return arm['model'], arm['acq_func'], next_index

    def register(self, spec):        
        ''' register the diversification strategies '''
        title = ''
        if title in self.config: 
            title = self.config['title']
        
        if spec == 'SEQ':
            return SequentialStrategy(self.num_arms, self.values, self.counts, 
                                    title)
        elif spec == 'SKO':
            num_iters_per_round = self.num_arms * 10
            return SequentialKnockOutStrategy(self.num_arms, self.values, self.counts,
                                            num_iters_per_round, title)
        elif spec == 'RANDOM':
            return RandomStrategy(self.num_arms, self.values, self.counts, 
                                    title)
        elif spec == 'HEDGE':
            eta = 1
            if 'eta' in self.config.keys():
                eta = self.config['eta']
            return ClassicHedgeStrategy(self.arms, eta, self.values, self.counts, 
                                        title)
        elif spec == 'BO-HEDGE':
            eta = 0.1
            if 'eta' in self.config.keys():
                eta = self.config['eta']
            return BayesianHedgeStrategy(self.arms, eta, 
                                        self.values, self.counts, 
                                        self.samples, self.choosers, 
                                        title=title)
        elif spec == 'BO-HEDGE-T':
            eta = 0.1
            if 'eta' in self.config.keys():
                eta = self.config['eta']
            return BayesianHedgeStrategy(self.arms, eta, 
                                        self.values, self.counts, 
                                        self.samples, self.choosers, 
                                        title=title,
                                        unbiased_estimation=True)
        elif spec == 'BO-HEDGE-LE':
            eta = 0.1
            if 'eta' in self.config.keys():
                eta = self.config['eta']
            return BayesianHedgeStrategy(self.arms, eta, 
                                        self.values, self.counts, 
                                        self.samples, self.choosers, 
                                        title=title,
                                        reward_scaling="LOG_ERR")
        elif spec == 'BO-HEDGE-LET':
            eta = 0.1
            if 'eta' in self.config.keys():
                eta = self.config['eta']
            return BayesianHedgeStrategy(self.arms, eta, 
                                        self.values, self.counts, 
                                        self.samples, self.choosers, 
                                        title=title,
                                        unbiased_estimation=True,
                                        reward_scaling="LOG_ERR")                                                   
        elif spec == 'EG':
            init_eps = 1.0
            decay_factor = 5
            
            self.num_skip = 2 #XXX: avoiding first two selection bias  

            if 'init_eps' in self.config.keys():
                init_eps = self.config['init_eps']
            if 'decay_factor' in self.config.keys():
                decay_factor = self.config['decay_factor']

            return EpsilonGreedyStrategy(self.num_arms, self.values, self.counts, 
                        title,
                        init_eps=init_eps, 
                        decay_factor=decay_factor)
        elif spec == 'EG-LE':
            init_eps = 1.0
            decay_factor = 5            
            reward_scaling = 'LOG_ERR'
            
            self.num_skip = 2 #XXX: avoiding first two selection bias  

            if 'init_eps' in self.config.keys():
                init_eps = self.config['init_eps']
            if 'decay_factor' in self.config.keys():
                decay_factor = self.config['decay_factor']

            return EpsilonGreedyStrategy(self.num_arms, self.values, self.counts, 
                        title,
                        init_eps=init_eps,
                        decay_factor=decay_factor, 
                        reward_scaling=reward_scaling)
        elif spec == 'GT':
            time_unit = 'H'            
            
            self.num_skip = 2 #XXX: avoiding first two selection bias  

            if 'time_unit' in self.config.keys():
                time_unit = self.config['time_unit']

            return GreedyTimeStrategy(self.num_arms, self.values, self.counts, 
                        title,
                        time_unit=time_unit)

        elif spec == 'GT-LE':
            time_unit = 'H'
            reward_scaling = 'LOG_ERR'
            
            self.num_skip = 2 #XXX: avoiding first two selection bias  

            if 'time_unit' in self.config.keys():
                time_unit = self.config['time_unit']

            return GreedyTimeStrategy(self.num_arms, self.values, self.counts, 
                        title,
                        time_unit=time_unit, 
                        reward_scaling=reward_scaling)                                                     
        else:
            raise ValueError("no such strategy available: {}".format(spec))             

        
