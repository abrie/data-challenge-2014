#!/bin/sh
set -ue

function ctrl_c {
    exit $?
}

trap ctrl_c SIGINT

if [ $# -lt 1 ] ; then
    echo "need projectId, please."
    echo usage: $0 [projectId]
    exit -1
fi

PROJECTID=$1

function collect {
    python main.py -i $1 -q $PROJECTID model:sql/$1-model.sql state:sql/$1-state.sql
    if [ $? != 0 ]; then
        exit $?
    fi
}

collect actor
collect repo
collect python-repo
collect ruby-repo
collect dcpu16-repo
collect friday-repo
collect sunday-repo
