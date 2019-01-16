from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import math

from ws.hpo.trainers.emul.trainer import EarlyTerminateTrainer
from ws.shared.logger import *


class VizMedianETRTrainer(EarlyTerminateTrainer): #

    def __init__(self, lookup):
        
        super(VizMedianETRTrainer, self).__init__(lookup)

        self.epoch_length = lookup.num_epochs        
        self.eval_epoch = int(self.epoch_length/3)
        self.percentile = 50 # median

    def get_time_saving(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        est_time = stop_epoch * (total_time / epoch_length)
        log("Evaluation time saving: {:.1f}s".format(total_time - est_time))
        return est_time

    def train(self, cand_index, estimates, min_train_epoch=None, space=None):
        acc = 0 # stopping accuracy
        min_epoch = 0
        cur_max_acc = 0
        debug("cand_index:{}".format(cand_index))
        acc_curve = self.acc_curves.loc[cand_index].values
        self.history.append(acc_curve)

        history = []   

        for i in range(len(self.history)):
            history.append(np.mean(self.history[i][:self.eval_epoch]))

        threshold = np.percentile(history, self.percentile)

        debug("commencing iteration {}".format(len(self.history)))
        debug("accuracy curve: {}".format(acc_curve))

        for i in range(min_epoch, self.epoch_length-1):
            acc = acc_curve[i]
            if acc > cur_max_acc:
                cur_max_acc = acc
            
            debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))

            if i+1 == self.eval_epoch:
                if acc < threshold:
                    debug("terminated at epoch{}".format(i+1))
                    self.early_terminated_history.append(True)
                    return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1), True

        self.early_terminated_history.append(False)
        return 1.0 - max(acc_curve), self.total_times[cand_index], False


class VizPentaETRTrainer(EarlyTerminateTrainer):
    
    def __init__(self, lookup, percentile=80, eval_start=0.5, eval_end=0.67):
        
        super(VizPentaETRTrainer, self).__init__(lookup)

        self.epoch_length = lookup.num_epochs
        self.lcs = self.history
        self.eval_epoch_start = int(self.epoch_length * eval_start)
        self.eval_epoch_end = int(self.epoch_length * eval_end)
        self.percentile = percentile

    def get_time_saving(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        est_time = stop_epoch * (total_time / epoch_length)
        log("Evaluation time saving: {:.1f}s".format(total_time - est_time))
        return est_time

    def train(self, cand_index, estimates, min_train_epoch=None, space=None):
        acc = 0 # stopping accuracy
        min_epoch = 0
        cur_max_acc = 0
        debug("cand_index:{}".format(cand_index))

        acc_curve = self.acc_curves.loc[cand_index].values
        train_time = self.total_times[cand_index]
        min_loss = 1.0 - max(acc_curve)
        lc = {"curve": acc_curve, "train_time":train_time}
        self.lcs.append(lc)

        history = []   
        early_terminated = False
        for i in range(len(self.lcs)):
            history.append(np.mean(self.lcs[i]["curve"][self.eval_epoch_start:self.eval_epoch_end+1]))

        threshold = np.percentile(history, self.percentile)

        debug("commencing iteration {}".format(len(self.lcs)))
        debug("accuracy curve: {}".format(acc_curve))

        for i in range(min_epoch, self.epoch_length-1):
            acc = acc_curve[i]
            if acc > cur_max_acc:
                cur_max_acc = acc
            
            debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))
            cum_train_time = sum([lc["train_time"] for lc in self.lcs])

            if i+1 == self.eval_epoch_end:
                if acc < threshold:
                    debug("terminated at epoch{}".format(i+1))
                    self.early_terminated_history.append(True)
                    min_loss = 1.0 - cur_max_acc
                    train_time = self.get_time_saving(cand_index, i+1)
                    early_terminated = True
                    break

        return min_loss, train_time, early_terminated