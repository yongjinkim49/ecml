# Parallel diversification
# no log + no ETR
python hpo_runner.py -rc p6div-no_log-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-no_log-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-no_log-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-no_log.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
# no log + ETR
python hpo_runner.py -rc p6div-no_log-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-no_log-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-no_log-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-no_log-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
# hybrid log + ETR
python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.935 -et 30h data207 100


