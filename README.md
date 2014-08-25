data-challenge-2014
===================

## Installation of Dependencies

This application uses [MCL](http://micans.org/mcl/). An archived source distribution is in the 3rdparty/ directory. The application expects it to be installed it into 'mcl/' relative to the project root.
 
## Authorization of APIs

This application uses Google Bigquery. You'll need to supply authenticated credentials:

- [ ] Log into [Google Developer Console](https://console.developers.google.com/)
- [ ] Create a new project and enable the BigQuery API.
- [ ] Generate a client_secrets file of type "Installed Application".
- [ ] Download the generated file and save as `client_secrets.json` to the root of this project.
- [ ] When you run the app a browser window will open and request authorization.
- [ ] Authorize it.

## Collecting and Munging Data

`main.py` contains the logic. Here is an example:

`python main.py -i firstquery --model sql/repo-model.sql --state sql/repo-state.sql`

- `-i [id]` is an optional parameter. Use it to manually set the ID for query results. Omit it and a random ID will be generated.
- `--model [sql]` specifies the query used to generate the markov model.
- `--state [sql]` specifies the query used to generate the population table.

Emitted output is recorded in the data/[id] directory. Within it will be the raw queries, the query results, and a results.json file which contains all the munged data.

## Displaying Data

`main.js` and `index.html` expose the gui. Serve them through a local webserver because it uses Ajax to retrieve the results.json file.
