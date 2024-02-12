# Spothinta

## Short description

- The goal of the project as whole is to simply create a graphical representation of Finnish electricity day ahead spot prices to be displayed on a website.

## Backend

The backend (Python v3.9+) requests the data from Entso-E (European Network of Transmission System Operators for Electricity) API in XML format and parses the data to both: Parquet database and JSON file. The latter is then used by the frontend.  

The backend contains functions for creating the database, but is specifically build to automatically update the already existing local data on runtime.  

The day ahead prices are typically released around 14.00 EET/EEST for when the execution of entso_e.py needs to be scheduled. Cron and shell scripts will do the job, but they need to be set manually. The time of releasing data may vary, so it's generally good to run the update f.e. in 15 minute intervals from 14.00 onwards for app. 2 hours.

## Frontend

- Frontend (HTML, CSS, PHP, JavaScript). PHP to read and truncate the JSON data and JavaScript to graph it. 

## Dependencies

- Python
    - requests (http request)
    - datetime (parsing and conversion of datetime)
    - pytz (time zones)
    - re (regular expressions)
    - Beautiful Soup (parsing xml files)
    - Polars (handling the parsed data)
    - json (reading and writing JSON files)
