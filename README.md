## Extended Feature Branch

This branch contains significant features not completed before the contest submission deadline.

- A display of the computed "stationary" population with small cross bars along the population line. They represent the Markov Equilibrium population, and could be interpreted as a clue to which direction the populations are expected to move. This makes some naive assumptions, and the author's (abrie) understanding of these mathematics are a bit clumsy. Interpret them with accordingly...  ![stationary populations](https://raw.githubusercontent.com/abrie/data-challenge-2014/master/README_assets/new_1.png)

## Results

See here: [Bundled-Edged Views of the Github Event Graph](http://abrie.github.io/data-challenge-2014)

## Methodology and Source

At the heart of this plot are the SQL (or rather, BQL) queries sent to Google Bigquery. The query files are found in [`sql/`](https://github.com/abrie/data-challenge-2014/tree/master/sql). The queries consist of two types: a [model query](https://github.com/abrie/data-challenge-2014/blob/master/sql/repo-model.sql) and [state query](https://github.com/abrie/data-challenge-2014/blob/master/sql/repo-state.sql). The model query builds the raw markov matrix by measuring transition ratios between adjacent events. The state query computes a census of the most-recent events. These two sets of data are then ["munged"](http://en.wikipedia.org/wiki/Data_wrangling) by [`munge.py`](https://github.com/abrie/data-challenge-2014/blob/master/munger.py). The munged data is passed through a [cluster detection algorithm](http://micans.org/mcl/). The results are gathered into a single JSON structure (example:[results.json](https://github.com/abrie/data-challenge-2014/blob/gh-pages/data/repo/results.json)), which is used by the [front end](https://github.com/abrie/data-challenge-2014/blob/master/pages/main.js). The frontend employs SVG via  [D3js](http://d3js.org).

## Installation of dependencies

This application uses [MCL](http://micans.org/mcl/). The source is contained in the `external/` directory. Install as follows:

- `tar xfz mcl-latest.tar.gz`
- ``configure --prefix=`pwd```
- `make`
- `make install`

MCL will then be installed to `external/mcl-14-137` which is where the application will assume it to be. If you install to a different path, then change the `MCL_BIN` string found in `mclinterface.py`.

Numpy/Scipy are also required. If you're using Mavericks, use this: [ScipySuperpack](https://github.com/fonnesbeck/ScipySuperpack). 
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

`python main.py -i identifier -q bigquery-id model:model.sql state:state.sql`

- `-i [setId]` This identifies the set. The query results will be stored in a folder named data/[setId]. If no query is specified using -q, then the most recent queries in this folder will be (re)munged. 
- `-q [projectId] [name:sql name2:sql2] ...` projectId is a BigQuery project number (ex: 'spark-mark-911'). The [name:sql] entries specify sql files and the id to use when storing the results. Each of the sql files will be sent to BigQuery, and the results stored under `data/[setId]/[name]`. The munger will subsequently process them to produce `results.json`. 

## Scripts

[collect.sh](https://github.com/abrie/data-challenge-2014/blob/master/collect.sh) demonstrates the use of `main.py`. It is the same script used to generate the results used by [this page](http://abrie.github.io/data-challenge-2014). If you wish watch it operate:

`./collect.sh [projectId]` You'll need to specify a projectId obtained from your google developer console. 

[deploy.sh](https://github.com/abrie/data-challenge-2014/blob/master/deploy.sh) generates the presentation pages and writes them to the specified directory. It assumes that the collect.sh script has been sucessfully run. Once generated, the site should be served through a webserver. This is because the `results.json` file is loaded through Ajax. [node http-server](https://github.com/nodeapps/http-server) is easy and recommended. Example of use:

- `./deploy.sh path/to/dir`
- `http-server -c-1 path/to/dir`
- Navigate to http://localhost:8080

## Citations
- Stijn van Dongen, Graph Clustering by Flow Simulation. PhD thesis, University of Utrecht, May 2000. [link](http://micans.org/mcl/lit/svdthesis.pdf.gz)

## Contact
abrhie@gmail.com

## Addendum

These images show the evolution from very hairball, to less hairball, to combed hairball.

![first](https://raw.githubusercontent.com/abrie/data-challenge-2014/master/README_assets/2.png)
![second](https://raw.githubusercontent.com/abrie/data-challenge-2014/master/README_assets/3.png)
![third](https://raw.githubusercontent.com/abrie/data-challenge-2014/master/README_assets/1.png)
