import json
import logging
import sys

def load_config(config_path='config.json'):
    """
    Load and validate the JSON config file. Exit on error.
    Returns the config dict.
    """
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except Exception as e:
        print(f"[dwdforecast] ERROR: Invalid {config_path}: {e}")
        logging.error("Invalid %s: %s", config_path, e)
        sys.exit(1)

def get_csv_file_candidates(config):
    """
    Return a list of CSV output paths from config, supporting both string and list.
    """
    csv_file_config = config['Output']['CSVFile']
    if isinstance(csv_file_config, list):
        return csv_file_config
    else:
        return [csv_file_config]

