import luigi
import os
from dotenv import load_dotenv
from pipeline.extract import ExtractData
from pipeline.utils.parse_html import parse_html
from pipeline.utils.transform_data import transform_data

load_dotenv()

class ParseData(luigi.Task):
    keyword = luigi.Parameter(default=os.getenv('KEYWORD'))
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))
    detail_csv_path = luigi.Parameter(default=os.getenv('DETAIL_CSV_PATH'))
    parsed_path = luigi.Parameter(default=os.getenv('PARSED_PATH'))
    
    def requires(self):
        return ExtractData(keyword=self.keyword, html_path=self.html_path, detail_csv_path=self.detail_csv_path)
    
    def output(self):
        return luigi.LocalTarget(self.parsed_path)
    
    def run(self):
        parse_html(html_data=self.html_path, 
                   parsed_path=self.parsed_path)

        
        
class TransformData(luigi.Task):
    detail_csv_path = luigi.Parameter(default=os.getenv('DETAIL_CSV_PATH'))
    parsed_path = luigi.Parameter(default=os.getenv('PARSED_PATH'))
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))
    transform_data_path = luigi.Parameter(default=os.getenv('TRANSFORMED_PATH'))
    
    def requires(self):
        return ParseData(html_path=self.html_path, parsed_path=self.parsed_path)
    
    def output(self):
        return luigi.LocalTarget(self.transform_data_path)
    
    def run(self):
        transform_data(parsed_data=self.parsed_path, 
                       detail_listing_path=self.detail_csv_path, 
                       transformed_path=self.transform_data_path)
        