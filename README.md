data-challenge-2014
===================

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
- [ ] Navigate the [project list][https://console.developers.google.com/project)
- [ ] Create a new project or select an existing one.
- [ ] Enable the BigQuery API: Select Project -> APIs and Auth -> API's -> BigQuery
- [ ] Generate a client_secrets JSON -> API's and Auth -> Credentials -> Create New Client ID
- [ ] Download the generated JSON and save as `client_secrets.json` to the root of this project.
- [ ] When you run the app a browser window will open and request authorization.
- [ ] Authorize it.

## Collecting and munging data

`main.py` contains the logic. Here is an example:

`python main.py -i firstquery --model sql/repo-model.sql --state sql/repo-state.sql`

- `-i [id]` is an optional parameter. Use it to manually set the ID for query results. Omit it and a random ID will be generated.
- `-p [projectId]` this is the unique projectId number associated with the BigQuery project, (ex: 'spark-mark-911')
- `--model [sql]` specifies the query used to generate the markov model.
- `--state [sql]` specifies the query used to generate the population table.

Emitted output is recorded in the data/[id] directory. Within it will be the raw queries, the query results, and a results.json file which contains all the munged data.



## Displaying data

`main.js` exposes the gui functions. It uses ajax calls to retrieve the results.json file, so it must be served through a webserver of some description.

## Scripts

Two scripts are provided which automate the collection and generator processes. They must be run sequentially:

- `collect.sh` runs queries and munges the data. You'll need to specify a projectId. For example: `./collect.sh gilded-toad-681`
- `deploy.sh` will use collected data and generate presentable html. This is what is used to make the [gh-pages content](http://abrie.github.io/data-challenge-2014).

## Contact
abrhie@gmail.com
