import sys
import time
import copy
import validators as valid

from hpo.utils.logger import *

import hpo.bandit as bandit
import hpo.hp_config as hp_config

from hpo.workers.worker import Worker 
import hpo.utils.lookup as lookup
import hpo.connectors.train_emul as train_emul
from hpo.utils.grid_gen import *
from hpo.sample_space import *

class SequentialOptimizer(Worker):
    
    def __init__(self, run_config, id):
        
        super(SequentialOptimizer, self).__init__()
        self.config = run_config

        self.type = 'smbo'
        self.id = id
        
        #debug("Run configuration: {}".format(run_config))
        if 'title' in run_config:
            self.id = run_config['title']

        self.device_id = 'hpo_cpu0'
        self.machine = None
        self.samples = None

    def get_sampling_space(self):
        return self.samples
        
    def start(self):
        if self.params is None:
            error('Set configuration properly before starting.')
            return
        else:
            super(SequentialOptimizer, self).start()

    def get_cur_result(self):
        if len(self.results) == 0:
            if self.machine != None and self.machine.result != None:
                latest = self.machine.get_current_results()
                #debug("current result: {}".format(latest))
            else:
                latest = {}
        else:
            latest = self.results
        result = {"result": latest}
        return result

    def execute(self):
        try:
            self.results = self.run(self.config, self.params)

        except Exception as ex:
            warn("Exception occurs: {}".format(traceback.format_exc()))            
            self.stop_flag = True

        finally:
            with self.thread_cond:
                self.busy = False
                self.params = None
                self.thread_cond.notify()

    def stop(self):
        if self.machine != None:
            self.machine.force_stop()

        super(SequentialOptimizer, self).stop()
 
    def run(self, run_cfg, args, save_results=False):
            
        num_resume = 0
        save_pkl = False
        if 'rerun' in args:
            num_resume = args['rerun']
        if 'pkl' in args:
            save_pkl = args['pkl']

        results = []
        hp_cfg = None 
        use_surrogate = None
        
        if 'surrogate' in args:
            use_surrogate = args['surrogate']
            hp_cfg = hp_config.read_config("hp_conf/{}.json".format(use_surrogate)) # FIXME:rewrite here
        elif 'hp_cfg' in args:
            hp_cfg = args['hp_cfg']

        shared_space = None
        if 'shared_space_url' in run_cfg:
            shared_space = run_cfg['shared_space_url']

        if 'worker_url' in args and valid.url(args['worker_url']):
            trainer = args['worker_url']
            hvg = HyperparameterVectorGenerator(hp_cfg, 20000, 1)
            hpvs = hvg.generate()
            t = train_remote.init(args['worker_url'], run_config, hp_cfg, hpvs, 
                credential="jo2fulwkq") # TODO:read cridential from secure DB
            
            self.samples = GridSamplingSpace(name, hpvs, hvg.get_grid(), t)

            self.machine = bandit.create_runner(
                trainer, 
                args['exp_crt'], args['exp_goal'], args['exp_time'],
                run_cfg, hp_cfg,                            
                num_resume=num_resume,
                save_pkl=save_pkl,
                space_url=shared_space,
                use_surrogate=use_surrogate,
                id=self.id)
        else:
            l = lookup.load(use_surrogate)
            t = train_emul.init(l, run_cfg)
            self.samples = SurrogateSamplingSpace(l)
            trainer = args['surrogate']
            self.machine = bandit.create_emulator(
                trainer, 
                args['exp_crt'], args['exp_goal'], args['exp_time'],
                num_resume=num_resume,
                space_url=shared_space,
                save_pkl=save_pkl, 
                run_config=run_cfg,
                id=self.id + "_emul")

        if args['mode'] == 'DIV' or args['mode'] == 'ADA':
            results = self.machine.mix(args['spec'], args['num_trials'], 
                save_results=save_results)
        elif args['mode'] in ALL_OPT_MODELS:
            results = self.machine.all_in(args['mode'], args['spec'], args['num_trials'], 
                save_results=save_results)
        else:
            raise ValueError('unsupported mode: {}'.format(args['mode']))
  
        
        return results