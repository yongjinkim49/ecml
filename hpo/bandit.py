from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import os.path
import time
import traceback
import pickle
import gzip

import numpy as np

from hpo.sample_space import *
from hpo.result import HPOResultFactory

import hpo.utils.lookup as lookup
import hpo.eval_time as eval_time
from hpo.utils.grid_gen import *

from hpo.utils.saver import ResultSaver, TempSaver
from hpo.utils.measurer import RankIntersectionMeasure
from hpo.utils.logger import *
from hpo.utils.converter import TimestringConverter

from hpo.bandit_config import BanditConfigurator
import hpo.hp_config as hp_cfg

import hpo.connectors.train_remote as train_remote
import hpo.connectors.train_emul as train_emul

NUM_MAX_ITERATIONS = 10000


def create_surrogate_space(surrogate, run_config):
    grid_order = None 
    if 'grid' in run_config and 'order' in run_config['grid']:
        grid_order = run_config['grid']['order']    
    l = lookup.load(surrogate, grid_order=grid_order)
    s = SurrogateSamplingSpace(l)
    debug("Surrogate sampling space created: {}".format(surrogate))
    return s


def connect_remote_space(space_url):
    name = "remote_grid_sample-{}".format(space_url)
    s = get_remote_samples(name, space_url)
    return s    


def create_grid_space(cfg, num_samples=20000, grid_seed=1):
    if hasattr(cfg, 'config'):
        if hasattr(cfg.config, 'num_samples'):
            num_samples = cfg.config.num_samples

        if hasattr(cfg.config, 'grid_seed'):
            grid_seed = cfg.config.grid_seed
    name = "grid_sample-{}".format(time.strftime('%Y%m%dT-%H:%M:%SZ',time.gmtime()))
    hvg = HyperparameterVectorGenerator(cfg, num_samples, grid_seed)
    s = GridSamplingSpace(name, hvg.get_grid(), hvg.get_hpv(), cfg)
    debug("Grid sampling space created: {}".format(name))
    return s


def create_emulator(space,
                    run_mode, target_acc, time_expired, 
                    run_config=None,
                    save_pkl=False,
                    num_resume=0,
                    id="HPO_emulator"
                    ):

    trainer = train_emul.init(space, run_config)
    machine = HPOBanditMachine(
        space, trainer, 
        run_mode, target_acc, time_expired, run_config, 
        num_resume=num_resume, 
        with_pkl=save_pkl,
        min_train_epoch=t.get_min_train_epoch(),
        id=id)
    
    return machine


def create_runner(trainer_url, space, 
                  run_mode, target_acc, time_expired, 
                  run_config, hp_config,
                  save_pkl=False,
                  num_samples=20000,
                  grid_seed=1,
                  num_resume=0,
                  use_surrogate=None,
                  id="HPO_runner"
                  ):
    
    # FIXME:test auth key. It should be deleted before release.
    kwargs = { "credential" : "jo2fulwkq" }  
    
    try:
        if use_surrogate != None:            
            kwargs["surrogate"] = use_surrogate
            id += " with surrogate-{}".format(use_surrogate)
        
        if isinstance(hp_config, dict):
            cfg = hp_cfg.HyperparameterConfiguration(hp_config)
        else:
            cfg = hp_config

        hpvs = space.get_hpv()
        trainer = train_remote.init(trainer_url, run_config, cfg, hpvs, **kwargs)
        
        machine = HPOBanditMachine(
            space, trainer, run_mode, target_acc, time_expired, run_config,
            num_resume=num_resume, 
            with_pkl=save_pkl, 
            id=id)
        
        return machine

    except Exception as ex:
        warn("runner creation failed: {}".format(ex))


class HPOBanditMachine(object):
    ''' k-armed bandit machine of hyper-parameter optimization.'''
    def __init__(self, samples, trainer, 
                 run_mode, target_acc, time_expired, run_config,
                 num_resume=0, 
                 with_pkl=False, 
                 calc_measure=False,
                 min_train_epoch=10,
                 id="HPO"):

        self.id = id

        self.samples = samples
        self.trainer = trainer
        self.save_name = samples.get_name()

        self.calc_measure = calc_measure
        
        self.target_accuracy = target_acc
        self.time_expired = TimestringConverter().convert(time_expired)
        self.eval_time_model = None

        self.run_mode = run_mode  # can be 'GOAL' or 'TIME'

        self.with_pkl = with_pkl
        self.est_records = {}  # for in-depth estimation performance analysis
        self.temp_saver = None
        self.num_resume = num_resume

        self.stop_flag = False

        self.result = None
        self.results = None

        self.run_config = run_config
        self.min_train_epoch = min_train_epoch
        if self.run_config:
            if "min_train_epoch" in self.run_config:
                self.min_train_epoch = self.run_config["min_train_epoch"]

        self.print_exception_trace = False

        self.saver = ResultSaver(self.save_name, self.run_mode, self.target_accuracy,
                                 self.time_expired, self.run_config, postfix=".{}".format(self.id))

    def init_bandit(self, config=None):
        if config is None:
            config = self.run_config
        self.bandit = BanditConfigurator(self.samples, config)
        self.samples.reset()
        self.trainer.reset()

    def force_stop(self):
        self.stop_flag = True
    
    def estimate_eval_time(self, cand_index, model):
        ''' Experimental function. - more evaluation will be required for future use. '''        
        
        samples = self.samples
        cand_est_times = None

        if self.eval_time_model and self.eval_time_model != "None":
            et = eval_time.get_estimator(samples, self.eval_time_model)
            
            if et is not None:
                
                success, cand_est_times = et.estimate(samples.get_candidates(), 
                                                    samples.get_completes())
                if success:
                    chooser = self.bandit.choosers[model]
                    chooser.set_eval_time_penalty(cand_est_times)

                if cand_est_times is not None:
                    for i in range(len(samples.get_candidates())):
                        if samples.get_candidates(i) == cand_index:
                            return int(cand_est_times[i])
        
        return None

    def select_candidate(self, model, acq_func, samples=None):
        if samples is None:
            samples = self.samples

        metrics = []
        chooser = self.bandit.choosers[model]
        start_time = time.time()
        exception_raised = False
        next_index = chooser.next(samples, acq_func)

        # for measure information sharing effect
        if self.calc_measure:
            mr = RankIntersectionMeasure(samples.get_test_error())
            if chooser.estimates:
                metrics = mr.compare_all(chooser.estimates['candidates'],
                                                chooser.estimates['acq_funcs'])

        opt_time = time.time() - start_time
        
        return next_index, opt_time, metrics

    def evaluate(self, cand_index, model, samples=None):
        if samples is None:
            samples = self.samples

        chooser = self.bandit.choosers[model]

        # set initial error for avoiding duplicate
        interim_err = self.trainer.get_interim_error(cand_index, 0)
        self.samples.update(cand_index, interim_err)

        test_error, exec_time = self.trainer.train(samples, cand_index, chooser.estimates)
        #debug("index: {}, error: {}, time: {}".format(cand_index, test_error, exec_time))
        return test_error, exec_time

    def pull(self, model, acq_func, repo, select_opt_time=0):

        exception_raised = False
        try:
            next_index, opt_time, metrics = self.select_candidate(
                model, acq_func)
        
        except KeyboardInterrupt:
            self.stop_flag = True
            return 0.0, None
        except:
            warn("Exception occurred in the estimation processing. " +
                 "To avoid stopping, it selects the candidate randomly.")
            model = 'RANDOM'
            acq_func = 'RANDOM'
            next_index, opt_time, metrics = self.select_candidate(
                model, acq_func)
            exception_raised = True

        # estimate an evaluation time of the next candidate
        #est_eval_time = self.estimate_eval_time(next_index, model)
        # evaluate the candidate
        test_error, exec_time = self.evaluate(next_index, model)
        total_opt_time = select_opt_time + opt_time
        repo.append(next_index, test_error,
                    total_opt_time, exec_time, metrics)
        self.samples.update(next_index, test_error)
        
        curr_acc = 1.0 - test_error
        est_log = {
            'exception_raised': exception_raised,
            "estimated_values": self.bandit.choosers[model].estimates
        }
        return curr_acc, est_log

    def all_in(self, model, acq_func, num_trials, save_results=True):
        ''' executing a specific arm in an exploitative manner '''
        self.temp_saver = TempSaver(self.samples.get_name(),
                                    model, acq_func, num_trials, self.run_config)

        if self.num_resume > 0:
            self.results, start_idx = self.saver.load(
                model, acq_func, self.num_resume)
        else:
            self.results, start_idx = self.temp_saver.restore()

        self.est_records = {}
        for i in range(start_idx, num_trials):
            trial_start_time = time.time()
            self.init_bandit()
            self.result = HPOResultFactory()
            best_acc = 0.0
            self.est_records[str(i)] = []
            for j in range(NUM_MAX_ITERATIONS):

                curr_acc, opt_log = self.pull(model, acq_func, self.result)
                if self.stop_flag == True:
                    return self.results

                self.est_records[str(i)].append(opt_log)

                if best_acc < curr_acc:
                    best_acc = curr_acc
                if self.run_mode == 'GOAL':
                    if best_acc >= self.target_accuracy:
                        break
                elif self.run_mode == 'TIME':
                    duration = self.result.get_elapsed_time()
                    #debug("current time: {} - {}".format(duration, self.time_expired))
                    if duration >= self.time_expired:
                        break

            trial_sim_time = time.time() - trial_start_time
            log("{} found best accuracy {:.2f}% at run #{}. ({:.1f} sec)".format(
                self.id, best_acc * 100, i, trial_sim_time))
            
            if best_acc < self.target_accuracy:
                self.result.force_terminated()

            self.results[i] = self.result.get_current_status()
            self.temp_saver.save(self.results)

        if save_results is True:
            
            est_records = None
            if self.with_pkl is True:
                est_records = self.est_records
            self.saver.save(model, acq_func,
                            num_trials, self.results, est_records)

        self.temp_saver.remove()

        self.show_best_hyperparams()

        return self.results

    def mix(self, strategy, num_trials, save_results=True):
        ''' executing the bandit with many arms by given mixing strategy '''
        model = 'DIV'
        self.temp_saver = TempSaver(self.samples.get_name(),
                                    model, strategy, num_trials, self.run_config)

        if self.num_resume > 0:
            self.results, start_idx = self.saver.load(
                model, strategy, self.num_resume)
        else:
            self.results, start_idx = self.temp_saver.restore()

        self.est_records = {}
        for i in range(start_idx, num_trials):
            
            trial_start_time = time.time()
            self.init_bandit()
            arm = self.bandit.get_arm(strategy)
            self.result = HPOResultFactory()
            best_acc = 0.0

            self.est_records[str(i)] = []

            for j in range(NUM_MAX_ITERATIONS):

                start_time = time.time()
                model, acq_func, _ = arm.select(j)
                select_opt_time = time.time() - start_time

                curr_acc, opt_log = self.pull(model, acq_func, self.result, select_opt_time)
                if self.stop_flag == True:
                    return self.results
                
                if opt_log['exception_raised']:
                    model = 'RANDOM'
                    acq_func = 'RANDOM'

                self.result.update_trace(model, acq_func)
                arm.update(j, curr_acc, opt_log)

                self.est_records[str(i)].append(opt_log)

                if best_acc < curr_acc:
                    best_acc = curr_acc

                if self.run_mode == 'GOAL':
                    if best_acc >= self.target_accuracy:
                        break
                elif self.run_mode == 'TIME':
                    duration = self.result.get_elapsed_time()
                    #debug("current time: {} - {}".format(duration, self.time_expired))
                    if duration >= self.time_expired:
                        break

            trial_sim_time = time.time() - trial_start_time
            log("{} found best accuracy {:.2f}% at run #{}. ({:.1f} sec)".format(
                self.id, best_acc * 100, i, trial_sim_time))
            if best_acc < self.target_accuracy:
                self.result.force_terminated()

            self.result.feed_arm_selection(arm)
            self.results[i] = self.result.get_current_status()

            self.temp_saver.save(self.results)

        if save_results is True:
            est_records = None
            if self.with_pkl is True:
                est_records = self.est_records
            self.saver.save('DIV', strategy,
                            num_trials, self.results, est_records)

            self.temp_saver.remove()
        
        self.show_best_hyperparams()

        return self.results

    def get_current_results(self):
        results = []
        if self.results:
            results += self.results

        if self.result != None:
            results.append(self.result.get_current_status())

        return results

    def show_best_hyperparams(self):
        for k in self.results.keys():
            result = self.results[k]
            
            acc_max_index = np.argmax(result['accuracy'])
            max_model_index = result['model_idx'][acc_max_index]
            #debug(max_model_index)
            max_hpv = self.samples.get_hpv(max_model_index)
            log("Achieved {:.4f} at run #{} by\n{}".format(result['accuracy'][acc_max_index], k, max_hpv))
            #accs = [ round(acc, 4) for acc in result['accuracy'] ]
            #log("selected accuracies: {}".format(accs))        

   
