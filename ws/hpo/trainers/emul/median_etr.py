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
            
            #debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))

            if i+1 == self.eval_epoch:
                if acc < threshold:
                    debug("terminated at epoch{}".format(i+1))
                    self.early_terminated_history.append(True)
                    return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1), True

        self.early_terminated_history.append(False)
        return 1.0 - max(acc_curve), self.total_times[cand_index], False


