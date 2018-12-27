from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import math

from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures

from commons.proto import TrainerPrototype
from commons.logger import *

def init(space, run_config):
    try:
        if not hasattr(space, 'lookup'):
            raise ValueError("Invalid surrogate space")
        lookup = space.lookup
        
        if run_config and "auto_early_stop" in run_config:
            log_func = None
            if "log" in run_config and run_config["log"]["log_err"]:
                if "log_err_func" in run_config["log"]:
                    log_func_type = run_config["log"]["log_err_func"]
                    return LogErrorGradientEarlyStopTrainer(lookup, log_func_type)
            return GradientEarlyStopTrainer(lookup)
        return NoEarlyStopTrainer(lookup)

    except Exception as ex:
        warn("early stop trainer creation failed: {}".format(ex))
        return NoEarlyStopTrainer(lookup)


class TrainEmulator(TrainerPrototype):
    def __init__(self, lookup):
    
        self.lookup = lookup
        self.acc_curves = lookup.get_accuracies_per_epoch()
        self.total_times = lookup.get_elapsed_times()
        self.data_type = lookup.data_type

    def reset(self):
        pass

    def get_min_train_epoch(self):
        if self.lookup.data_type == "data200":
            return 30
        elif self.lookup.data_type == "data20" or self.lookup.data_type == "data30":
            return 15
        else:
            return 4  

    def train(self, space, cand_index, estimates=None):
        acc_curve = self.acc_curves.loc[cand_index].values
        total_time = self.total_times[cand_index]
        return 1.0 - max(acc_curve), total_time         

    def get_interim_error(self, model_index, cur_dur):
        total_dur = self.total_times[model_index]
        cur_epoch = int(cur_dur / total_dur * self.lookup.num_epochs)
        error = 0.9 # random initial performance for 10 classification problem
        if cur_epoch == 0:
            
            if self.data_type == 'data30':
                error = 0.99 # for CIFAR-100
            elif self.data_type == 'data10':
                error = 0.7 # for PTB
        else:
            pre_errors = self.lookup.get_test_errors(cur_epoch)
            error = pre_errors[model_index]
        #debug("training model #{} at {:.1f} may return loss {:.4f}.".format(model_index, cur_dur, error))
        return error


class NoEarlyStopTrainer(TrainEmulator):
    def __init__(self, lookup):
        super(NoEarlyStopTrainer, self).__init__(lookup)


class EarlyStopTrainer(NoEarlyStopTrainer):

    def __init__(self, lookup):

        super(EarlyStopTrainer, self).__init__(lookup)

        self.history = []
        self.early_stopped = []

    def reset(self):
        # reset history
        self.history = []
        self.early_stopped = []


class GradientEarlyStopTrainer(EarlyStopTrainer):
    
    def __init__(self, lookup, shaping_func=None):

        super(GradientEarlyStopTrainer, self).__init__(lookup)

        self.diff_threshold = 0.1
        self.coefficient = 1
        if shaping_func:
            self.shaping_func = shaping_func
        else:
            self.shaping_func = self.no_shaping
        
    def early_stop_time(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        est_time = stop_epoch * (total_time / epoch_length)
        log("Evaluation time saving by early stopping: {:.1f} sec".format(total_time - est_time))
        return est_time

    def get_gradient_average(self, cand_index, num_step):
        # averaging gradients of learning curves
        acc_curve = self.acc_curves.loc[cand_index].values
        acc_delta = []
        num_grads = len(acc_curve[:num_step]) - 1
        for j in range(num_grads):
            delta = acc_curve[j+1] - acc_curve[j]
            acc_delta.append(delta)
        avg_deltas =  sum(acc_delta) / num_grads
        #debug("delta average: {:.5f}, delta list: {}".format(avg_deltas, [round(d, 5) for d in acc_delta]))         
        return avg_deltas      

    def no_shaping(self, means):
        return means

    def train(self, space, cand_index, estimates=None):
        acc_curve = self.acc_curves.loc[cand_index].values
        self.history.append(acc_curve)

        max_epoch = len(acc_curve)
        min_train_epoch = self.get_min_train_epoch()
        
        if estimates is None:
            self.early_stopped.append(False)
            return super(GradientEarlyStopTrainer, self).train(space, cand_index)
        else:
            candidates = estimates['candidates']
            acq_funcs = estimates['acq_funcs']
            means = estimates['means']
            vars = estimates['vars']        
        
            i_max = np.argmax(acq_funcs)
            v_max = acq_funcs[i_max]
            #print("max {} ({})".format(v_max, i_max))
            m = means[i_max]
            s = math.sqrt(vars[i_max])
        
            est_acc_mean = 1 - self.shaping_func(m)
            #debug("estimated mean: {:.4f}, stdev: {:.4f}".format(est_acc_mean, s))        
            acc_delta = 0
            cur_max_acc = 0
            
            #debug("accuracy curve: {}".format([ round(acc, 5) for acc in acc_curve]))

            for i in range(min_train_epoch, max_epoch):
                acc = acc_curve[i]
                obs_n = i - 1
                if acc > cur_max_acc:
                    cur_max_acc = acc

                reduced_s = (s - s / max_epoch * i)
                lower_bound = est_acc_mean # - self.coefficient * reduced_s
                # dynamic stdev decrease
                
                min_delta = (est_acc_mean - acc) / (max_epoch - i)
                #debug("current accuracy: {:.4f}, lower bound: {:.4f}".format(acc, lower_bound))
                #debug("est. mean acc: {:.4f}, min delta: {:.4f}".format(est_acc_mean - acc, min_delta))
                if acc < lower_bound and \
                    min_delta > self.get_gradient_average(cand_index, i):

                    diff = max(acc_curve) - acc                
                    debug("Early stopping at {} epochs. (accuracy difference {:.3f})".format(i + 1, diff))
                    
                    if diff > self.diff_threshold:
                        warn("Large difference: true {:.4f}, current max {:.4f}".format(max(acc_curve), cur_max_acc))
                    
                    # stop early
                    self.early_stopped.append(True)
                    return 1.0 - cur_max_acc, self.early_stop_time(cand_index, i+1)
            
            self.early_stopped.append(False)
            return 1.0 - max(acc_curve), self.total_times[cand_index]    


class LogErrorGradientEarlyStopTrainer(GradientEarlyStopTrainer):

    def __init__(self, lookup, log_func_type):
        if log_func_type == "ada_log_3":
            log_func = self.transform_hybrid_log
            super(LogErrorGradientEarlyStopTrainer, self).__init__(lookup, log_func)
        else:
            raise NotImplementedError()

    def transform_hybrid_log(self, err, threshold=0.3):
        if err > threshold:
            return err
        else:
            moved = err - (threshold - math.log10(threshold))
            unscaled = 10**(moved)
            return unscaled


class EarlyStopTrainerBoilerplate(EarlyStopTrainer):
    ''' Sample code for your ETR logic. 
        You will implement the following methods:   
    
    '''
    
    def __init__(self, lookup, **kwargs):
        # TODO: you can add more attributes here (if required)       
        super(EarlyStopTrainerBoilerplate, self).__init__(lookup)

    def train(self, space, cand_index, 
            estimates=None):
        # Firstly, you should add current candidate index to 
        
        # You can access the accuracy curve as below
        acc_curve = self.acc_curves.loc[cand_index].values

        # You can also access a previous accuracy curve as follows:
        for acc_curve in self.history:
            print(acc_curve) 

        # TODO: Your algorithm here
        early_stopped = True # if your algorithm fires, append the result as below:
        if early_stopped:
            self.early_stopped.append(True)
            stopped_error = 0.1
            eval_time = 100

            # TODO: you should return the error when it stopped and time to execute here.
            return stopped_error, eval_time
        else:
            self.early_stopped.append(False)

            return 1.0 - max(acc_curve), self.total_times[cand_index] 

