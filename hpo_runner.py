from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import argparse

import validators as valid
from hpo.utils.logger import *
from hpo.eval_time import *

import hpo.bandit_config as run_config
import hpo.hp_config as hp_config
import hpo.bandit as bandit
import hpo.workers.seq_run as runner
import hpo.batch_sim as batch


ALL_OPT_MODELS = ['RANDOM', 'GP', 'GP-NM', 'RF', 'HO', 'GP-HLE', 'RF-HLE', 'HO-HLE']
ACQ_FUNCS = ['RANDOM', 'TPE', 'EI', 'PI', 'UCB']
DIV_SPECS = ['SEQ', 'RANDOM']
ALL_MIXING_SPECS = ['HEDGE', 'BO-HEDGE', 'BO-HEDGE-T', 'BO-HEDGE-LE', 'BO-HEDGE-LET', 
                    'EG', 'EG-LE', 'GT', 'GT-LE',
                    'SKO']

BATCH_SPECS = ['SYNC', 'ASYNC']
ALL_LOG_LEVELS = ['debug', 'warn', 'error', 'log']
    
LOOKUP_PATH = './lookup/'
RUN_CONF_PATH = './run_conf/'
HP_CONF_PATH = './hp_conf/'


def validate_args(args):

    surrogate = None
    valid = {}
    #debug(os.getcwd())
    hp_cfg_path = args.hp_conf
    if args.config_name.endswith('.json'):
        # config_name is a json file
        hp_cfg_path += args.config_name
    else:
        # config_name is surrogate name, check whether same csv file exists in lookup folder.
        if not check_lookup_existed(args.config_name):
            raise ValueError('Invaild arguments.')            
        surrogate = args.config_name
        hp_cfg_path += (args.config_name + ".json")
    
    hp_cfg = hp_config.read_config(hp_cfg_path)
    if hp_cfg is None:
            raise ValueError('Invaild hp_config : {}'.format(hp_cfg_path))
              
    run_cfg = run_config.read(args.conf, path=args.run_conf)
    if not run_config.validate(run_cfg):
        error("Invalid run configuration. see {}".format(args.conf))
        raise ValueError('invaild run configuration.')    
    else:
        valid['surrogate'] = surrogate
        valid['hp_cfg'] = hp_cfg
        #valid['run_cfg'] = run_cfg
        
    valid['exp_time'] = args.exp_time
#    valid['models'] = ALL_OPT_MODELS
    
#    if args.time_penalty != 'NONE':
#        valid['eval_time_model'] = 'RF'
#    else:
#        valid['eval_time_model'] = 'None'
#    valid['time_acq_funcs'] = get_time_penalties(args.time_penalty)

    for attr, value in vars(args).items():
        valid[str(attr)] = value        
        
    return run_cfg, valid


def check_lookup_existed(name):
    for csv in os.listdir(LOOKUP_PATH):
        if csv == '{}.csv'.format(name):
            return True
    return False

ALL_OPT_MODELS = ['RANDOM', 'GP', 'RF', 'HYPEROPT', 'GP-NM', 'GP-HLE', 'RF-HLE']


def execute(run_cfg, args, save_results=False):
    try:
        if run_cfg is None:
            if "run_cfg" in args:
                run_cfg = args['run_cfg']
            else:
                raise ValueError("No run configuration found.")
        
        num_resume = 0
        save_pkl = False
        if 'rerun' in args:
            num_resume = args['rerun']
        if 'pkl' in args:
            save_pkl = args['pkl']
        
        result = []
        if args['mode'].upper() != 'BATCH':
            m = None
            hp_cfg = None 
            use_surrogate = None

            trainer = None
            if valid.url(args['worker_url']):
                trainer = args['worker_url']
                if 'surrogate' in args:
                    use_surrogate = args['surrogate']
                    path = "hp_conf\{}.json".format(args['surrogate'])
                    hp_cfg = hp_config.read_config(path)
                    #debug(hp_cfg)
                elif 'hp_cfg' in args:
                    hp_cfg = args['hp_cfg']
                
                m = bandit.create_runner(trainer, 
                            args['exp_crt'], args['exp_goal'], args['exp_time'],
                            num_resume=num_resume,
                            save_pkl=save_pkl,
                            run_config=run_cfg,
                            hp_config=hp_cfg,
                            use_surrogate=use_surrogate)
            else:
                trainer = args['surrogate']
                m = bandit.create_emulator(trainer, 
                            args['exp_crt'], args['exp_goal'], args['exp_time'],
                            num_resume=num_resume,
                            save_pkl=save_pkl, 
                            run_config=run_cfg)

            if args['mode'] == 'DIV' or args['mode'] == 'ADA':
                result = m.mix(args['spec'], args['num_trials'], save_results=save_results)
            elif args['mode'] in ALL_OPT_MODELS:
                result = m.all_in(args['mode'], args['spec'], args['num_trials'], save_results=save_results)
            else:
                raise ValueError('unsupported mode: {}'.format(args['mode']))
        else:
            raise ValueError("BATCH mode is not upsupported here.")
    except:
        warn('Exception occurs on executing SMBO:{}'.format(sys.exc_info()[0]))     
    
    return result


def main():

    available_models = ALL_OPT_MODELS + ['DIV', 'ADA', 'BATCH']
    default_model = 'DIV'
    
    all_specs = ACQ_FUNCS + DIV_SPECS + ALL_MIXING_SPECS + BATCH_SPECS
    default_spec = 'SEQ'

    default_target_goal = 0.9999
    default_expired_time = 24 * 60 * 60
    
    exp_criteria = ['TIME', 'GOAL']
    default_exp_criteria = 'TIME'
    
    # XXX:disable acquistion function with time penalties
    #time_penalties_modes = ['NONE', 'ALL', 'MOST', 'LEAST', 'LINEAR', 'TOP_K', 'SEC'] + ALL_TIME_STRATEGIES
    #default_time_penalty = 'NONE'

    default_run_config = 'arms.json'
    default_log_level = 'warn'

    parser = argparse.ArgumentParser()

    # Hyperparameter optimization methods
    parser.add_argument('-m', '--mode', default=default_model, type=str,
                        help='The optimization mode. Set a model name to use a specific model only.' +\
                        'Set DIV to sequential diverification mode. Set BATCH to parallel mode. {} are available. default is {}.'.format(available_models, default_model))
    parser.add_argument('-s', '--spec', default=default_spec, type=str,
                        help='The detailed specification of the given mode. (e.g. acquisition function)' +\
                        ' {} are available. default is {}.'.format(all_specs, default_spec))
    
    # Termination criteria
    parser.add_argument('-e', '--exp_crt', default=default_exp_criteria, type=str,
                        help='Expiry criteria of the trial.\n Set "TIME" to run each trial until given exp_time expired.'+\
                        'Or Set "GOAL" to run until each trial achieves exp_goal.' +\
                        'Default setting is {}.'.format(default_exp_criteria))                        
    parser.add_argument('-eg', '--exp_goal', default=default_target_goal, type=float,
                        help='The expected target goal accuracy. ' +\
                        'When it is achieved, the trial will be terminated automatically. '+\
                        'Default setting is {}.'.format(default_target_goal))
    parser.add_argument('-et', '--exp_time', default=default_expired_time, type=str,
                        help='The time each trial expires. When the time is up, '+\
                        'it is automatically terminated. Default setting is {}.'.format(default_expired_time))
    
    # Configurations
    parser.add_argument('-c', '--conf', default=default_run_config, type=str,
                        help='Run configuration file name existed in {}.\n'.format(RUN_CONF_PATH)+\
                        'Default setting is {}'.format(default_run_config))
    parser.add_argument('-rc', '--run_conf', default=RUN_CONF_PATH, type=str,
                        help='Run configuration directory.\n'+\
                        'Default setting is {}'.format(RUN_CONF_PATH))                        
    parser.add_argument('-hc', '--hp_conf', default=HP_CONF_PATH, type=str,
                        help='Hyperparameter configuration directory.\n'+\
                        'Default setting is {}'.format(HP_CONF_PATH))
    parser.add_argument('-w', '--worker_url', default='none', type=str,
                        help='Remote training worker URL.\n'+\
                        'Set the valid URL for remote training.') 

    # Debugging option
    parser.add_argument('-l', '--log_level', default=default_log_level, type=str,
                        help='Print out log level.\n'+\
                        '{} are available. default is {}'.format(ALL_LOG_LEVELS, default_log_level))
    
    # XXX:below options are for experimental use.  
    parser.add_argument('-r', '--rerun', default=0, type=int,
                        help='[Experimental] Use to expand the number of trials for the experiment. zero means no rerun. default is {}.'.format(0))
    parser.add_argument('-p', '--pkl', default=False, type=bool,
                        help='[Experimental] Whether to save internal values into a pickle file.\n' + 
                        'CAUTION:this operation requires very large storage space! Default value is {}.'.format(False))                        
#    parser.add_argument('-tp', '--time_penalty', default=default_time_penalty, type=str,
#                        help='[Experimental] Time penalty strategies for acquistion function.\n'+\
#                        '{} are available. Default setting is {}'.format(time_penalties_modes, default_time_penalty))
 

    parser.add_argument('config_name', type=str, help='hyperparameter configuration name.')
    parser.add_argument('num_trials', type=int, help='The total repeats of the experiment.')

    args = parser.parse_args()

    set_log_level(args.log_level)

    run_cfg, args = validate_args(args)

    if args['mode'] == 'BATCH':
        if args['worker_url'] is 'none':
            c = batch.get_simulator(args['spec'].upper(), args['surrogate'],
                                args['exp_crt'], args['exp_goal'], 
                                args['exp_time'], run_cfg)
            result = c.run(args['num_trials'], save_results=True)
        else:
            raise NotImplementedError("This version only supports simulation of parallelization via surrogates.")
    else:
        results = execute(run_cfg, args, save_results=True)        
   

if __name__ == "__main__":
    main()
