# Parallel diversification with ETR
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9334 -et 30h data207 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.8994 -et 4h data10 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.784 -et 4h data20 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9933 -et 4h data2 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.9922 -et 4h data3 100
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -e GOAL -eg 0.4596 -et 4h data30 100