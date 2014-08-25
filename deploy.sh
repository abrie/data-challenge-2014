#!/bin/sh
rm -rf ghpages
mkdir -p ghpages/data

cp -R lib ghpages
cp main.js ghpages
cp style.css ghpages

python templates/make_page.py -t templates/page.template -d templates/descriptions/actor.html -i actor -o ghpages/actor.html
cp -vR data/actor ghpages/data/

python templates/make_page.py -t templates/page.template -d templates/descriptions/index.html -i repo -o ghpages/index.html
cp -vR data/repo ghpages/data/

python templates/make_page.py -t templates/page.template -d templates/descriptions/python.html -i python -o ghpages/python.html
cp -vR data/python ghpages/data/

python templates/make_page.py -t templates/page.template -d templates/descriptions/ruby.html -i ruby -o ghpages/ruby.html
cp -vR data/ruby ghpages/data/
