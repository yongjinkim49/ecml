import json
import time
import sys
import copy

import numpy as np
import math

from ws.shared.logger import *
from ws.hpo.trainers.remote.trainer import EarlyTerminateTrainer


class MultiThresholdingETRTrainer(EarlyTerminateTrainer):
    
    def __init__(self, controller, hpvs, survive_ratio):
        
        if survive_ratio < 0.0 or survive_ratio > 0.5:
            raise ValueError("Invalid survive_ratio: {}".format(survive_ratio))

        super(MultiThresholdingETRTrainer, self).__init__(controller, hpvs)
        self.survive_ratio = survive_ratio
        self.drop_percentile = 100.0 - (survive_ratio * 100.0)
        self.survive_percentile = (survive_ratio * 100.0)
        self.num_epochs = self.max_train_epoch
                
    def get_eval_indices(self, eval_start_ratio, eval_end_ratio):
        start_index = int(self.num_epochs * eval_start_ratio)
        if start_index > 0:
            start_index -= 1
        
        eval_start_index = start_index
        eval_end_index = int(self.num_epochs * eval_end_ratio) - 1
        return eval_start_index, eval_end_index

    def get_acc_threshold(self, cur_acc_curve, eval_start_index, eval_end_index, percentile):
        mean_accs = []   
        if len(cur_acc_curve) > 0:
            cur_mean_acc = np.mean(cur_acc_curve)
            if np.isnan(cur_mean_acc) == False:
                mean_accs.append(cur_mean_acc)

        for i in range(len(self.history)):
            acc_curve_span = []
            prev_curve = self.history[i]["curve"]
            
            if len(prev_curve) > eval_start_index:
                acc_curve_span = prev_curve[eval_start_index:]
            if len(prev_curve) > eval_end_index+1:
                acc_curve_span = prev_curve[eval_start_index:eval_end_index+1]
            
            if len(acc_curve_span) > 0:
                mean_acc = np.mean(acc_curve_span)
                if np.isnan(mean_acc) == False:
                    mean_accs.append(mean_acc)
        
        debug("# of history :{}, mean accs:{}".format(len(self.history), ["{:.4f}".format(acc) for acc in mean_accs]))
        
        if len(mean_accs) > 0:
            threshold = np.percentile(mean_accs, percentile)
        else:
            threshold = 0.0
        
        return threshold

    def check_termination_condition(self, acc_curve, estimates):
        cur_epoch = len(acc_curve)
        
        early_drop_epoch = int(self.num_epochs * 0.5)
        survive_check_epoch = int(self.num_epochs * (1.0 - self.survive_ratio))

        debug("Current epoch: {}, checkpoints: {}".format(cur_epoch, [early_drop_epoch, survive_check_epoch]))
        
        if cur_epoch >= early_drop_epoch and cur_epoch < survive_check_epoch:
            # evaluate early termination criteria
            start_index, end_index = self.get_eval_indices(0.0, 0.5)
            cur_acc = acc_curve[end_index]
            debug("Checking early termination: {}".format(["{:.4f}".format(acc) for acc in acc_curve[:end_index+1]]))
            acc_thres = self.get_acc_threshold(acc_curve[:end_index+1], start_index, end_index, self.drop_percentile)
            if cur_acc < acc_thres:
                debug("Early dropped by {} vs. {}".format(cur_acc, acc_thres))
                return True
        elif cur_epoch >= survive_check_epoch:
            # evaluate late survival criteria
            eval_end_ratio = 1.0 - self.survive_ratio
            start_index, end_index = self.get_eval_indices(0.5, eval_end_ratio)
            cur_acc = acc_curve[end_index]
            debug("Checking late termination: {}".format(["{:.4f}".format(acc) for acc in acc_curve[start_index:end_index+1]]))
            acc_thres = self.get_acc_threshold(acc_curve[start_index:end_index+1], start_index, end_index, self.survive_percentile)
            if cur_acc < acc_thres:
                debug("Late dropped by {} vs. {}".format(cur_acc, acc_thres))
                return True
                
        elif cur_epoch >= self.max_train_epoch:
            warn("Invalid scenario: current epochs exceeds max epochs")
            return True
        
        return False
