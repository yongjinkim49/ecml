from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import os.path

import pickle
import gzip
import json

from ws.shared.logger import *

class ResultSaver(object):
    def __init__(self, data_type, run_mode, 
                target_accuracy, time_expired, config, 
                path='./results/', postfix=""):

        self.data_type = data_type
        self.run_mode = run_mode
        self.target_accuracy = target_accuracy
        self.time_expired = time_expired
        self.path = path
        self.config = config
        self.postfix = postfix

    def save(self, name1, name2, trials, results, est_records=None):
    
        directory = self.path + str(self.data_type) +\
            "/" + str(trials) + "_trials"

        if self.run_mode == 'GOAL':
            directory += "/goal_" + str(self.target_accuracy)
        elif self.run_mode == 'TIME':
            directory += "/" + str(int(self.time_expired)) + "_secs"

        if not os.path.exists(directory):
            debug('Creating ' + directory)
            os.makedirs(directory)

        file_path = directory + '/' +\
            name1 + '_' + name2

        if 'title' in self.config:
            file_path = "{}-{}".format(file_path, self.config['title'])

        file_path += self.postfix
        
        log("The results will be saved as {}.json".format(file_path))
        with open(file_path + '.json', 'w') as json_file:
            json_file.write(json.dumps(results))

        if est_records is not None:
            with gzip.open(file_path + '.pkl.gz', 'wb') as pkl_gz:
                pickle.dump(est_records, pkl_gz)

    def load(self, optimizer, aquisition_func, num_trials):
        
        directory = self.path + str(self.data_type) +\
            "/" + str(num_trials) + "_trials"

        if self.run_mode == 'GOAL':
            directory += "/goal_" + str(self.target_accuracy)
        elif self.run_mode == 'TIME':
            directory += "/" + str(int(self.time_expired)) + "_secs"

        if not os.path.exists(directory):
            debug('Creating ' + directory)
            os.makedirs(directory)
        file_path = directory + '/' +\
            optimizer + '_' + aquisition_func + ".json"
        if os.path.isfile(file_path):
            with open(file_path) as json_temp:
                temp_results = json.load(json_temp)
                iters = [int(key) for key in temp_results.keys()]
                sorted_iters = sorted(iters)
                return temp_results, sorted_iters[-1] + 1
        else:
            return {}, 0


class BatchResultSaver(object):
    
    def __init__(self, data_type, run_mode, 
                target_accuracy, time_expired, config, 
                path='./results/'):

        self.data_type = data_type
        self.run_mode = run_mode
        self.target_acc = target_accuracy
        self.time_expired = time_expired
        self.path = path
        self.config = config

    def save(self, sync_type, trials, results,
                path='./results/'):

        directory = path + str(self.data_type) +\
            "/" + str(trials) + "_trials"

        if self.run_mode == 'GOAL':
            directory += "/goal_" + str(self.target_acc)
        elif self.run_mode == 'TIME':
            directory += "/" + str(int(self.time_expired)) + "_secs"

        if not os.path.exists(directory):
            debug('Creating ' + directory)
            os.makedirs(directory)

        file_path = directory + '/' +\
            sync_type.upper() + '_BATCH'

        if 'title' in self.config:
            file_path = "{}-{}".format(file_path, self.config['title'])

        log("The results will be saved as {}.json".format(file_path))
        with open(file_path + '.json', 'w') as json_file:
            json_file.write(json.dumps(results))    


class TempSaver(object):
    
    def __init__(self, data_type, optimizer, aquisition_func, num_trials, config,
                path='./'):
        
        self.temp_name = "{}-{}_{}-{}".format(data_type, 
                        optimizer, aquisition_func, num_trials)
        if 'title' in config:
            self.temp_name = "{}-{}".format(self.temp_name, config['title'])
        self.path = path
        self.temp_file_path = None

    def save(self, results):
        self.temp_file_path = self.path + self.temp_name + '.temp.json'
        with open(self.temp_file_path, 'w') as json_file:
            json_file.write(json.dumps(results))

    def restore(self):
        self.temp_file_path = self.path + self.temp_name + '.temp.json'
        if os.path.isfile(self.temp_file_path):
            with open(self.temp_file_path) as json_temp:
                temp_results = json.load(json_temp)
                iters = [int(key) for key in temp_results.keys()]
                sorted_iters = sorted(iters)
                return temp_results, sorted_iters[-1] + 1
        else:
            return {}, 0

    def remove(self):
        if self.temp_file_path is not None:
            try:
                os.remove(self.temp_file_path)
            except OSError:
                pass

    