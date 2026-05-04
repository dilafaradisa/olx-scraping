import os
import glob

def delete_temp(directory):
    try:
        # Delete all files in the temp directory
        files = os.listdir(directory)
        
        for file in files:
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                print(f"Deleting file: {file_path}")
                os.remove(file_path)
        
        # Delete Luigi task marker files and intermediate data to force re-execution
        marker_files = [
            'data/raw/scraped_data.html',
            'data/raw/scraped_detailed_listing_data.csv',
            'data/parsed/parsed_data.csv',
            'data/transformed/transformed_data.csv',
        ]
        
        # Delete load_complete_*.txt files
        for load_file in glob.glob('data/inserted/load_complete_*.txt'):
            if os.path.isfile(load_file):
                print(f"Deleting marker file: {load_file}")
                os.remove(load_file)
        
        # Delete other marker files
        for marker in marker_files:
            if os.path.isfile(marker):
                print(f"Deleting marker file: {marker}")
                os.remove(marker)

    except Exception as e:
        print(f"An error occurred: {e}")