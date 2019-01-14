import math
import random
import numpy        as np
import numpy.random as npr
import scipy.stats  as sps
import sklearn.ensemble
import sklearn.ensemble.forest

from util import *
from acq_func import *

from ws.shared.logger import *
from ws.shared.resp_shape import *

from sklearn.externals.joblib import Parallel, delayed

#Example Config
#https://github.com/automl/HPOlib/blob/master/optimizers/smac/smac_2_10_00-devDefault.cfg

def init(expt_dir, arg_string):
    args = unpack_args(arg_string)
    return RFChooser(**args)


class RandomForestRegressorWithVariance(sklearn.ensemble.RandomForestRegressor):

    def predict(self,X):
        # Check data
        X = np.atleast_2d(X)

        all_y_hat = [ tree.predict(X) for tree in self.estimators_ ]

        # Reduce
        y_hat = sum(all_y_hat) / self.n_estimators
        y_var = np.var(all_y_hat,axis=0,ddof=1)

        return y_hat, y_var

class RFChooser:
    # XXX: set min_samples_split to 2 from 1. See issue #2 
    def __init__(self,n_trees=50,
                 max_depth=None,
                 min_samples_split=2, 
                 max_monkeys=7,
                 max_features="auto",
                 n_jobs=1,
                 random_state=None,
                 response_shaping=False,
                 shaping_func="log_err"):
        self.n_trees = float(n_trees)
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.n_jobs = float(n_jobs)
        self.random_state = random_state
        self.response_shaping = bool(response_shaping)
        self.shaping_func = shaping_func
        self.rf = RandomForestRegressorWithVariance(n_estimators=n_trees,
                                                    max_depth=max_depth,
                                                    min_samples_split=min_samples_split,
                                                    max_features=max_features,
                                                    n_jobs=n_jobs,
                                                    random_state=random_state)
        self.acq_funcs = ['EI', 'PI', 'UCB']

        self.mean_value = None
        self.estimates = None

    def set_eval_time_penalty(self, estmated_time):
        # TODO: Set eval time penalty for acquisition
        pass

    def next(self, samples, af, use_interim=True):        
        
        candidates = samples.get_candidates(use_interim)
        completes = samples.get_completes(use_interim)
        # Grab out the relevant sets.
        
        # Don't bother using fancy RF stuff at first.
        if completes.shape[0] < 2:
            return int(random.choice(candidates))

        # Grab out the relevant sets.
        
        errs = samples.get_errors("completes", use_interim)
        comp = samples.get_grid("completes", use_interim)
        cand = samples.get_grid("candidates", use_interim)

        #debug("[RF] shape of completes: {}, cands: {}, errs: {}".format(comp.shape, cand.shape, errs.shape))

        if self.response_shaping is True:
            # transform errors to log10(errors) for enhancing optimization performance
            if self.shaping_func == "log_err":
                
                debug("before scaling: {}".format(errs))
                errs = np.log10(errs)
                v_func = np.vectorize(apply_log_err)
                errs = v_func(errs)
            elif self.shaping_func == "hybrid_log":
                v_func = np.vectorize(apply_hybrid_log)
                errs = v_func(errs, threshold=.3)
            else:
                errs = np.log10(errs)
                
        #debug("errors: {}".format(errs))  

        self.rf.fit(comp, errs) 

        func_m, func_v = self.rf.predict(cand)

        # Current best.
        best = np.min(errs)

        acq_func = get_acq_func(af)
        af_values = acq_func(best, func_m, func_v)
        
        best_cand = np.argmax(af_values)

        self.mean_value = func_m[best_cand]
        self.estimates = {
            'candidates' : candidates.tolist(),
            'acq_funcs' : af_values.tolist(),
            'means': func_m.tolist(),
            'vars' : func_v.tolist()
        }
        

        return int(candidates[best_cand])
