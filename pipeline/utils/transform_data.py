import pandas as pd
import re
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import csv
import logging

load_dotenv()

DOMAIN = os.getenv("DOMAIN")
DIR_TEMP_LOG = os.getenv("DIR_TEMP_LOG")

def extract_year_mileage(data):
    if pd.isna(data) or data == "Data tidak ditemukan":
        return None, None, None
        
    data_str = str(data).strip().lower()
    if ' - ' not in data:
        return None, None, None
      
    year, km_text = data_str.split(" - ", 1)
    km_text = km_text.replace(' km', '').replace('.', '').strip()
    if '-' in km_text:
        lower_km, upper_km = km_text.split('-', 1)
    else:
        lower_km = upper_km = km_text.strip()
        
    return year, lower_km, upper_km

def transform_installment(value):
    if pd.isna(value) or value == 'not found':
        return None
        
    numbers = re.findall(r'\d+', str(value).replace('.', ''))
    if numbers:
        return float(numbers[0]) * 1000000 
    return None

def transform_posted_time(value):
    value = str(value).lower()

    if 'hari ini' in value:
        date = datetime.now()
        return date.strftime('%d %b')
        
    if 'kemarin' in value:
        date = datetime.now() - timedelta(days=1)
        return date.strftime('%d %b')
        
    if len(value) > 7:
        day = re.search(r'(\d+)', value)
        if day:
            day_num = int(day.group(1))
            date = datetime.now() - timedelta(days=day_num)
            return date.strftime('%d %b')
        return None # if there no number found
                
    return value


def transform_data(parsed_data, detail_listing_path,transformed_path):
    '''this function transforms parsed data based on given requirements'''

    logging.basicConfig(level = logging.INFO,
                        filename=f'{DIR_TEMP_LOG}/logs.log',
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
    os.makedirs(os.path.dirname(transformed_path), exist_ok=True)

    df = pd.read_csv(parsed_data)
    df_detail = pd.read_csv(detail_listing_path)

    # cleansing price column
    df['price'] = df.price.str.extract(r'(\d+[.\d]*)')
    df['price'] = df['price'].str.replace('.', '').astype(float)

    # transform years_mileage column to separate year, lower_km, upper_km
    df[['year', 'lower_km', 'upper_km']] = df['year_mileage'].apply(
        lambda x: pd.Series(extract_year_mileage(x))
    )
    df = df.drop(columns=['year_mileage'])

    # enrich listing url column
    df['listing_url'] = DOMAIN + df['listing_url']

    # cleansing location column
    df['location'] = df['location'].str.replace('"', '')

    # cleansing installment column
    df['installment'] = df['installment'].apply(transform_installment)

    # transform posted_time column, max character 7
    df['posted_time'] = df['posted_time'].apply(transform_posted_time)

    # merge with detail listing data
    df_merged = pd.merge(df, df_detail, left_on='listing_url', right_on='url', how='left')
    df_merged = df_merged.drop(columns=['url'])
    df_merged['description'] = df_merged['description'].replace(',', ' ')
    df_merged['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    df_merged.to_csv(transformed_path, index=False, quoting=csv.QUOTE_ALL)

    logging.info(f"Transformed data saved to {transformed_path}")