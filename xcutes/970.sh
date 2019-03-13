# Parallel diversification
# no log + no ETR
#python hpo_runner.py -rc p6div-no_log-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
# no log + ETR
#python hpo_runner.py -rc p6div-no_log-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
# hybrid log + ETR
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
python hpo_runner.py -rc p6div-one_hot_grid.json -m RF -s EI -et 12h data3 50
python hpo_runner.py -rc p6div-one_hot_grid.json -m GP -s EI -et 12h data3 50
python hpo_runner.py -rc p6div-etr-one_hot_grid.json -m DIV -s SEQ -et 12h data3 13
