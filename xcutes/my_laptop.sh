# Parallel diversification with ETR
#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100

#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.8994 -et 4h data10 100
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.8994 -et 4h data10 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.8994 -et 4h data10 100

#python hpo_runner.py -rc p6div-etr-nc.json -m BATCH -s ASYNC -e GOAL -eg 0.784 -et 4h data20 100
#python hpo_runner.py -rc p6div-etr-nf.json -m BATCH -s ASYNC -e GOAL -eg 0.784 -et 4h data20 100
#python hpo_runner.py -rc p6div-etr-rand.json -m BATCH -s ASYNC -e GOAL -eg 0.784 -et 4h data20 100

python hpo_runner.py -m DIV -s SEQ -et 1d -etr TetraTercet data2 100