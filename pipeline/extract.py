import luigi
from datetime import datetime
import time
import pandas as pd
import os
from dotenv import load_dotenv
from pipeline.utils.scrape_sync import scrape
# from pipeline.utils.scrape_selenium import scrape
from playwright.sync_api import sync_playwright


load_dotenv()
KEYWORD = os.getenv("KEYWORD")
HTML_PATH = os.getenv("HTML_PATH")
DETAIL_CSV_PATH = os.getenv("CSV_PATH")

class ExtractData(luigi.Task):
    """
    scrape data from olx.co.id based on given keyword and save the html and csv file to local directory.
    """
    keyword = luigi.Parameter(default=KEYWORD)
    html_path = luigi.Parameter(default=HTML_PATH)
    detail_csv_path = luigi.Parameter(default=DETAIL_CSV_PATH)

    def requires(self):
        pass

    def run(self):
        with sync_playwright() as playwright:
            scrape(playwright, self.keyword, self.html_path, self.detail_csv_path)
        # scrape(self.keyword, self.html_path, self.detail_csv_path)

    def output(self):
        return [luigi.LocalTarget(self.html_path),
                luigi.LocalTarget(self.detail_csv_path)]

# if __name__ == "__main__":
#     print("==========running luigi pipeline==========")
    
#     luigi.build([ExtractData()], local_scheduler=True)    