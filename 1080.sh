# Baseline algorithms
#python hpo_runner.py -m RANDOM -s RANDOM -et 1d data1 100
# Single BO
#python hpo_runner.py -m GP -s EI -et 1d data1 100
python hpo_runner.py -m GP -s PI -et 1d data1 100
python hpo_runner.py -m GP -s UCB -et 1d data1 100
python hpo_runner.py -m RF -s EI -et 1d data1 100
python hpo_runner.py -m RF -s PI -et 1d data1 100
python hpo_runner.py -m RF -s UCB -et 1d data1 100
# Adaptation
python hpo_runner.py -rc gp-hedge3.json -m ADA -s BO-HEDGE -et 1d data1 100
# Sequential diversification
python hpo_runner.py -m DIV -s RANDOM -et 1d data1 100
python hpo_runner.py -m DIV -s SEQ -et 1d data1 100
#python hpo_runner.py -rc arms-log.json -m DIV -s SEQ -et 1d data1 100
python hpo_runner.py -rc arms-pure.json -m DIV -s SEQ -et 1d data1 100
# Parallel BO
python hpo_runner.py -rc p6gp.json -m BATCH -s SYNC -et 4h data1 100
python hpo_runner.py -rc p6gp.json -m BATCH -s ASYNC -et 4h data1 100
python hpo_runner.py -rc p6gp-nm.json -m BATCH -s ASYNC -et 4h data1 100
python hpo_runner.py -rc p6rf.json -m BATCH -s ASYNC -et 4h data1 100
# parallel diversification
#python hpo_runner.py -m BATCH -s ASYNC -et 4h data1 100