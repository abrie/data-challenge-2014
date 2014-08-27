#!/bin/sh
if [ $# -lt 1 ] ; then
    echo "need projectId, please." ; exit 0
fi

PROJECTID=$1

function collect {
    python main.py -i $1 -q $PROJECTID model:sql/$1-model.sql state:sql/$1-state.sql
}

collect actor
collect repo
collect python-repo
collect ruby-repo
collect dcpu16-repo
collect friday-repo
collect sunday-repo
