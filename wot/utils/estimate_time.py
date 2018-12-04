from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy as cp
import numpy as np
import scipy.linalg as spla
import scipy.stats as sps
from sklearn.ensemble import RandomForestRegressor
from sklearn import datasets, linear_model, metrics

from utils.logger import *

def get_exec_time_estimator(type, sobol_grid=None, exec_time=None):
    if type == 'LR':
        model = linear_model.LinearRegression()
        if sobol_grid is None or exec_time is None:
            return SequentialTimeEstimator(model)
        else:
            return SobolSequenceTimeEstimator(model, sobol_grid, exec_time)
    elif type == 'RF':
        model = RandomForestRegressor(n_estimators=50, max_depth=2, random_state=0)
        if sobol_grid is None or exec_time is None:
            return SequentialTimeEstimator(model)
        else:
            return SobolSequenceTimeEstimator(model, sobol_grid, exec_time)
    else:
        raise ValueError('unsupported estimator type: {}'.format(type))


def configure_time_acquisitions(strategies):
    time_acq_funcs = []

    if 'ET_L0.1' in strategies:
        time_acq_funcs.append(
            {'name': 'ET_L0.1', 'type': 'linear', 'rate': 0.1})
    if 'ET_L0.2' in strategies:
        time_acq_funcs.append(
            {'name': 'ET_L0.2', 'type': 'linear', 'rate': 0.2})
    if 'ET_L0.4' in strategies:
        time_acq_funcs.append(
            {'name': 'ET_L0.4', 'type': 'linear', 'rate': 0.4})
    if 'ET_T5' in strategies:
        time_acq_funcs.append(
            {'name': 'ET_T5', 'type': 'top_k', 'rate': 5})
    if 'ET_T10' in strategies:
        time_acq_funcs.append(
            {'name': 'ET_T10', 'type': 'top_k', 'rate': 10})
    if 'ET_T20' in strategies:
        time_acq_funcs.append(
            {'name': 'ET_T20', 'type': 'top_k', 'rate': 20})
    if 'ET_PS' in strategies:
        time_acq_funcs.append({'name': 'ET_PS', 'type': 'per_second'})
    if 'ET_PLS' in strategies:
        time_acq_funcs.append({'name': 'ET_PLS', 'type': 'per_log_second'})
    # TODO: add more time strategy

    return time_acq_funcs


class SequentialTimeEstimator(object):
    '''Training time predictor'''
    def __init__(self, model):
        self.train_model = model
        self.reset()

    def reset(self):
        self.train_x = None
        self.train_y = np.array([])
        self.trained = False
        self.predict_y = None

    def add_train_data(self, train_x, train_y):
        if len(train_x) != len(train_y):
            raise ValueError('train data size mismatch: {}, {}'.format(
                len(train_x), len(train_y)))
        if self.train_x is None:
            self.train_x = train_x
        else:
            self.train_x = np.concatenate(self.train_x, train_x)

        self.train_y = np.append(self.train_y, train_y)
        debug("training data size: {}".format(len(self.train_y)))

    def train(self):
        if len(self.train_x) > 0 and len(self.train_y) > 0:
            if len(self.train_x) == len(self.train_y):
                self.train_model.fit(self.train_x, self.train_y)
                self.trained = True
                return True
        return False

    def predict(self, eval_x):
        if self.trained is False:
            raise TypeError('model is not trained yet.')

        predict_y = self.train_model.predict(eval_x)
        
        return predict_y

    def evaluate(self, predict_y, real_y):
        if len(real_y) == 0 or len(predict_y) == 0:
            raise ValueError("no predicted values or actual values.")
        error = np.absolute(real_y - predict_y)
        error_rate = np.mean(error / real_y)

        return error_rate, error


class SobolSequenceTimeEstimator(SequentialTimeEstimator):
    ''' Time estimation with Sobol sequences look up '''
    def __init__(self, model, sobol_grid, exec_time, do_eval=False):
        self.sobol_grid = sobol_grid
        self.exec_time = exec_time
        self.min_train_data = 10

        self.do_eval = do_eval
        self.curr_cv_err = None
        self.best_model = None

        super(SobolSequenceTimeEstimator, self).__init__(model)

    def cross_validate(self, complete, n_fold=5):
        n_fold_data = {}
        for n in range(n_fold):
            n_fold_data[str(n)] = {'eval': [], 'train': []}

        if len(complete) % n_fold == 0:
            for i in range(n_fold):
                for j in range(len(complete)):
                    if j % n_fold == i:
                        n_fold_data[str(i)]['eval'].append(complete[j])
                    else:
                        n_fold_data[str(i)]['train'].append(complete[j]) 
            # get a mean of cross validation error
            validate_errors = []
            for n in range(n_fold):
                self.reset()
                trains = n_fold_data[str(n)]['train']
                evals = n_fold_data[str(n)]['eval']
                self.add_train_data(self.sobol_grid[trains, :], 
                                    self.exec_time[trains])
                self.train()
                predict_exec_time = self.predict(self.sobol_grid[evals, :])
                real_exec_time = self.exec_time[evals]
                error_rate, _ = self.evaluate(predict_exec_time, real_exec_time)
                validate_errors.append(error_rate)

            if self.curr_cv_err is None or self.curr_cv_err > np.mean(validate_errors):
                self.curr_cv_err = np.mean(validate_errors)
                debug('best model will be updated with CV error: {}'.format(self.curr_cv_err))
                self.reset()
                self.add_train_data(self.sobol_grid[complete, :], self.exec_time[complete])
                self.train()
                self.best_model = cp.copy(self.train_model)
                return True
            else:
                return False

        else:
            return False


    def estimate(self, candidates, complete):
        if self.min_train_data > len(self.sobol_grid[complete, :]):
            return False, None
        
        if self.cross_validate(complete, n_fold=5) is False:
            if self.best_model is not None:
                self.train_model = self.best_model
            else:
                return False, None
        
        hp_candidate = self.sobol_grid[candidates, :]
        predict_exec_times = self.predict(hp_candidate)
        if self.do_eval:
            real_exec_time = self.exec_time[candidates]
            error_rate, _ = self.evaluate(predict_exec_times, real_exec_time)            
            debug('actual time estimation mean error: {}%'.format(error_rate * 100))

        return True, predict_exec_times


