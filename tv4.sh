# Baseline algorithms
#python hpo_runner.py -m RANDOM -s RANDOM -et 1d data3 100
# Single BO
#python hpo_runner.py -m GP -s EI -et 1d data3 100
#python hpo_runner.py -m GP -s PI -et 1d data3 100
#python hpo_runner.py -m GP -s UCB -et 1d data3 100
#python hpo_runner.py -m RF -s EI -et 1d data3 100
#python hpo_runner.py -m RF -s PI -et 1d data3 100
#python hpo_runner.py -m RF -s UCB -et 1d data3 100
# Adaptation
#python hpo_runner.py -rc gp-hedge3.json -m ADA -s BO-HEDGE -et 1d data3 100
# Sequential diversification
#python hpo_runner.py -m DIV -s RANDOM -et 1d data3 100
#python hpo_runner.py -m DIV -s SEQ -et 1d data3 100
#python hpo_runner.py -rc arms-log.json -m DIV -s SEQ -et 1d data3 100
#python hpo_runner.py -rc arms-pure.json -m DIV -s SEQ -et 1d data3 100
# Parallel BO
#python hpo_runner.py -rc p6gp.json -m BATCH -s SYNC -et 4h data3 100
#python hpo_runner.py -rc p6gp.json -m BATCH -s ASYNC -et 4h data3 100
#python hpo_runner.py -rc p6gp-nm.json -m BATCH -s ASYNC -et 4h data3 100
#python hpo_runner.py -rc p6rf.json -m BATCH -s ASYNC -et 4h data3 100
# Parallel diversification
#python hpo_runner.py -rc no_failover.json -m BATCH -s ASYNC -et 4h data3 100
#python hpo_runner.py -m BATCH -s ASYNC -et 4h data3 100
# Sequential diversification with ETR
#python hpo_runner.py -m DIV -s SEQ -et 1d -etr VizMedian data2 90
#python hpo_runner.py -m DIV -s SEQ -et 1d -etr Interval data2 90
#python hpo_runner.py -m DIV -s SEQ -et 1d -etr Knock data2 90
#python hpo_runner.py -m DIV -s SEQ -et 1d -etr IntervalPentaOpt data3 100
python hpo_runner.py -rc p6gp-nm.json -m BATCH -s ASYNC -et 30h data207 100
python hpo_runner.py -rc p6rf.json -m BATCH -s ASYNC -et 30h data207 100

# Parallel diversification
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -et 30h data207 100
python hpo_runner.py -rc no_failover.json -m BATCH -s ASYNC -et 30h data207 100
