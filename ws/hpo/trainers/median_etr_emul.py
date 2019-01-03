from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import math

from ws.hpo.trainers.etr_emul import EarlyStopTrainer
from ws.shared.logger import *


class VizMedianETRTrainer(EarlyStopTrainer): #

    def __init__(self, lookup):
        
        super(VizMedianETRTrainer, self).__init__(lookup)

        self.epoch_length = lookup.num_epochs
        self.lcs = self.history
        self.eval_epoch = int(self.epoch_length/3)
        self.percentile = 50 # median

    def early_stop_time(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        est_time = stop_epoch * (total_time / epoch_length)
        log("evaluation time saving: {:.1f}".format(total_time - est_time))
        return est_time

    def train(self, cand_index, estimates, min_train_epoch=None):
        acc = 0 # stopping accuracy
        min_epoch = 0
        cur_max_acc = 0

        acc_curve = self.acc_curves.loc[cand_index].values
        self.lcs.append(acc_curve)

        history = []   

        for i in range(len(self.lcs)):
            history.append(np.mean(self.lcs[i][:self.eval_epoch]))

        threshold = np.percentile(history, self.percentile)
        
        debug('             ')
        debug('             ')
        debug("commencing iteration {}".format(len(self.lcs)))
        debug("accuracy curve: {}".format(acc_curve))


        for i in range(min_epoch, self.epoch_length-1):
            acc = acc_curve[i]
            if acc > cur_max_acc:
                cur_max_acc = acc
            
            debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))

            if i+1 == self.eval_epoch:
                if acc < threshold:
                    debug("terminated at epoch{}".format(i+1))
                    self.early_stopped.append(True)
                    return 1.0 - cur_max_acc, self.early_stop_time(cand_index, i+1)

        self.early_stopped.append(False)
        return 1.0 - max(acc_curve), self.total_times[cand_index]