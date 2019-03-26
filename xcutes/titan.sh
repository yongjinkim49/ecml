python hpo_runner.py -m SOBOL -s RANDOM -et 1d data3 100
# Sequential BO + donham15 (no fantasy use)
python hpo_runner.py -m RF -s EI -et 1d -etr Donham15 data3 100
python hpo_runner.py -m RF -s PI -et 1d -etr Donham15 data3 100
python hpo_runner.py -m RF -s UCB -et 1d -etr Donham15 data3 100
python hpo_runner.py -m DIV -s SEQ -et 1d -etr Donham15 data3 100
# Sequential BO + donham15 (fantasy use)
python hpo_runner.py -m RF -s EI -et 1d -etr Donham15Fantasy data3 100
python hpo_runner.py -m RF -s PI -et 1d -etr Donham15Fantasy data3 100
python hpo_runner.py -m RF -s UCB -et 1d -etr Donham15Fantasy data3 100
python hpo_runner.py -m DIV -s SEQ -et 1d -etr Donham15Fantasy data3 100
# Sequential BO + donham15 (no fantasy use)
python hpo_runner.py -m GP -s EI -et 1d -etr Donham15Fantasy data3 100
python hpo_runner.py -m GP -s PI -et 1d -etr Donham15Fantasy data3 100
python hpo_runner.py -m GP -s UCB -et 1d -etr Donham15Fantasy data3 100
# Sequential BO + donham15 (fantasy use)
python hpo_runner.py -m GP -s EI -et 1d -etr Donham15 data3 100
python hpo_runner.py -m GP -s PI -et 1d -etr Donham15 data3 100
python hpo_runner.py -m GP -s UCB -et 1d -etr Donham15 data3 100