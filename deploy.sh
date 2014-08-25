#!/bin/sh
rm -rf ghpages
mkdir -p ghpages/data

cp -R lib ghpages
cp main.js ghpages
cp style.css ghpages

python generate.py -d templates/actor.html -i actor -o ghpages/actor.html
cp -R data/actor ghpages/data/

python generate.py -d templates/index.html -i repo -o ghpages/index.html
cp -R data/repo ghpages/data/

python generate.py -d templates/python.html -i python -o ghpages/python.html
cp -R data/python ghpages/data/

python generate.py -d templates/ruby.html -i ruby -o ghpages/ruby.html
cp -R data/ruby ghpages/data/
