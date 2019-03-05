# Diversified Bayesian Optimization for DNN Hyperparameter Optimization

## Abstract

Bayesian Optimization (BO) is a well-known solution for automatic Hyper-Parameter Optimization (HPO) of machine learning models. For Deep Neural Networks (DNN), however, the use of BO has been rather limited because of the fear of a disastrous failure. 
In this paper, we adopt a diversification strategy using six different BO algorithms to design S-Div and P-Div, and show that both expected and worst-case performances can be improved. 
S-Div is a sequential diversification strategy that repeatedly goes through the six options using a single processor and P-Div is its parallel version. For further enhancements, cost function transformation and early termination rule are investigated for S-Div and history sharing strategy over parallel workers is investigated for P-Div. 
For the evaluation, we have performed an extensive investigation over six benchmark tasks. In terms of success rate, S-Div and P-Div achieved 53\% and 134\% of average improvements over the existing BO techniques. In terms of time to reach a target performance, S-Div and P-Div achieved 41\% and 50\% of average reductions. Also, S-Div and a state-of-the-art algorithm BOHB are compared and S-Div is found to substantially outperform BOHB for the benchmark DNN problems.  

**Key features**
  * Pluggable structure which can easily expand HPO algorithms
  * HPO as Multi-armed Bandits
  * Diversification for robust and effective HPO
  * Large scale HPO by building a microservices architecture
    * Resource Oriented Architecture with RESTful Web API

We unified all three practical ML HPO frameworks for diversificated BO:

* [Spearmint](https://github.com/JasperSnoek/spearmint) 
* [SMAC](http://www.cs.ubc.ca/labs/beta/Projects/SMAC/)
* [Hyperopt](https://github.com/hyperopt/hyperopt)

We diversify these regression modelling algorithms (along with their acquisition functions) to achieve robust and excellent performance. 

## Installation

### Prerequisites

I strongly suggest to make new virtual environment by using [Anaconda](https://www.anaconda.com/download/).
Due to complex package dependencies, this project only tested on Python 2.7.x.

```bash
    conda create -n hpo python=2.7
```

After creating the environment, activate your environment as follows:

```bash
    source activate hpo
```

The following additional packages are required to install:

* pandas
* scikit-learn
* future
* hyperopt
* validators
* weave
* flask-restful
* requests

If you are working on Linux, install these packages as follows:

```bash

(hpo)device:path$ conda install pandas scikit-learn future numpy scipy
(hpo)device:path$ pip install hyperopt validators flask-restful requests
```


(Optional) Speeding up the gradient calculation in GP, install below package:
```bash
(hpo)device:path$ conda install -c conda-forge weave
```


## How to run the experiment 

### Run with Console Mode

```bash
(mab)$ python hpo_runner.py data2 10 -m=GP -s=EI -e=GOAL -eg=0.99
```

* This command executes the hyperparameter optimization with the surrogates named data2 10 times by a specific optimizer(*GP modeling and EI acquisition function*).
  * It forces to be terminated when the target goal accuracy (0.99) achieved.


```bash
(mab)$ python hpo_runner.py data3 10 -e=TIME -et=36000
```

* This command optimizes the hyperparameters of surrogates benchmark data3 10 times with diverification with given time bin.
  * It will not be terminated before the given time (36000 secs == 10 min.) expired.


See help for more options.

```bash
(mab)$ python hpo_runner.py --help
usage: hpo_runner.py [-h] [-m MODE] [-s SPEC] [-e EXP_CRT] [-eg EXP_GOAL]
                     [-et EXP_TIME] [-etr EARLY_TERM_RULE] [-rd RCONF_DIR]
                     [-hd HCONF_DIR] [-rc RCONF] [-w WORKER_URL]
                     [-l LOG_LEVEL] [-r RERUN] [-p PKL]
                     hp_config num_trials

positional arguments:
  hp_config             hyperparameter configuration name.
  num_trials            The total repeats of the experiment.

optional arguments:
  -h, --help            show this help message and exit
  -m MODE, --mode MODE  The optimization mode. Set a model name to use a
                        specific model only. Set DIV to sequential
                        diverification mode. Set BATCH to parallel mode.
                        ['SOBOL', 'GP', 'RF', 'TPE', 'GP-NM', 'GP-HLE',
                        'RF-HLE', 'TPE-HLE', 'DIV', 'ADA', 'BATCH'] are available.
                        default is DIV.
  -s SPEC, --spec SPEC  The detailed specification of the given mode. (e.g.
                        acquisition function) ['RANDOM', 'EI', 'PI',
                        'UCB', 'SEQ', 'RANDOM', 'HEDGE', 'BO-HEDGE', 'BO-
                        HEDGE-T', 'BO-HEDGE-LE', 'BO-HEDGE-LET', 'EG', 'EG-
                        LE', 'GT', 'GT-LE', 'SKO', 'SYNC', 'ASYNC'] are
                        available. default is SEQ.
  -e EXP_CRT, --exp_crt EXP_CRT
                        Expiry criteria of the trial. Set "TIME" to run each
                        trial until given exp_time expired.Or Set "GOAL" to
                        run until each trial achieves exp_goal.Default setting
                        is TIME.
  -eg EXP_GOAL, --exp_goal EXP_GOAL
                        The expected target goal accuracy. When it is
                        achieved, the trial will be terminated automatically.
                        Default setting is 0.9999.
  -et EXP_TIME, --exp_time EXP_TIME
                        The time each trial expires. When the time is up, it
                        is automatically terminated. Default setting is 86400.
  -etr EARLY_TERM_RULE, --early_term_rule EARLY_TERM_RULE
                        Early termination rule. Default setting is None.
  -rd RCONF_DIR, --rconf_dir RCONF_DIR
                        Run configuration directory. Default setting is
                        ./run_conf/
  -hd HCONF_DIR, --hconf_dir HCONF_DIR
                        Hyperparameter configuration directory. Default
                        setting is ./hp_conf/
  -rc RCONF, --rconf RCONF
                        Run configuration file in ./run_conf/. Default setting
                        is arms.json
  -w WORKER_URL, --worker_url WORKER_URL
                        Remote training worker node URL. Set the valid URL if
                        remote training required.
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        Print out log level. ['debug', 'warn', 'error', 'log']
                        are available. default is warn
  -r RERUN, --rerun RERUN
                        [Experimental] Use to expand the number of trials for
                        the experiment. zero means no rerun. default is 0.
  -p PKL, --pkl PKL     [Experimental] Whether to save internal values into a
                        pickle file. CAUTION:this operation requires very
                        large storage space! Default value is False.


```

