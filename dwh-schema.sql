-- CREATE TABLE FOR LOAD THE DATA FROM SCRAPING PROCESS

CREATE TABLE IF NOT EXISTS scrape_data (
    uuid SERIAL PRIMARY KEY,
    title varchar,
    price float8,
    listing_url varchar NOT NULL,
    location varchar,
    installment float8,
    posted_time varchar,
    year float8,
    lower_km float8,
    upper_km float8,
    created_at timestamp NOT NULL DEFAULT current_timestamp
);