#!/bin/sh

python main.py -i actor --model sql/actor-model.sql --state sql/actor-state.sql
python main.py -i repo --model sql/repo-model.sql --state sql/repo-state.sql
python main.py -i python --model sql/python-repo-model.sql --state sql/python-repo-state.sql
python main.py -i ruby --model sql/ruby-repo-model.sql --state sql/ruby-repo-state.sql
