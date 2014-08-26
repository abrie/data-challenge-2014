#!/bin/sh
DEST="ghpages"
rm -rf $DEST
mkdir -p $DEST/data

cp -R pages/lib $DEST
cp pages/main.js $DEST
cp pages/page.css $DEST

python pages/make_page.py -t pages/page.html -d pages/descriptions/actor.html -i actor -o $DEST/actor.html
cp -R data/actor $DEST/data/

python pages/make_page.py -t pages/page.html -d pages/descriptions/repo.html -i repo -o $DEST/index.html
cp -R data/repo $DEST/data/

python pages/make_page.py -t pages/page.html -d pages/descriptions/python.html -i python -o $DEST/python.html
cp -R data/python $DEST/data/

python pages/make_page.py -t pages/page.html -d pages/descriptions/ruby.html -i ruby -o $DEST/ruby.html
cp -R data/ruby $DEST/data/

python pages/make_page.py -t pages/page.html -d pages/descriptions/dcpu16.html -i dcpu16 -o $DEST/dcpu16.html
cp -R data/dcpu16 $DEST/data/

python pages/make_page.py -t pages/page.html -d pages/descriptions/sunday-repo.html -i sunday -o $DEST/sunday-repo.html
cp -R data/sunday $DEST/data/

python pages/make_page.py -t pages/page.html -d pages/descriptions/friday-repo.html -i friday -o $DEST/friday-repo.html
cp -R data/friday $DEST/data/
