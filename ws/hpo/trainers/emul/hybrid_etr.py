from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from itertools import compress

import numpy as np

from ws.hpo.trainers.emul.trainer import EarlyTerminateTrainer
from ws.shared.logger import *


class IntervalKnockETRTrainer(EarlyTerminateTrainer): # 

    def __init__(self, lookup):

        super(IntervalKnockETRTrainer, self).__init__(lookup)
        
        self.epoch_length = lookup.num_epochs
        
        self.eval_epoch = int(self.epoch_length/4)
        self.satisfy_epochs = int(self.epoch_length/self.eval_epoch*3)
        self.percentile = 75 # percentile X 100
        self.acc_min = 0.0
        self.acc_max = 0.2


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
        knocked_in_count = 0
        min_epoch = 0
        cur_max_acc = 0
        knock_out_barrier = 0

        acc_curve = self.acc_curves.loc[cand_index].values
        self.history.append(acc_curve)

        history = []
        knock_temp_storage = []
        knock_in_barriers = [0] * self.eval_epoch #7
        unstopped_list = list(compress(self.history, self.early_terminated))
        knock_out_candidates = []       


        for i in range(self.eval_epoch): #7
            history.append([])
            for n in range(len(self.history)): # number of iterations
                history[i].append(self.history[n][i]) # vertical congregation of curve values     
            knock_in_barriers[i] = np.percentile(history[i], self.percentile) # 75% value of the vertical row
        
        for i in range(len(unstopped_list)): # number of iterations fully trained without ETR activated
            knock_temp_storage.append([1])
            for n in range(self.eval_epoch, self.epoch_length-1): # epoch 8 ~ 15
                knock_temp_storage[i].append(unstopped_list[i][n]) 
            knock_out_candidates.append(min(knock_temp_storage[i]))


        if len(knock_out_candidates) >= 1:
            if len(self.history) > int(round(1/(1-self.percentile/100))):

                knock_out_point = min(knock_out_candidates)
                knock_out_adjusted_margin = max(0,(0.05 - 0.001 * (len(self.history)-int(round(1/(1-self.percentile/100))))))
                knock_out_barrier = knock_out_point - knock_out_adjusted_margin
            else:
                knock_out_barrier = np.max(knock_out_candidates)
        else: 
            knock_out_barrier = knock_in_barriers[self.eval_epoch-1]
        
        debug('             ')
        debug('             ')
        debug("commencing iteration {}".format(len(self.history)))
        debug("accuracy curve: {}".format(acc_curve))


        for i in range(min_epoch, self.epoch_length-1):
            acc = acc_curve[i]
            if acc > cur_max_acc:
                cur_max_acc = acc
            
            debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))

            if len(self.history) > int(round(1/(1-self.percentile/100))): # fully train a few trials for intial parameter setting
                if i >= 1:
                    if self.acc_min < acc < self.acc_max:
                        debug("stopped at epoch{} locked between ({},{})".format(i+1, self.acc_min, self.acc_max))
                        self.early_terminated.append(True)
                        return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1)
                if i <= self.eval_epoch-1:
                    if acc > knock_in_barriers[i]:
                        debug("acc knocked into above {} at epoch{}".format(knock_in_barriers[i],i+1))
                        knocked_in_count += 1

                if i == self.eval_epoch-1:
                    if knocked_in_count <= self.satisfy_epochs:
                        debug("terminated at epoch{} with {} less knock_ins".format(i+1, self.satisfy_epochs - knocked_in_count))
                        # stop early
                        self.early_terminated.append(True)
                        return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1)

                if self.epoch_length-1 > i > self.eval_epoch-1:
                    if knocked_in_count > self.satisfy_epochs:
                        if acc < knock_out_barrier:
                            #stop early
                            self.early_terminated.append(True)
                            debug("terminated at epoch{} by knocking out below {}".format(i+1, knock_out_barrier))
                            return 1.0 - cur_max_acc, self.get_time_saving(cand_index, i+1)

        return 1.0 - max(acc_curve), self.total_times[cand_index]


### 2 controllable dimensions:
    # 1) eval_p: 3, 4, or 5
    # 2) percentile: 0 ~ 100
class IntervalMultiKnockETRTrainer(EarlyTerminateTrainer): 

    def __init__(self, lookup, eval_p=3, percentile=0.75):

        super(IntervalMultiKnockETRTrainer, self).__init__(lookup)
        
        self.epoch_length = lookup.num_epochs
                
        self.eval_p = 3 # can choose 3, 4, or 5
        self.satisfy_p = self.eval_p * 1.5
        if self.eval_p == 3:
            self.eval_epoch1 = int(self.epoch_length/self.eval_p)
            self.eval_epoch2 = int(self.epoch_length/self.eval_p)*2
        elif self.eval_p == 4:
            self.eval_epoch1 = int(self.epoch_length/self.eval_p)
            self.eval_epoch2 = int(self.epoch_length/self.eval_p)*2
            self.eval_epoch3 = int(self.epoch_length/self.eval_p)*3
        elif self.eval_p == 5:
            self.eval_epoch1 = int(self.epoch_length/self.eval_p)
            self.eval_epoch2 = int(self.epoch_length/self.eval_p)*2
            self.eval_epoch3 = int(self.epoch_length/self.eval_p)*3
            self.eval_epoch4 = int(self.epoch_length/self.eval_p)*4
        self.satisfy_epochs = int(self.epoch_length/self.satisfy_p)
        self.percentile = percentile * 100
        self.acc_min = 0.0
        self.random_guess = 0.1
        self.acc_max = self.random_guess * 1.5

        self.early_stopped1 = []
        self.early_stopped2 = []
        self.early_stopped3 = []
        self.early_stopped4 = []


    def get_time_saving(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        est_time = stop_epoch * (total_time / epoch_length)
        log("evaluation time saving: {:.1f}".format(total_time - est_time))
        return est_time


    def train(self, cand_index, estimates, min_train_epoch=None, space=None):
        acc = 0 # stopping accuracy
        knocked_in_count1 = 0
        knocked_in_count2 = 0
        knocked_in_count3 = 0
        knocked_in_count4 = 0
        min_epoch = 0
        cur_max_acc = 0

        acc_curve = self.acc_curves.loc[cand_index].values
        self.history.append(acc_curve)

        history1 = []; history2 = []; history3 = []; history4 = []
        knock_in_barriers1 = [0] * self.eval_epoch1
        knock_in_barriers2 = [0] * (self.eval_epoch2 - self.eval_epoch1)
        if self.eval_p >= 4:
            knock_in_barriers3 = [0] * (self.eval_epoch3 - self.eval_epoch2)
            if self.eval_p == 5:
                knock_in_barriers4 = [0] * (self.eval_epoch4 - self.eval_epoch3)

        unstopped_list1 = list(compress(self.history, 1 - np.array(self.early_stopped1))) ### survives if the paired component is True
        unstopped_list2 = list(compress(unstopped_list1, 1 - np.array(self.early_stopped2)))
        unstopped_list3 = list(compress(unstopped_list2, 1 - np.array(self.early_stopped3)))       


        for i in range(self.eval_epoch1): # creating knock-in barriers for the first segment
            history1.append([]) # add base list for the next epoch
            for n in range(len(self.history)): # number of iterations
                history1[i].append(self.history[n][i]) # vertical congregation of curve values     
            knock_in_barriers1[i] = np.percentile(history1[i], self.percentile, interpolation = 'lower') 

        if len(unstopped_list1) >= int(round(1/(1-self.percentile/100))):  # creating knock-in barriers for the second segment (if eval_p >= 3)
            for i in range(self.eval_epoch2-self.eval_epoch1):
                actual_i = i + self.eval_epoch1
                history2.append([])
                for n in range(len(unstopped_list1)):
                    history2[i].append(unstopped_list1[n][actual_i])
                knock_in_barriers2[i] = np.percentile(history2[i], self.percentile, interpolation = 'lower')
        else:
            for i in range(self.eval_epoch2-self.eval_epoch1):
                knock_in_barriers2[i] = knock_in_barriers1[i]

        if self.eval_p >= 4:  # creating knock-in barriers for the third segment (if eval_p >= 4)
            if len(unstopped_list2) >= int(round(1/(1-self.percentile/100))):
                for i in range(self.eval_epoch3-self.eval_epoch2):
                    actual_i = i + self.eval_epoch2
                    history3.append([])
                    for n in range(len(unstopped_list2)):
                        history3[i].append(unstopped_list2[n][actual_i])
                    knock_in_barriers3[i] = np.percentile(history3[i], self.percentile, interpolation = 'lower')
            else:
                for i in range(self.eval_epoch3-self.eval_epoch2):
                    knock_in_barriers3[i] = knock_in_barriers2[i]

        if self.eval_p == 5: # creating knock-in barriers for the fourth segment (if eval_p >= 5)
            if len(unstopped_list3) >= int(round(1/(1-self.percentile/100))):
                for i in range(self.eval_epoch4-self.eval_epoch3):
                    actual_i = i + self.eval_epoch3
                    history4.append([])
                    for n in range(len(unstopped_list3)):
                        history4[i].append(unstopped_list3[n][actual_i])
                    knock_in_barriers4[i] = np.percentile(history4[i], self.percentile, interpolation = 'lower')
            else:
                for i in range(self.eval_epoch4-self.eval_epoch3):
                    knock_in_barriers4[i] = knock_in_barriers3[i]
        
        debug("commencing iteration {}".format(len(self.history)))
        debug("accuracy curve: {}".format(acc_curve))


        for i in range(min_epoch, self.epoch_length-1):
            acc = acc_curve[i]
            if acc > cur_max_acc:
                cur_max_acc = acc
            
            debug("current accuracy at epoch{}: {:.4f}".format(i+1, acc))

            if len(self.history) >= int(round(1/(1-self.percentile/100))): # after fully training a few trials
                ## INTERVAL RULE
                # activates regardless of epoch in concern
                if self.acc_min <= acc <= self.acc_max:
                    debug("stopped at epoch{} locked between ({},{})".format(i+1, self.acc_min, self.acc_max))
                    self.early_stopped1.append(True)
                    self.early_stopped.append(True)
                    return 1.0 - cur_max_acc, self.get_time_saving(cand_index,i+1)

                ## KNOCK RULE
                if i+1 <= self.eval_epoch1:
                    if acc > knock_in_barriers1[i]:
                        debug("acc knocked into above {} at epoch{}".format(knock_in_barriers1[i],i+1))
                        knocked_in_count1 += 1

                if i+1 == self.eval_epoch1:
                    debug('evaluation 1/{} at epoch{}'.format(self.eval_p-1,i+1))
                    if knocked_in_count1 <= self.satisfy_epochs:
                        debug("terminated with {} less knock_ins".format(self.satisfy_epochs - knocked_in_count1))
                        self.early_stopped1.append(True)
                        self.early_stopped.append(True)
                        return 1.0 - cur_max_acc, self.get_time_saving(cand_index,i+1)

                if len(unstopped_list1) >= int(round(1/(1-self.percentile/100))):                             
                    if self.eval_epoch1 < i+1 <= self.eval_epoch2:
                        if acc > knock_in_barriers2[i]:
                            debug("acc knocked into above {} at epoch{}".format(knock_in_barriers2[i],i+1))
                            knocked_in_count2 += 1

                    if i+1 == self.eval_epoch2:
                        debug('evaluation 2/{} at epoch{}'.format(self.eval_p-1,i+1))
                        if knocked_in_count2 <= self.satisfy_epochs:
                            debug("terminated with {} less knock_ins".format(self.satisfy_epochs - knocked_in_count2))
                            self.early_stopped2.append(True)
                            self.early_stopped.append(True)
                            return 1.0 - cur_max_acc, self.get_time_saving(cand_index,i+1)

                if self.eval_p >= 4:
                    if len(unstopped_list2) >= int(round(1/(1-self.percentile/100))):  
                        if self.eval_epoch2 < i+1 <= self.eval_epoch3:
                            if acc > knock_in_barriers3[i]:
                                debug("acc knocked into above {} at epoch{}".format(knock_in_barriers3[i],i+1))
                                knocked_in_count3 += 1

                        if i+1 == self.eval_epoch3:
                            debug('evaluation 3/{} at epoch{}'.format(self.eval_p-1,i+1))
                            if knocked_in_count3 <= self.satisfy_epochs:
                                debug("terminated with {} less knock_ins".format(self.satisfy_epochs - knocked_in_count3))
                                self.early_stopped3.append(True)
                                self.early_stopped.append(True)
                                return 1.0 - cur_max_acc, self.get_time_saving(cand_index,i+1)

                        if self.eval_p == 5:
                            if len(unstopped_list3) >= int(round(1/(1-self.percentile/100))):  
                                if self.eval_epoch3 < i+1 <= self.eval_epoch4:
                                    if acc > knock_in_barriers4[i]:
                                        debug("acc knocked into above {} at epoch{}".format(knock_in_barriers4[i],i+1))
                                        knocked_in_count4 += 1

                                if i+1 == self.eval_epoch4:
                                    debug('evaluation 4/{} at epoch{}'.format(self.eval_p-1,i+1))
                                    if knocked_in_count4 <= self.satisfy_epochs:
                                        debug("terminated with {} less knock_ins".format(self.satisfy_epochs - knocked_in_count4))
                                        self.early_stopped4.append(True)
                                        self.early_stopped.append(True)
                                        return 1.0 - cur_max_acc, self.get_time_saving(cand_index,i+1)

        return 1.0 - max(acc_curve), self.total_times[cand_index]