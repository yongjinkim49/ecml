python hpo_runner.py -m DIV -s SEQ -et 1d -e GOAL -eg 0.8994 -etr DecaTercet data10 100
python hpo_runner.py -m DIV -s SEQ -e GOAL -et 1d -eg 0.9933 -etr DecaTercet data2 100
python hpo_runner.py -m DIV -s SEQ -e GOAL -et 1d -etr DecaTercet data207 100

python hpo_runner.py -m DIV -s SEQ -e GOAL -et 1d -etr PentaTercet data207 100
python hpo_runner.py -m DIV -s SEQ -e GOAL -e GOAL -eg 0.8994 -et 1d -etr PentaTercet data10 100
python hpo_runner.py -m DIV -s SEQ -e GOAL -eg 0.9933 -et 1d -etr PentaTercet data2 100


