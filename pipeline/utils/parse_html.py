import pandas as pd
from bs4 import BeautifulSoup
import re
import os

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