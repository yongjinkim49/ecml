
# Parallel diversification with ETR
python hpo_runner.py -rc p6dic-etr.json -m BATCH -s ASYNC -et 30h data207 100
python hpo_runner.py -rc p6dic-etr.json -m BATCH -s ASYNC -et 4h data10 100
python hpo_runner.py -rc p6dic-etr.json -m BATCH -s ASYNC -et 4h data20 100
python hpo_runner.py -rc p6dic-etr.json -m BATCH -s ASYNC -et 4h data2 100
python hpo_runner.py -rc p6dic-etr.json -m BATCH -s ASYNC -et 4h data3 100
python hpo_runner.py -rc p6dic-etr.json -m BATCH -s ASYNC -et 4h data30 100


