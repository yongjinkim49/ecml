from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

import argparse
from hpo.interface import *
from hpo.workers.parallel_opt import *
import hpo.bandit_config as bandit_config

RUN_CONF_PATH = './run_conf/'
ALL_LOG_LEVELS = ['debug', 'warn', 'error', 'log']


def main():

    try:
        default_run_config = 'arms.json'
        default_log_level = 'warn'
        default_port = 5000    
        parser = argparse.ArgumentParser()
        
        # Configurations
        parser.add_argument('-c', '--conf', default=default_run_config, type=str,
                            help='Run configuration file name existed in {}.\n'.format(RUN_CONF_PATH)+\
                            'Default setting is {}'.format(default_run_config))
        parser.add_argument('-rc', '--run_conf', default=RUN_CONF_PATH, type=str,
                            help='Run configuration directory.\n'+\
                            'Default setting is {}'.format(RUN_CONF_PATH))     
        parser.add_argument('-p', '--port', default=default_port, type=int,
                            help='Port number for daemon. default is {}.'.format(default_port))

        # Debugging option
        parser.add_argument('-l', '--log_level', default=default_log_level, type=str,
                            help='Print out log level.\n'+\
                            '{} are available. default is {}'.format(ALL_LOG_LEVELS, default_log_level))

        args = parser.parse_args()
        set_log_level(args.log_level)
        
        enable_debug = False
        if args.log_level == 'debug':
            enable_debug = True

        run_cfg = bandit_config.read(args.conf, path=args.run_conf)
        if not bandit_config.validate(run_cfg):
            error("Invalid run configuration. see {}".format(args.conf))
            raise ValueError('invaild run configuration.')    

        debug("HPO daemon will be ready to serve in port {}.\n".format(args.port))
        wait_seq_opt_request(run_cfg, enable_debug=enable_debug, port=args.port)
    
    except KeyboardInterrupt as ki:
        warn("Terminated by Ctrl-C.")
        sys.exit(-1) 

    except Exception as ex:
        error("Exception ocurred: {}".format(ex))


if __name__ == "__main__":
    main()