# OLX Car Scraper 🚗
A simple Python scraper that grabs car listings from OLX Indonesia, then saves them into CSV or JSON.  
Just a fun little project I did during bootcamp in pacmann.ai

## What’s this for?
This tool helps you to scrape many listings in OLX, extract info like title, price, location, and turn it into structured data (CSV or JSON). Ideal if you want to do analysis or build something on top of the data.

## How to start

### Setting Up Virtual Environment (venv)
```bash
python3 -m venv your_project
source your_project/bin/activate
```
### Installing the requirements
`
pip install -r requirements.txt
`
### Create your .env
create a .env file in the project root to store all credential informations
`
touch .env
`
here is the example:
```bash
# --- PostgreSQL Settings ---
POSTGRES_USER=[your_username]
POSTGRES_PASSWORD=[your_password]
POSTGRES_DB=[your_db_name]
POSTGRES_PORT=5433

# Connection string for inserting data into PostgreSQL
DB_URL=postgresql://your_username:your_password@localhost:5433/your_db_name
POSTGRES_TABLE=your_table_name

# --- Scraper Settings ---
KEYWORD="your keyword here"
HTML_PATH=[your_html_path]
PARSED_PATH=[your_parsed_csv_path]
TRANSFORMED_PATH=[your_transformed_csv_path]
INSERTED_PATH=[your_inserted_json_path]
```

### Set up the database
start the docker-compose
`
docker-compose up -d
`
to create the table based on dwh-schema.sql, first access the container, then log in to postgresql inside the container
```bash
docker exec -it your_container_name bash

# inside the container
psql -d scrape_olx -U olx_user -h localhost -p 5433 -f dwh-schema.sql
```
### Run the pipeline
`
python scraps.py
`
## Author
Adila Zahra Faradisa

Feel free to connect with me on
[LinkedIn](https://www.linkedin.com/in/adila-zahra-faradisa/)
