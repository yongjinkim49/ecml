import os

import pandas as pd
import numpy as np

import wot.utils.hp_cfg as hp_cfg
from commons.logger import *

def load(data_type, data_folder='lookup/', config_folder='hp_conf/', grid_order=None):
    grid_shuffle = False
    if grid_order == 'shuffle':
        grid_shuffle = True
    
    #debug("current working dir: {}".format(os.getcwd()))
    #cwd = "{}/".format(os.getcwd())
    csv_path = data_folder + str(data_type) + '.csv'
    csv_data = pd.read_csv(csv_path)

    cfg_path = config_folder + str(data_type) + '.json'
    cfg = hp_cfg.read_config(cfg_path)

    num_epochs = 15
    if hasattr(cfg, 'num_epoch'):
        num_epochs = cfg.num_epoch
    
    if data_type == 'data200':
        
        loader = LookupData200Loader(data_type, csv_data, cfg)
    else:
        loader = LookupDataLoader(data_type, csv_data, cfg, num_epochs, grid_shuffle)
    return loader


class LookupDataLoader(object):
    ''' Load lookup table data as pandas DataFrame object'''
    def __init__(self, dataset_type, surrogate, cfg, num_epochs, grid_shuffle):
        self.data = surrogate
        if grid_shuffle is True:
            self.data = self.data.sample(frac=1).reset_index(drop=True)
            
        self.config = cfg
        self.data_type = dataset_type
        
        self.begin_index = 1
        self.num_epochs = num_epochs
        self.num_hyperparams = len(cfg.param_order)

    def get_hyperparam_vectors(self):
        start_index = self.begin_index
        end_index = start_index + self.num_hyperparams
        hp_grid = self.data.ix[:, start_index:end_index].values  # hyperparameter vectors

        return hp_grid

    def get_accuracies_per_epoch(self, end_epoch=None):
        
        start_index = self.begin_index + self.num_hyperparams
        if end_epoch is None or end_epoch > self.num_epochs:            
            end_epoch = self.num_epochs
        end_index = start_index + end_epoch 
        accs = self.data.ix[:, start_index:end_index]  # accuracy at each epoch

        if hasattr(self.config, 'metric'):
            if self.config.metric == 'perplexity':
                # XXX:handle perplexity metric
                max_perplexity = 1000.0
                perplexities = accs
                accs = (max_perplexity - perplexities) / max_perplexity       
        return accs

    def get_test_errors(self, end_epoch=None):
        vals = self.get_accuracies_per_epoch(end_epoch)
        sorted_vals = np.sort(vals)  # sorted accuracies
        ei = self.num_epochs - 1
        if end_epoch is not None: 
            if end_epoch > 0 and end_epoch <= self.num_epochs:
                ei = end_epoch - 1

        fin_vals = sorted_vals[:, ei]  # accuracy when training finished
        fin_loss = 1 - fin_vals  # final error
        return fin_loss

    def get_elapsed_times(self):
        time_col_index = self.begin_index + self.num_hyperparams + self.num_epochs  #25
        dur = self.data.ix[:, time_col_index].values  # elapsed time

        return dur

    def get_sobol_grid(self): 
        start_index = self.begin_index + self.num_hyperparams + self.num_epochs + 1 #26
        end_index = start_index + self.num_hyperparams #35
        sobol_grid = self.data.ix[:, start_index:end_index].values 
    
        return sobol_grid

    def get_best_acc_of_trial(self):
        return np.max(self.get_accuracies_per_epoch().values, axis=1)


class LookupData200Loader(LookupDataLoader):
    ''' Load lookup table data as pandas DataFrame object'''
    def __init__(self, dataset_type, results, cfg):
        
        self.data = results    
        self.config = cfg

        self.data_type = dataset_type
        
        self.begin_index = 1
        self.num_epochs = 100
        
        self.num_hyperparams = len(cfg.param_order)

    def get_hyperparam_vectors(self):

        start_index = self.begin_index
        end_index = start_index + self.num_hyperparams
        hp_grid = self.data.ix[:, start_index:end_index].values  # hyperparameter vectors

        return hp_grid

    def get_accuracies_per_epoch(self, end_epoch=None):
        
        start_index = self.begin_index + self.num_hyperparams + 102 # skip durations + 0 epoch
        if end_epoch is None or end_epoch > self.num_epochs:            
            end_epoch = self.num_epochs
        end_index = start_index + end_epoch 
        accs = self.data.ix[:, start_index:end_index]  # accuracy at each epoch
    
        return accs

    def get_elapsed_times(self, end_epoch=None):
        if end_epoch is None:
            end_epoch = 100
        time_col_index = self.begin_index + self.num_hyperparams + end_epoch  #25
        dur = self.data.ix[:, time_col_index].values  # elapsed time

        return dur

    def get_sobol_grid(self): 
        start_index = self.begin_index + self.num_hyperparams + 202
        end_index = start_index + self.num_hyperparams
        sobol_grid = self.data.iloc[:, start_index:end_index].values 

        return sobol_grid


if __name__ == '__main__':
    l = load('data200', data_folder='./lookup/')
    print(l.num_hyperparams)
    print(list(l.get_elapsed_times().columns.values))
