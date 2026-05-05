import luigi
import os
from dotenv import load_dotenv
# from pipeline.extract import ExtractData
# from pipeline.transform import ParseData, TransformData
from pipeline.load import LoadData
from pipeline.utils.delete_temp_data import delete_temp
from pipeline.utils.copy_log import copy_log

load_dotenv()

DIR_TEMP_DATA = os.getenv("DIR_TEMP_DATA")
DIR_TEMP_LOG = os.getenv("DIR_TEMP_LOG")
DIR_LOG = os.getenv("DIR_LOG")

if __name__ == "__main__":
    print("===========running luigi pipeline===========")

    delete_temp(DIR_TEMP_DATA)
    
    luigi.build([LoadData()], 
                local_scheduler=True)
    
    copy_log(source_file=f'{DIR_TEMP_LOG}/logs.log', destination_file=f'{DIR_LOG}/logs.log')

    print("===========finished luigi pipeline===========")
    
