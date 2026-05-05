import os
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import logging

load_dotenv()

DOMAIN = "https://www.olx.co.id"
KEYWORD = os.getenv("KEYWORD")
DIR_TEMP_LOG = os.getenv("DIR_TEMP_LOG")
# HTML_PATH = os.getenv("HTML_PATH")
# DETAIL_CSV_PATH = os.getenv("DETAIL_CSV_PATH")

def scrape(playwright, keyword, html_path, csv_path):
    try:
        logging.basicConfig(level = logging.INFO,
                            filename=f'{DIR_TEMP_LOG}/logs.log',
                            format='%(asctime)s - %(levelname)s - %(message)s')
                    
        logging.info("keyword value:", keyword)
        keyword_formatted = keyword.replace(' ', '-')
        url = f"{DOMAIN}/mobil-bekas_c198/q-{keyword_formatted}"
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        browser = playwright.firefox.launch(headless=True, slow_mo=500)
        # context = browser.new_context(
        #     user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        # )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        # page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            logging.info(f"Successfully loaded page: {url}")

            # filter location
            try:
                location_input = 'input[placeholder="Cari kota, area, atau lokalitas"]'
                location_item = "div[data-aut-id='locationItem']"
                
                page.wait_for_selector(location_input, state="visible", timeout=10000)
                page.hover(location_input)
                page.wait_for_timeout(300)
                page.click(location_input)
                page.wait_for_timeout(500)

                page.click(location_input)
                page.fill(location_input, "")
                logging.info(f"Typing location: Indonesia")
                page.type(location_input, "Indonesia", delay=200)
                logging.info(f'Typed Indonesia as a filter')


                item = page.wait_for_selector(location_item, timeout=7000)
                item.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                item.hover()
                page.wait_for_timeout(300)
                item.click()
                page.wait_for_timeout(2000)
                # page.click(location_item)
                # # page.keyboard.press("Enter")
                # page.wait_for_timeout(2000)
            except Exception as e:
                logging.error(f"Location selection failed, proceeding without setting location filter.")

            # scroll until no more load more button
            load_more_button = 'button[data-aut-id="btnLoadMore"]'
            for _ in range(5):
                page.mouse.wheel(0, 3000)
                # page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                page.wait_for_timeout(2000)
                try:
                    button = page.locator(load_more_button)
                    if button.count() > 0:
                        button.click()
                        page.wait_for_timeout(3000)
                    else:
                        break
                except Exception:
                    break

            # get listing urls
            listing = page.locator("li[data-aut-id='itemBox']")
            total_cards = listing.count()
            logging.info("Cards found:", total_cards)

            listing_urls = []
            for i in range(total_cards):
                href = listing.nth(i).locator("a").get_attribute("href")
                if href:
                    listing_urls.append(f"{DOMAIN}{href}")

            detailed_listing_info = []

            # open each listing page
            for target_url in listing_urls[:3]:
                try:
                    p = context.new_page()
                    p.goto(target_url, timeout=45000)
                    logging.info(f"Processing listing: {target_url}")

                    # scroll down
                    p.evaluate("window.scrollBy(0, 600)")
                    p.wait_for_timeout(1500)

                    # get variant
                    variant = "not found"
                    try:
                        container = p.locator("[data-aut-id='carDetailInfo']")
                        if container.count() > 0:
                            variant = container.locator("[data-aut-id='itemTitle'] >> xpath=following-sibling::div[1]").inner_text()
                            logging.info(f"Variant found for {id(target_url)}: {variant}")
                    except Exception as e:
                        logging.error(f"Variant not found for {id(target_url)}: {e}, setting as 'not found'")

                    # get seller type
                    seller_type = "not found"
                    try:
                        overview = p.locator("[data-aut-id='overviewDetails']")
                        if overview.count() > 0:
                            seller_type = overview.locator('div:text-is("penjual") + div').inner_text()
                            logging.info(f"Seller type found for {id(target_url)}: {seller_type}")
                    except Exception as e:
                        logging.info(f"Seller type not found for {id(target_url)}: {e}, setting as 'not found'")

                    # get description
                    description = "not found"
                    try:
                        desc_container = p.locator("[data-aut-id='descriptionDetails']")

                        if desc_container.count() > 0:
                            desc_container.scroll_into_view_if_needed()
                            p.wait_for_timeout(1000)

                            see_more_btn = desc_container.locator("[data-aut-id='seeMoreButtonDescription']")

                            if see_more_btn.is_visible():
                                logging.info("Clicking 'Selengkapnya' button...")

                                see_more_btn.dispatch_event("click")
                                p.wait_for_timeout(3000)

                                modal_selector = "[data-aut-id='modalDescriptionContent']"
                                p.wait_for_selector(modal_selector, state="visible", timeout=5000)

                                description = p.locator(modal_selector).inner_text()
                                logging.info(f"Description extracted for {id(target_url)}")

                                p.keyboard.press("Escape")
                                p.wait_for_timeout(500)

                            else:
                                inline_desc = p.locator("[data-aut-id='itemDescriptionContent']")
                                if inline_desc.is_visible():
                                    description = inline_desc.inner_text()

                    except Exception as e:
                        logging.error(f"Description error for {target_url}: {e}")

                    data = {
                        "url": target_url,
                        "variant": variant,
                        "seller_type": seller_type,
                        "description": description
                    }
                    logging.info(f"Data collected for {id(target_url)}")
                
                    detailed_listing_info.append(data)
                    p.close()

                except Exception as e:
                    logging.error(f"Error while processing {target_url}: {e}")

            # save detailed listing into csv
            df = pd.DataFrame(detailed_listing_info)
            df.to_csv(csv_path, index=False)
            logging.info(f"Detailed listing info saved to {csv_path}")

            # save HTML of the main search page
            html_content = page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"HTML content saved to {html_path}")

        except Exception as e:
            logging.error(f"Error during scraping: {e}")
            raise
        finally:
            browser.close()

    except Exception as e:
        logging.error(f"Error in scrape function: {e}")
        raise

# keyword = "Wuling Air EV"
# html_save_path = "output/search_results.html"
# csv_save_path = "output/detailed_listings.csv"

# def main():
#     with sync_playwright() as playwright:
#         scrape(playwright, KEYWORD, html_path=html_save_path, csv_path=csv_save_path)

# if __name__ == "__main__":
#     main()