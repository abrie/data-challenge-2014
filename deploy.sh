#!/bin/sh
DEST="ghpages"
rm -rf $DEST
mkdir -p $DEST/data

cp -R lib $DEST
cp pages/main.js $DEST
cp pages/style.css $DEST

python pages/make_page.py -t pages/page.template -d pages/descriptions/actor.html -i actor -o $DEST/actor.html
cp -R data/actor $DEST/data/

python pages/make_page.py -t pages/page.template -d pages/descriptions/index.html -i repo -o $DEST/index.html
cp -R data/repo $DEST/data/

python pages/make_page.py -t pages/page.template -d pages/descriptions/python.html -i python -o $DEST/python.html
cp -R data/python $DEST/data/

python pages/make_page.py -t pages/page.template -d pages/descriptions/ruby.html -i ruby -o $DEST/ruby.html
cp -R data/ruby $DEST/data/
