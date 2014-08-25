data-challenge-2014
===================

## Installation of dependencies

This application uses [MCL](http://micans.org/mcl/). An archived source distribution is in the 3rdparty/ directory. The application expects it to be installed it into 'mcl/' relative to the project root.
 
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
- `--model [sql]` specifies the query used to generate the markov model.
- `--state [sql]` specifies the query used to generate the population table.

Emitted output is recorded in the data/[id] directory. Within it will be the raw queries, the query results, and a results.json file which contains all the munged data.

### Let the script collect it

protip: Use the included `collect.sh` script to collect preset data sets. Or inspect the script to see how the utility works.

## Displaying data

`main.js` and `index.html` expose the gui. Serve them through a local webserver because it uses Ajax to retrieve the results.json file.

### Let the script collect it

protip: There is a script named 'deploy.sh' which will generate serveable pages of the data. This is what is used to make the [gh-pages content](http://abrie.github.io/data-challenge-2014).

## Contact
abrhie@gmail.com
