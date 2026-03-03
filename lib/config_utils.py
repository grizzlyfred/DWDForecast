import json
import logging
import sys
from types import SimpleNamespace

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

def extract_main_config(config):
    """
    Extract all main config values as a dictionary, including PVLIB config, from the config JSON.
    Returns a dict with all needed values for the main script.
    """
    return {
        'station': config['DWD']['DWDStation'],
        'urlpath': config['DWD']['DWDStationURL'],
        'pv': config['SolarSystem'],
        'sleeptime': config['Processing']['Sleeptime'],
        'print_output': config['Output']['PrintOutput'],
        'csv_output': config['Output']['CSVOutput'],
        'db_output': config['Output']['DBOutput'],
        'db_user': config['Output']['DBUser'],
        'db_password': config['Output']['DBPassword'],
        'db_host': config['Output']['DBHost'],
        'db_name': config['Output']['DBName'],
        'db_port': config['Output']['DBPort'],
        'db_table': config['Output']['DBTable'],
        'csv_file_candidates': get_csv_file_candidates(config),
        'logging': config.get('Logging', {})
    }

class ConfigAccessor:
    def __init__(self, config_dict):
        self._data = self._to_namespace(config_dict)
    def _to_namespace(self, d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: self._to_namespace(v) for k, v in d.items()})
        elif isinstance(d, list):
            return [self._to_namespace(i) for i in d]
        else:
            return d
    def __getattr__(self, item):
        return getattr(self._data, item)
    def __getitem__(self, item):
        return getattr(self._data, item)

def load_config_accessor(config_path='config.json'):
    config = load_config(config_path)
    return ConfigAccessor(config)
