-- ALTER TABLE final.scrape_data 
-- ADD CONSTRAINT uq_listing_url UNIQUE (listing_url);

INSERT INTO final.scrape_data 
    (title, price, listing_url, location, installment, posted_time, year, 
     lower_km, upper_km, variant, seller_type, description, status)
SELECT 
    title, price, listing_url, location, installment, posted_time, year,
    lower_km, upper_km, variant, seller_type, description, COALESCE(status, 'active')
FROM stg.scrape_data

ON CONFLICT (listing_url) 
DO UPDATE SET
    title = EXCLUDED.title,
    price = EXCLUDED.price,
    location = EXCLUDED.location,
    installment = EXCLUDED.installment,
    posted_time = EXCLUDED.posted_time,
    year = EXCLUDED.year,
    lower_km = EXCLUDED.lower_km,
    upper_km = EXCLUDED.upper_km,
    variant = EXCLUDED.variant,
    seller_type = EXCLUDED.seller_type,
    description = EXCLUDED.description,
    status = 'active',
    updated_at = CASE WHEN 
                    final.scrape_data.title <> EXCLUDED.title
                    OR final.scrape_data.price <> EXCLUDED.price
                    OR final.scrape_data.location <> EXCLUDED.location
                    OR final.scrape_data.installment <> EXCLUDED.installment
                    OR final.scrape_data.posted_time <> EXCLUDED.posted_time
                    OR final.scrape_data.year <> EXCLUDED.year
                    OR final.scrape_data.lower_km <> EXCLUDED.lower_km
                    OR final.scrape_data.upper_km <> EXCLUDED.upper_km
                    OR final.scrape_data.variant <> EXCLUDED.variant
                    OR final.scrape_data.seller_type <> EXCLUDED.seller_type
                    OR final.scrape_data.description <> EXCLUDED.description
                THEN current_timestamp
                ELSE final.scrape_data.updated_at
            END;

-- mark records as 'inactive' if they dont appear in the new scrape
UPDATE final.scrape_data f
SET 
    status = 'inactive',
    updated_at = current_timestamp
WHERE status = 'active'
    AND NOT EXISTS (
        SELECT 1 FROM stg.scrape_data s 
        WHERE s.listing_url = f.listing_url
    );

