# Scalable Unified Hyperparameter Optimization Framework of Deep Neural Networks

## Abstract

TBD

**Key features**
  * Pluggable structure which can easily expand HPO algorithms
  * HPO as Multi-armed Bandits
  * Diversification for robust and effective HPO
  * Large scale HPO by building a microservices architecture
    * Resource Oriented Architecture with RESTful Web API

TODO:System architecture diagram required

We firstly unified all three practical ML HPO frameworks:

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

If you are working on Linux, install these packages as follows:

```bash

(hpo)device:path$ conda install pandas scikit-learn future numpy scipy
(hpo)device:path$ pip install hyperopt validators flask-restful
```

(Optional) Speeding up the gradient calculation in GP, install below package:
```bash
(hpo)device:path$ conda install -c conda-forge weave
```

### Install with PIP

TODO

------

## How to run the experiment in single mode

### Run with Console Mode

```bash
(mab)$ python hpo_runner.py data2 10 -m=GP -s=EI -e=GOAL -eg=0.99
```

* This command executes the hyperparameter optimization with the surrogates named data2 10 times by a specific optimizer(*GP modeling and EI acquisition function*).
  * It forces to be terminated when the target goal accuracy (0.99) achieved.


```bash
(mab)$ python hpo_runner.py data3 10 -e=TIME -et=36000
```

* This command optimizes the hyperparameters of surrogates data3 10 times with diverification with given time bin.
  * It will not be terminated before the given time (36000 secs == 10 min.) expired.


See help for more options.

```bash
(mab)$ python hpo_runner.py --help
usage: hpo_runner.py [-h] [-m MODE] [-s SPEC] [-e EXP_CRT] [-eg EXP_GOAL]
                        [-et EXP_TIME] [-c CONF] [-rc RUN_CONF] [-hc HP_CONF]
                        [-w WORKER_URL] [-l LOG_LEVEL] [-r RERUN] [-p PKL]
                        [-tp TIME_PENALTY]
                        config_name num_trials

positional arguments:
  config_name           hyperparameter configuration name.
  num_trials            The total repeats of the experiment.

optional arguments:
  -h, --help            show this help message and exit
  -m MODE, --mode MODE  The optimization mode. Set a model name to use a
                        specific model only.Set DIV to sequential
                        diverification mode. Set BATCH to parallel mode.
                        ['RANDOM', 'GP', 'RF', 'TPE', 'GP-NM', 'GP-ALE', 'RF-
                        ALE', 'DIV', 'BATCH'] are available. default is DIV.
  -s SPEC, --spec SPEC  The detailed specification of the given mode. (e.g.
                        acquisition function) ['RANDOM', 'TPE', 'EI', 'PI',
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
                        Default setting is 0.999.
  -et EXP_TIME, --exp_time EXP_TIME
                        The time each trial expires. When the time is up, it
                        is automatically terminated. Default setting is 86400.
  -c CONF, --conf CONF  Run configuration file name existed in ./run_conf/.
                        Default setting is arms.json
  -rc RUN_CONF, --run_conf RUN_CONF
                        Run configuration directory. Default setting is
                        ./run_conf/
  -hc HP_CONF, --hp_conf HP_CONF
                        Hyperparameter configuration directory. Default
                        setting is ./hp_conf/
  -w WORKER_URL, --worker_url WORKER_URL
                        Remote training worker URL. Set the valid URL for
                        remote training.
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        Print out log level. ['debug', 'warn', 'error', 'log']
                        are available. default is warn


```

For more information, kindly refer to the [Wiki page](https://github.com/hyunghunny/hpo-mab/wiki).

#### Run HPO through surrogates
TODO

#### Run HPO through the remote worker

TODO

## How to run the experiment on Microservice Mode

### Install WoT interface 

TODO

### Run HPO with Web Service Mode

TODO

## How to run the experiment in parallel mode

#### Configure your mashup

TODO
