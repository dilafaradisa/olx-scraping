import luigi
from engine import scrape, parse_html, transform_data, load_data
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

print("Loading .env...")
load_dotenv()
print("KEYWORD:", os.getenv("KEYWORD"))

class Scrape(luigi.Task):
    keyword = luigi.Parameter(default=os.getenv('KEYWORD'))
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))

    def output(self):
        return luigi.LocalTarget(self.html_path)
    
    def run(self):   
        print("=====starting scraping task=====")

        with sync_playwright() as playwright:
            scrape(playwright, self.keyword, self.html_path)
    

class Parse(luigi.Task):
    keyword = luigi.Parameter(default=os.getenv('KEYWORD'))
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))
    parsed_path = luigi.Parameter(default=os.getenv('PARSED_PATH'))
    
    def requires(self):
        return Scrape(keyword=self.keyword, html_path=self.html_path)
    
    def output(self):
        return luigi.LocalTarget(self.parsed_path)
    
    def run(self):
        print('=====starting parsing task=====')
        parse_html(self.html_path, self.parsed_path)

class Transform(luigi.Task):
    keyword = luigi.Parameter(default=os.getenv('KEYWORD'))
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))
    parsed_path = luigi.Parameter(default=os.getenv('PARSED_PATH'))
    transformed_path = luigi.Parameter(default=os.getenv('TRANSFORMED_PATH'))
    
    def requires(self):
        return Parse(
            keyword=self.keyword,
            html_path=self.html_path,
            parsed_path=self.parsed_path
        )
    
    def output(self):
        return luigi.LocalTarget(self.transformed_path)
    
    def run(self):
        print('=====starting transforming task=====')
        transform_data(self.parsed_path, self.transformed_path)

class Load(luigi.Task):
    keyword = luigi.Parameter(default=os.getenv('KEYWORD'))
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))
    parsed_path = luigi.Parameter(default=os.getenv('PARSED_PATH'))
    transformed_path = luigi.Parameter(default=os.getenv('TRANSFORMED_PATH'))
    inserted_path = luigi.Parameter(default=os.getenv('INSERTED_PATH'))
    table_name = luigi.Parameter(default=os.getenv('POSTGRES_TABLE'))
    db_url = luigi.Parameter(default=os.getenv('DB_URL'))
    
    def requires(self):
        return Transform(
            keyword=self.keyword,
            html_path=self.html_path,
            parsed_path=self.parsed_path,
            transformed_path=self.transformed_path
        )
    
    def output(self):
        return luigi.LocalTarget(self.inserted_path)
    
    def run(self):
        print('=====starting loading task=====')
        print(f'using table name: {self.table_name} at {self.db_url}')

        load_data(
            transformed_data=self.transformed_path,
            inserted_path=self.inserted_path,
            table_name=self.table_name,
            db_url=self.db_url
        )

if __name__ == "__main__":
    print("=====running luigi pipeline=====")
    
    luigi.build([Load()], local_scheduler=True)    