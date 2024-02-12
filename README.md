# Spothinta

## Short description

The goal of the project as whole is to simply create a graphical representation of Finnish electricity day ahead spot prices to be displayed on a website. Earlier implemenation of the project can be viewed in [spothinta](https://truelemmings.fi/spothinta), albeit with a different folder structure.

## Backend

The backend (Python v3.9+) requests the data from Entso-E (European Network of Transmission System Operators for Electricity) API in XML format and parses the data to both: Parquet database and JSON file. The latter is then used by the frontend.  

The backend contains functions for initiating and updating the database, but for now, at runtime is build to just update the already existing local database. Command line interface might be added later to encapsulate all of the functionality, but it seems somewhat redundant since initiating the database needs to be done only once and initiated database is already included here.

New day ahead prices are typically released daily around 14.00 EET/EEST, for when the execution of entso_e.py needs to be scheduled. The scheduling is system dependent and needs to be set manually. E.g. via Cron and shell scripting in Unix systems. Time of the daily data release may vary, so it's generally good to schedule the update to run f.e. in 15 minute intervals from 14.00 onwards for about 2-3 hours. The script will refrain itself from sending unnecessary requests to Entso-E if local data is already up to date.

## Frontend

Frontend (HTML, CSS, PHP, JavaScript). PHP to read and truncate the JSON data and JavaScript to graph it. 

## Dependencies

### Python
- requests (http request)
- datetime (parsing and conversion of datetime)
- pytz (time zones)
- re (regular expressions)
- Beautiful Soup (parsing xml files)
- Polars (handling the parsed data)
- json (reading and writing JSON files)
