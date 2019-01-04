from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import math

from ws.hpo.trainers.etr_emul import EarlyTerminateTrainer
from ws.shared.logger import *


class IntervalETRTrainer(EarlyTerminateTrainer):

    def __init__(self, lookup):
        
        super(IntervalETRTrainer, self).__init__(lookup)

        self.epoch_length = lookup.num_epochs
        self.acc_min = 0.0
        self.acc_max = 0.2
        self.lcs = self.history


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

        acc_curve = self.acc_curves.loc[cand_index].values
        self.lcs.append(acc_curve)

        debug('             ')
        debug('             ')
        debug("commencing iteration {}".format(len(self.lcs)))
        debug("accuracy curve: {}".format(acc_curve))

        for i in range(min_epoch, self.epoch_length-1):
            acc = acc_curve[i]
            if acc > cur_max_acc:
                cur_max_acc = acc

            debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))                
            if self.acc_min < acc < self.acc_max:
                debug("stop at epoch{} if acc is ({},{})".format(i+1, self.acc_min, self.acc_max))
                self.early_terminated.append(True)
                return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1)
    
        return 1.0 - max(acc_curve), self.total_times[cand_index]