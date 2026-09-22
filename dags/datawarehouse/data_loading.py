import json
from datetime import date
import logging

# Create a module-specific logger so Airflow records messages in task logs instead of stdout.
logger = logging.getLogger(__name__)

# Builds today's raw-extract filename, reads it, and converts its JSON array into Python objects.
def load_data():

    # This must match the date-based filename written by save_to_json() in video_stats.py.
    file_path = f"./data/YT_json_{date.today()}.json"

    try:
        # Record the input file before opening it, making failed Airflow runs easier to diagnose.
        logger.info(f"Processing file: YT_json_{date.today()}.json")

        # The context manager closes the file automatically, including when parsing fails.
        with open(file_path, "r", encoding="utf-8") as raw_data:
            # json.load converts the file's JSON array of video records into a Python list of dictionaries.
            data = json.load(raw_data)
        
        return data

    except FileNotFoundError:

        # Log the full expected path, then re-raise so the calling Airflow task is marked failed.
        logger.error(f"File not found: {file_path}")
        raise 
    
    except json.JSONDecodeError:
        # A malformed or incomplete file cannot be safely loaded, so report and re-raise the error.
        logger.error(f"Invalid JSON file: {file_path}")
        raise
