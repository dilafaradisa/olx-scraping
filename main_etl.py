import luigi
import os
from dotenv import load_dotenv
# from pipeline.extract import ExtractData
# from pipeline.transform import ParseData, TransformData
from pipeline.load import LoadData
from pipeline.utils.delete_temp_data import delete_temp

load_dotenv()

DIR_TEMP_DATA = os.getenv("DIR_TEMP_DATA")

if __name__ == "__main__":
    print("===========running luigi pipeline===========")

    delete_temp(DIR_TEMP_DATA)
    
    luigi.build([LoadData()], 
                local_scheduler=True)
    
