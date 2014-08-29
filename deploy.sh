#!/bin/sh

if [ $# -lt 1 ] ; then
    echo "need a destination directory, please."
    echo usage: $0 [path/to/dir]
    exit -1
fi

DEST=$1

mkdir -p $DEST/data

cp -R pages/lib $DEST
cp pages/main.js $DEST
cp pages/page.css $DEST

function deploy {
    if [ $# -lt "2" ]; then
        FILENAME=$1
    else
        FILENAME=$2
    fi

    python pages/make_page.py -t pages/page.html -d pages/descriptions/$1.html -i $1 -o $DEST/$FILENAME.html
    cp -R data/$1 $DEST/data/
}

deploy actor 
deploy repo index 
deploy python-repo
deploy ruby-repo
deploy dcpu16-repo
deploy friday-repo
deploy sunday-repo
