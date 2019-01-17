
# Parallel diversification with ETR
#python hpo_runner.py -m BATCH -s ASYNC -et 20h data207 100
#python hpo_runner.py -rc no_failover.json -m BATCH -s ASYNC -et 20h data207 100
#python hpo_runner.py -m DIV -s SEQ -et 5d -etr IntervalPentaOpt data207 100
# Parallel BO
python hpo_runner.py -rc p6div-etr.json -m BATCH -s ASYNC -et 4h data2 100


