# hybrid log + no ETR
#python hpo_runner.py -rc p6div-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
# no log + ETR
#python hpo_runner.py -rc p6div-no_log-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-no_log-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
python hpo_runner.py -rc p6div-etr-one_hot_grid.json -m DIV -s SEQ -et 12h data3 50

