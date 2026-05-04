-- CREATE TABLE FOR LOAD THE DATA FROM SCRAPING PROCESS
CREATE SCHEMA IF NOT EXISTS stg AUTHORIZATION olx_user;

CREATE TABLE IF NOT EXISTS stg.scrape_data (
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
    variant varchar,
    seller_type varchar,
    description text,
    status varchar DEFAULT 'active',
    scraped_at timestamp NOT NULL DEFAULT current_timestamp,
    created_at timestamp NOT NULL DEFAULT current_timestamp
);



