#!/bin/sh
if [ $# -lt 1 ] ; then
    echo "need projectId, please." ; exit 0
fi

PROJECTID=$1
python main.py -p $PROJECTID -i actor --model sql/actor-model.sql --state sql/actor-state.sql
python main.py -p $PROEJCTID -i repo --model sql/repo-model.sql --state sql/repo-state.sql
python main.py -p $PROJECTID -i python --model sql/python-repo-model.sql --state sql/python-repo-state.sql
python main.py -p $PROJECTID -i ruby --model sql/ruby-repo-model.sql --state sql/ruby-repo-state.sql
python main.py -p $PROJECTID -i dcpu16 --model sql/dcpu16-repo-model.sql --state sql/dcpu16-repo-state.sql
python main.py -p $PROJECTID -i friday --model sql/friday-repo-model.sql --state sql/friday-repo-state.sql
python main.py -p $PROJECTID -i sunday --model sql/sunday-repo-model.sql --state sql/sunday-repo-state.sql
