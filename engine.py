import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, MetaData, Table
from dotenv import load_dotenv

load_dotenv()
print("Loading .env...")
load_dotenv()
print("KEYWORD:", os.getenv("KEYWORD"))

DOMAIN = "https://www.olx.co.id"

def scrape(playwright, keyword, html_path):
    try:
        print("keyword value:", keyword)
        keyword_formatted = keyword.replace(' ', '-')
        url = f"{DOMAIN}/mobil-bekas_c198/q-{keyword_formatted}"
        os.makedirs(os.path.dirname(html_path), exist_ok=True)

        # launch chromium browser 
        # browser = playwright.chromium.launch(headless=False, args=["--no-sandbox", "--disable-setuid-sandbox"])
        browser = playwright.webkit.launch(headless=False, slow_mo=1000)

        # open new page and go to OLX indonesia
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            print(f"Successfully loaded page: {url}")

            try:
                location_input = 'input[placeholder="Cari kota, area, atau lokalitas"]'
                location_click = "div[data-aut-id='locationItem']"
                page.fill(location_input, "Indonesia")
                page.wait_for_selector(location_click, timeout=3000)
                page.click(location_click)
            except Exception:
                pass
            
            # available_listing_selector = "span._351MY"

            # scroll to the bottom of the page, click load more button if available, repeat several times
            load_more_button = 'button[data-aut-id="btnLoadMore"]'
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                page.wait_for_timeout(1000)
                try:
                    if page.locator(load_more_button).count() > 0:
                        page.click(load_more_button)
                        page.wait_for_timeout(1500)
                    else:
                        break
                except PlaywrightTimeoutError:
                    print("No more 'Load More' button found. Exiting loop.")
                    break  
            
            # save html content to file
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML content saved to {html_path}")

        except Exception as e:
                print(f"Error during scraping: {e}")
                raise
        finally:
            browser.close()
    except Exception as e:
        print(f"Error in scrape function: {e}")
        raise       

def parse_html(html_data, parsed_path):
    '''this function parses html content to csv file'''
    try:
        with open(html_data, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        listings = soup.find_all('li', attrs={'data-aut-id': 'itemBox'})

        data = []
        for listing in listings:
            # title
            title_element = listing.find('div', attrs={'data-aut-id': 'itemTitle'})
            title = title_element.get_text(strip=True) if title_element else 'not found'

            # price
            price_element = listing.find('span', attrs={'data-aut-id': 'itemPrice'})
            price = price_element.get_text(strip=True) if price_element else 'not found'

            # location and posted time
            location_postedtime_element = listing.find('div', attrs={'data-aut-id': 'itemDetails'})
            location = location_postedtime_element.contents[0].strip() if location_postedtime_element else 'not found'
            posted_time = location_postedtime_element.find('span').text.strip() if location_postedtime_element and location_postedtime_element.find('span') else 'not found'
            
            # year and mileage
            years_mileage_element = listing.find('div', attrs={'data-aut-id': 'itemSubTitle'})
            year_mileage = years_mileage_element.get_text(strip =True) if years_mileage_element else 'not found'

            # listing url
            url_element = listing.find('a', href=True)
            listing_url = url_element['href'] if url_element else 'not found'

            # installment
            installment_element = listing.find('span', string=re.compile(r'cicilan|angsuran|cicil', re.IGNORECASE))
            installment = installment_element.get_text(strip=True) if installment_element else 'not found'

            data.append({
                'title': title,
                'price': price,
                'listing_url': listing_url,
                'location': location,
                'installment': installment,
                'posted_time': posted_time,
                'year_mileage': year_mileage
            })

        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(parsed_path), exist_ok=True)
        df.to_csv(parsed_path, index=False)
        print(f"Parsed data saved to {parsed_path}")

    except Exception as e:
        print(f"An error occurred while parsing HTML: {e}")

def transform_data(parsed_data, transformed_path):
    '''this function transforms parsed data based on given requirements'''

    df = pd.read_csv(parsed_data)

    # cleansing price column
    df['price'] = df.price.str.extract(r'(\d+[.\d]*)')
    df['price'] = df['price'].str.replace('.', '').astype(float)

    # transform years_mileage column to separate year, lower_km, upper_km
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
    
    df[['year', 'lower_km', 'upper_km']] = df['year_mileage'].apply(
        lambda x: pd.Series(extract_year_mileage(x))
    )
    df = df.drop(columns=['year_mileage'])

    # enrich listing url column
    df['listing_url'] = DOMAIN + df['listing_url']

    # cleansing location column
    df['location'] = df['location'].str.replace('"', '')

    # cleansing installment column
    def transform_installment(value):
        if pd.isna(value) or value == 'not found':
            return None
        
        numbers = re.findall(r'\d+', str(value).replace('.', ''))
        if numbers:
            return float(numbers[0]) * 1000000 
        return None
    df['installment'] = df['installment'].apply(transform_installment)

    # transform posted_time column, max character 7
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
    
    df['posted_time'] = df['posted_time'].apply(transform_posted_time)

    os.makedirs(os.path.dirname(transformed_path), exist_ok=True)

    df.to_csv(transformed_path, index=False)
    print(f"Transformed data saved to {transformed_path}")

def load_data(transformed_data, inserted_path, table_name, db_url):
    '''this function loads transformed data to database'''
    
    os.makedirs(os.path.dirname(inserted_path), exist_ok=True)

    try:
        engine = create_engine(db_url)
        conn = engine.connect()

        metadata = MetaData()
        metadata.reflect(bind=engine)

        df = pd.read_csv(transformed_data)

        records = df.to_dict('records')

        table = metadata.tables.get(table_name)
        if table is None:
            raise ValueError(f"Table '{table_name}' does not exist in the database.")
        
        try:
            conn.execute(table.insert(), records)
            conn.commit()
            print(f"Successfully inserted {len(records)} records into {table_name}")

            os.makedirs(os.path.dirname(inserted_path), exist_ok=True)

            with open(inserted_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            print(f"Inserted data saved to: {inserted_path}")
            
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Database insertion failed: {str(e)}")
        
        finally:
            conn.close()
            engine.dispose()
            
    except Exception as e:
        raise RuntimeError(f"Load data failed: {str(e)}")