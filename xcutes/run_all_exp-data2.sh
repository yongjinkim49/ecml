# Baseline algorithms
python hpo_runner.py -m SOBOL -s RANDOM -e GOAL -eg 0.9933 data2 100
# Single BO
python hpo_runner.py -m GP -s EI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -m GP -s PI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -m GP -s UCB -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -m RF -s EI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -m RF -s PI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -m RF -s UCB -e GOAL -eg 0.9933 data2 100
# Adaptation
python hpo_runner.py -rc gp-hedge3.json -m ADA -s BO-HEDGE -e GOAL -eg 0.9933 data2 100
# Sequential diversification
python hpo_runner.py -m DIV -s RANDOM -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -m DIV -s SEQ -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc arms-log.json -m DIV -s SEQ -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc arms-pure.json -m DIV -s SEQ -e GOAL -eg 0.9933 data2 100
# Single diversification ablation test
python hpo_runner.py -rc p6div-no_log.json -m DIV -s SEQ -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m DIV -s SEQ -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m DIV -s SEQ -e GOAL -eg 0.9933 data2 100
# GP EI ablation test
python hpo_runner.py -rc p6div-no_log.json -m GP -s EI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m GP -s EI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m GP -s EI -e GOAL -eg 0.9933 data2 100
# GP PI ablation test
python hpo_runner.py -rc p6div-no_log.json -m GP -s PI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m GP -s PI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m GP -s PI -e GOAL -eg 0.9933 data2 100
# GP UCB ablation test
python hpo_runner.py -rc p6div-no_log.json -m GP -s UCB -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m GP -s UCB -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m GP -s UCB -e GOAL -eg 0.9933 data2 100
# RF EI ablation test
python hpo_runner.py -rc p6div-no_log.json -m RF -s EI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m RF -s EI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m RF -s EI -e GOAL -eg 0.9933 data2 100
# RF PI ablation test
python hpo_runner.py -rc p6div-no_log.json -m RF -s PI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m RF -s PI -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m RF -s PI -e GOAL -eg 0.9933 data2 100
# RF UCB ablation test
python hpo_runner.py -rc p6div-no_log.json -m RF -s UCB -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m RF -s UCB -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m RF -s UCB -e GOAL -eg 0.9933 data2 100
# Parallel BO
python hpo_runner.py -rc p6gp.json -m BATCH -s SYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6gp.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6gp-nm.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6gp_pi.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6gp_ucb.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6rf.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6rf_pi.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6rf_ucb.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
# Parallel diversification ablation test
python hpo_runner.py -rc p6div-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
# no log + no ETR
python hpo_runner.py -rc p6div-no_log-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
# no log + ETR
python hpo_runner.py -rc p6div-no_log-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-no_log-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
# hybrid log + ETR
python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 data2 100
