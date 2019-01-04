from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ws.hpo.trainers.etr_emul import EarlyTerminateTrainer
from ws.shared.logger import *

import numpy as np
import math
from ws.hpo.choosers.util import *
from ws.shared.resp_shape import *


class GradientETRTrainer(EarlyTerminateTrainer):
    
    def __init__(self, lookup, shape_func_type=None):

        super(GradientETRTrainer, self).__init__(lookup)

        self.diff_threshold = 0.1
        self.coefficient = 1

        if shape_func_type == "hybrid_log":
            self.shaping_func = apply_hybrid_log
        elif shape_func_type == "log_err":
            self.shaping_func = apply_log_err
        else:
            self.shaping_func = apply_no_shaping
        
    def get_time_saving(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        est_time = stop_epoch * (total_time / epoch_length)
        log("Evaluation time saving by early termination: {:.1f} sec".format(total_time - est_time))
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

    def apply_no_shaping(self, errs):
        return err

    def train(self, cand_index, estimates=None, space=None):
        acc_curve = self.acc_curves.loc[cand_index].values
        self.history.append(acc_curve)

        max_epoch = len(acc_curve)
        min_train_epoch = self.get_min_train_epoch()
        
        if estimates is None:
            self.early_terminated.append(False)
            return super(GradientETRTrainer, self).train(cand_index, space=space)
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
                    self.early_terminated.append(True)
                    return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1)
            
            self.early_terminated.append(False)
            return 1.0 - max(acc_curve), self.total_times[cand_index]    


