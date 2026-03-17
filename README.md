# DWD Forecast Script

## Overview

This script extracts weather forecast data from DWD Mosmix for a given station and processes it for PV system analysis. It has been modernized and modularized in 2026 by Sven Witterstein to improve maintainability and enable easier debugging and extension.

## Usage Modes

### Standard Mode (Default)
- **How to use:** Run the script without any command-line arguments:
  ```
  python dwdforecast.py
  ```
- **Behavior:**
  - Performs a single polling attempt to fetch and process the latest DWD forecast data.
  - Outputs results as configured (CSV, print, database, etc.).
  - Exits after the attempt.

### Server Mode (Polling/Daemon)
- **How to use:** Run the script with any command-line argument(s):
  ```
  python dwdforecast.py --server
  ```
- **Behavior:**
  - Starts a background polling thread that checks for new DWD forecast data at regular intervals (as configured).
  - Suitable for continuous operation or integration as a service.
  - The polling interval and cooldown are configurable in `config.json`.

## Configuration

All configuration is handled via `config.json`. The script no longer uses INI files for runtime configuration. See the `config.json` file for all available options, including:
- DWD station and URL
- PV system parameters
- Output options (CSV, print, database)
- Logging (file path, level)
- Polling interval

**Example:**
```json
{
  "DWD": {
    "DWDStation": "P148",
    "DWDStationURL": "http://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/P148/kml/"
  },
  "SolarSystem": {
    "ModuleName": "...",
    "InverterName": "...",
    ...
  },
  "Output": {
    "CSVOutput": 1,
    "PrintOutput": 1,
    "DBOutput": 0,
    "CSVFile": "output.csv",
    ...
  },
  "Logging": {
    "File": "/tmp/dwd_kml.log",
    "Level": "INFO"
  },
  "Processing": {
    "Sleeptime": 300
  }
}
```

## Modularization

The codebase is now split into logical modules:
- `dwdforecast.py`: Main entry point, handles configuration and orchestration.
- `lib/config_utils.py`: Configuration loading and access.
- `lib/kml_reader.py`: Downloading and parsing DWD KML/KMZ files.
- `lib/data_processing.py`: DataFrame and PVLIB processing.
- `lib/db.py`: Database operations.
- `lib/poller.py`: Polling/threading logic.
- `lib/data_output.py`: Output utilities (CSV, print, etc.).

## Logging

Logging is fully configurable via `config.json`. By default, logs are written to `/tmp/dwd_kml.log`.

## Output Formats

Whenever the script writes a CSV file, it also writes a JSON file (with the same base name) containing the same data in records format. This ensures that both CSV and JSON are always available for downstream use or inspection.

Example: If your output is `output.csv`, you will also get `output.json` in the same directory.

## Notes on Dependencies and Workarounds

### SciPy Chandrupatla Algorithm
If you encounter issues related to `scipy.optimize._chandrupatla` (used internally by SciPy for root-finding and optimization), be aware that some workarounds or patches may be required for certain edge cases or division-by-zero errors. If you experience unexpected errors or warnings from this module, consult the SciPy documentation or consider updating your SciPy installation to the latest version.

If a workaround or patch is applied to your local `scipy.optimize._chandrupatla.py`, please document the change and keep a backup of the original file.

## License

See `LICENSE.md` for details. Original copyright (C) 2020 Kilian Knoll. Modernization and modularization (C) 2026 Sven Witterstein.
