from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ws.shared.logger import *
from ws.shared.proto import TrainerPrototype

class TrainEmulator(TrainerPrototype):
    def __init__(self, lookup):
    
        self.lookup = lookup
        self.acc_curves = lookup.get_accuracies_per_epoch()
        self.total_times = lookup.get_elapsed_times()
        self.data_type = lookup.data_type
        
        super(TrainEmulator, self).__init__()

    def reset(self):
        pass

    def get_min_train_epoch(self):
        if self.lookup.data_type == "data200":
            return 30
        elif self.lookup.data_type == "data20" or self.lookup.data_type == "data30":
            return 15
        else:
            return 4  

    def train(self, cand_index, estimates=None, space=None):
        acc_curve = self.acc_curves.loc[cand_index].values
        total_time = self.total_times[cand_index]

        return 1.0 - max(acc_curve), total_time, False         

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


class EarlyTerminateTrainer(TrainEmulator):

    def __init__(self, lookup):

        super(EarlyTerminateTrainer, self).__init__(lookup)

        self.history = []
        self.early_terminated_history = []

    def reset(self):
        # reset history
        self.history = []
        self.early_terminated_history = []

    def get_train_time(self, cand_index, stop_epoch):
        # XXX: consider preparation time later
        total_time = self.total_times[cand_index]
        acc_curve = self.acc_curves.loc[cand_index].values
        epoch_length = len(acc_curve)
        elapsed_time = stop_epoch * (total_time / epoch_length)
        log("Evaluation time saving by early termination: {:.1f} sec".format(total_time - elapsed_time))
        return elapsed_time

    def get_preevaluated_result(self, cand_index):
        acc_curve = self.acc_curves.loc[cand_index].values
        train_time = self.total_times[cand_index]
        min_loss = 1.0 - max(acc_curve)
        return acc_curve, train_time, min_loss
        

class EarlyStopTerminateBoilerplate(EarlyTerminateTrainer):
    ''' Sample code for your ETR logic. 
        You will implement the following methods:   
    
    '''
    def __init__(self, lookup, **kwargs):
        # TODO: you can add more attributes here (if required)       
        super(EarlyStopTrainerBoilerplate, self).__init__(lookup)

    def train(self, cand_index, estimates=None, space=None):
        # Firstly, you should add current candidate index to 
        
        # You can access the accuracy curve as below
        acc_curve = self.acc_curves.loc[cand_index].values

        # You can also access a previous accuracy curve as follows:
        for acc_curve in self.history:
            print(acc_curve) 

        # TODO: Your algorithm here
        early_termination = True # if your algorithm fires, append the result as below:
        if early_termination:
            self.early_terminated_history.append(True)
            stopped_error = 0.1
            eval_time = 100

            # TODO: you should return the error when it stopped and time to execute here.
            return stopped_error, eval_time, True
        else:
            self.early_terminated_history.append(False)

            return 1.0 - max(acc_curve), self.total_times[cand_index], False

