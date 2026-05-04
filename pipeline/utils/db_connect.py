from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')
import os
from dotenv import load_dotenv

load_dotenv()

def dwh_db_connection():
    try:
        # database = os.getenv("OSTGRES_DB")
        # host = os.getenv("DWH_POSTGRES_HOST")
        # user = os.getenv("DWH_POSTGRES_USER")
        # password = os.getenv("DWH_POSTGRES_PASSWORD")
        # port = os.getenv("DWH_POSTGRES_PORT")
        db_url = os.getenv("DB_URL")

        # conn_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        engine = create_engine(db_url)
        print("DWH DB connected successfully")
        return engine

    except Exception as e:
        print("Error connecting to DWH DB")
        print(e)
        return None