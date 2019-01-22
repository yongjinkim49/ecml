# Baseline algorithms
#python hpo_runner.py -m RANDOM -s RANDOM -et 5d data207 100
# Sequential BO
#python hpo_runner.py -m GP -s EI -et 5d data207 100
#python hpo_runner.py -m GP -s PI -et 5d data207 100
#python hpo_runner.py -m GP -s UCB -et 5d data207 100
#python hpo_runner.py -m RF -s EI -et 5d data207 100
#python hpo_runner.py -m RF -s PI -et 5d data207 100
#python hpo_runner.py -m RF -s UCB -et 5d data207 100
# Adaptation
#python hpo_runner.py -rc gp-hedge3.json -m ADA -s BO-HEDGE -et 5d data207 100
# Sequential diversification
#python hpo_runner.py -m DIV -s RANDOM -et 5d data207 100
#python hpo_runner.py -m DIV -s SEQ -et 5d data207 100
#python hpo_runner.py -rc arms-log.json -m DIV -s SEQ -et 5d data207 100
#python hpo_runner.py -rc arms-pure.json -m DIV -s SEQ -et 5d data207 100
# Parallel BO
#python hpo_runner.py -rc p6gp.json -m BATCH -s SYNC -et 20h data207 100
#python hpo_runner.py -rc p6gp.json -m BATCH -s ASYNC -et 20h data207 100
#python hpo_runner.py -rc p6gp-nm.json -m BATCH -s ASYNC -et 20h data207 100
#python hpo_runner.py -rc p6rf.json -m BATCH -s ASYNC -et 20h data207 100
# Parallel diversification
#python hpo_runner.py -m BATCH -s ASYNC -et 20h data207 100
#python hpo_runner.py -rc no_failover.json -m BATCH -s ASYNC -et 20h data207 100
#python hpo_runner.py -m DIV -s SEQ -et 5d -etr IntervalPentaOpt data207 100
# Parallel BO
#python hpo_runner.py -rc p6gp.json -m BATCH -s SYNC -et 30h data207 100
#python hpo_runner.py -rc p6gp.json -m BATCH -s ASYNC -et 30h data207 100
#python hpo_runner.py -rc no_failover.json -m BATCH -s ASYNC -et 30h data207 100
#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 -et 4h data2 100
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 -et 4h data2 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 -et 4h data2 100
#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9922 -et 4h data3 100
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9922 -et 4h data3 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9922 -et 4h data3 100
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.4596 -et 4h data30 100
#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.4596 -et 4h data30 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.4596 -et 4h data30 100
python hpo_runner.py -rc p6div-etr-w12h.json -m DIV -s SEQ -et 1d data3 100

