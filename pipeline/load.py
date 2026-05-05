import luigi
import os
import pandas as pd
import sqlalchemy
import logging
from datetime import datetime
from dotenv import load_dotenv
from pipeline.utils.db_connect import dwh_db_connection
from pipeline.transform import TransformData
from pipeline.utils.read_sql_file import read_sql_file

load_dotenv()

DIR_TEMP_LOG = os.getenv("DIR_TEMP_LOG")

class LoadData(luigi.Task):
    html_path = luigi.Parameter(default=os.getenv('HTML_PATH'))
    parsed_path = luigi.Parameter(default=os.getenv('PARSED_PATH'))
    detail_csv_path = luigi.Parameter(default=os.getenv('DETAIL_CSV_PATH')) 
    transformed_data_path = luigi.Parameter(default=os.getenv('TRANSFORMED_PATH'))
    table_name = luigi.Parameter(default=os.getenv('POSTGRES_TABLE'))
    db_url = luigi.Parameter(default=os.getenv('DB_URL'))
    load_query_path = luigi.Parameter(default=os.getenv('LOAD_QUERY_PATH'))
    
    def requires(self):
        return TransformData(
            html_path=self.html_path,
            parsed_path=self.parsed_path,
            detail_csv_path=self.detail_csv_path,
            transform_data_path=self.transformed_data_path
        )
    
    def output(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return luigi.LocalTarget(f'data/inserted/load_complete_{timestamp}.txt')
    
    def run(self):
        logging.basicConfig(level = logging.INFO,
                            filename=f'{DIR_TEMP_LOG}/logs.log',
                            format='%(asctime)s - %(levelname)s - %(message)s')

        logging.info(f'using table name: {self.table_name} at {self.db_url}')

        try:
            dwh_engine = dwh_db_connection()
        except Exception as e:
            logging.error(f"Error connecting to DWH DB: {e}")
            return
        
        try:
            df = pd.read_csv(self.transformed_data_path)
            with dwh_engine.begin() as conn:
                conn.execute(sqlalchemy.text(f"TRUNCATE TABLE stg.{self.table_name} RESTART IDENTITY"))

                df.to_sql(
                    self.table_name,
                    con=conn,
                    if_exists='append',
                    index=False,
                    schema='stg'
                )
            logging.info(f"Data loaded into {self.table_name} successfully.")

        except Exception as e:
            raise Exception(f"Error loading data into {self.table_name}: {e}")
        
        try:
            load_query = read_sql_file(self.load_query_path)
            with dwh_engine.connect() as connection:
                connection.execute(sqlalchemy.text(load_query))
                connection.commit()

                logging.info("Data loaded into final schema successfully.")

        except Exception as e:
            raise Exception(f"Error in loading data into final schema: {e}")
        
        # Write success marker
        with open(self.output().path, 'w') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"Successfully run at {timestamp}")
        


