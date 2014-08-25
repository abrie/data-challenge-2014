## Methodology and Source

At the heart of this plot are the SQL (or rather, BQL) queries sent to Google Bigquery. The query files are found in [`sql/`](https://github.com/abrie/data-challenge-2014/tree/master/sql). The queries consist of two types: a [model query](https://github.com/abrie/data-challenge-2014/blob/master/sql/repo-model.sql) and [state query](https://github.com/abrie/data-challenge-2014/blob/master/sql/repo-state.sql). The model query builds the raw markov matrix by measuring transition ratios between adjacent events. The state query computes a census of the most-recent events. These two sets of data are then ["munged"](http://en.wikipedia.org/wiki/Data_wrangling) by [`munge.py`](https://github.com/abrie/data-challenge-2014/blob/master/munger.py). The munged data is passed through a [cluster detection algorithm](http://micans.org/mcl/). The results are gathered into a single JSON structure (example:[results.json](https://github.com/abrie/data-challenge-2014/blob/gh-pages/data/repo/results.json)), which is used by the [front end](https://github.com/abrie/data-challenge-2014/blob/master/pages/main.js). The frontend employs SVG via  [D3js](http://d3js.org).

## Installation of dependencies

This application uses [MCL](http://micans.org/mcl/). The source is contained in the `external/` directory. Install as follows:

- `tar xfz mcl-latest.tar.gz`
- ``configure --prefix=`pwd```
- `make`
- `make install`

MCL will then be installed to `external/mcl-14-137` which is where the application will assume it to be. If you install to a different path, then change the `MCL_BIN` string found in `mclinterface.py`.
 
## Authorization of APIs

This application uses Google Bigquery. You'll need to supply authenticated credentials:

- [ ] Log into [Google Developer Console](https://console.developers.google.com/)
- [ ] Navigate to the [project list](https://console.developers.google.com/project)
- [ ] Create a new project. (Or use one you may have previously created :)
- [ ] Enable the BigQuery API: Select Project -> APIs and Auth -> API's -> BigQuery
- [ ] Generate a client_secrets JSON -> API's and Auth -> Credentials -> Create New Client ID
- [ ] Download the generated JSON and save as `client_secrets.json` to the root of this project.
- [ ] When you run the app a browser window will open and request authorization.
- [ ] Authorize it.

## Collecting and munging data

[`main.py`](https://github.com/abrie/data-challenge-2014/blob/master/main.py) contains the data collection logic. Here is an example:

`python main.py -i firstquery --model sql/repo-model.sql --state sql/repo-state.sql`

- `-i [id]` is an optional parameter. Use it to manually set the ID for query results. Omit it and a random ID will be generated.
- `-p [projectId]` this is the unique projectId number associated with the BigQuery project, (ex: 'spark-mark-911')
- `--model [sql]` specifies the query used to generate the markov model.
- `--state [sql]` specifies the query used to generate the population table.

Emitted output is recorded in the data/[id] directory. Within it will be the raw queries, the query results, and a results.json file which contains all the munged data.

## Scripts

Two scripts are provided which automate the collection and generator processes. They must be run sequentially:

- `collect.sh` runs queries and munges the data. You'll need to specify a projectId. For example: `./collect.sh gilded-toad-681`
- `deploy.sh` will use collected data and generate presentable html. This is what is used to make the [gh-pages content](http://abrie.github.io/data-challenge-2014).

## Citations
- Stijn van Dongen, Graph Clustering by Flow Simulation. PhD thesis, University of Utrecht, May 2000. [link](http://micans.org/mcl/lit/svdthesis.pdf.gz)

## Contact
abrhie@gmail.com
