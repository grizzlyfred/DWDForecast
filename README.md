# dwdforecast

## Purpose
Extract weather forecast data from DWD Mosmix for a given Station ID.

## Background
DWD provides 10 day forecast weather and radiation data at an hourly resolution for over 5000 stations worldwide (focus is on Germany/Europe). The script downloads, unzips, and parses KML files from DWD, extracting key weather parameters for a specified station.

- **KML file description:**
  https://www.dwd.de/DE/leistungen/opendata/help/schluessel_datenformate/kml/mosmix_elemente_pdf.pdf?__blob=publicationFile&v=3
- **List of available stations:**
  https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication&nn=495490

## How to Use
1. Find the station close to your geographic location:
   - Go to https://wettwarn.de/mosmix/mosmix.html, zoom to your location, and click on "Mosmix Stationen anzeigen".
   - Note the closest station number (e.g., P755 for Munich).
2. Update your `config.json` file with your station number and URL.
   - Example: `"DWDStation": "P755"`, `"DWDStationURL": "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/P755/kml"`

## Implementation Notes
- DWD provides two types of KML files:
  - Single station KML files (updated every ~6 hours, recommended for most users)
  - All stations KML file (updated hourly, very large, not recommended for low-memory systems)
- The script uses a subthread to poll the DWD webserver and check for updates. When an update is found, the file is downloaded, unzipped, and parsed.
- Extracted parameters:
  - `myTZtimestamp`: Timestamp of the forecast data
  - `Rad1h`: Radiation Energy [kJ/m²]
  - `TTT`: Temperature 2 m above surface [°C]
  - `PPPP`: Pressure Values (Surface Pressure reduced)
  - `FF`: Wind speed [m/s]

## Update History
- **July 30, 2020:** Added 'Simple' and 'Complex' operation modes.
- **August 9, 2020:** Added PVLIB support for more precise power prediction; added output options (print, CSV, MariaDB).
- **August 9, 2020 (Update 2):** Moved all configuration parameters to `configuration.ini` (now `config.json`).
- **August 12, 2020:** Fixed Rad1Energy calculation.
- **September 5, 2020:** Adjusted timezones, changed to ERBS simulation model.
- **September 10, 2020:** Improved error messaging, added support for East/West PV systems.
- **October 10, 2020:** Updated documentation, improved compatibility with different pvlib versions.
- **October 12, 2020:** Added database port configuration.
- **October 18, 2020:** Dropped support for pvlib < 0.8.0, added TEMPERATURE_MODEL_PARAMETERS config.
- **October 24, 2020:** Changed datetime field format for DB compatibility, added more debugging.
- **Feb 12, 2023:** Updated for pvlib 0.9.4 and future deprecations.

## Dependencies & Installation
- Python 3.x
- Required Python packages:
  - `pvlib` (install with `pip install pvlib`)
  - `mysql-connector-python` (install with `pip install mysql-connector-python`)
  - `scipy`, `numpy`, `pandas`, `requests`, `beautifulsoup4`
- On Raspberry Pi or similar:
  - `sudo apt-get install python3-numpy python3-scipy`

## Configuration
All configuration is now in `config.json`. See the template and comments in this README for details.

## Operation Modes
- **Simple:** Pulls data once, processes, outputs, and terminates.
- **Complex:** Runs in a loop, polls for updates, processes, and outputs continuously.

## Output Options
- Print to console
- Write to CSV
- Write to MariaDB/MySQL database (table must exist)

## Output Configuration and Paths

The output CSV file path is configured in `config.json` under the `Output` section. You can specify a single path or a list of candidate paths for cross-platform compatibility. The script will attempt to write the output to each path in order and use the first one that works.

Example:

```
"Output": {
  "CSVFile": [
    "/home/witti/dwd.git/outputdwdforecast.csv",
    "/Users/witti/dwd.git/outputdwdforecast.csv",
    "outputdwdforecast.csv"
  ],
  ...
}
```

If you specify a list, the script will try each path in order. This is useful for running the script on different operating systems (Linux, macOS, Windows) without changing the config each time.

If none of the paths are writable, you will see an error in the terminal and in the log file (`dwd_debug.txt`).

## Modularized Output Logic

The output logic is now handled in `lib/data_output.py`. This module provides a function to write the DataFrame to the first available path from the list, improving maintainability and clarity.

## Example Table Definition
```
describe dwd;
+-------------+------------+------+-----+---------+-------+
| Field       | Type       | Null | Key | Default | Extra |
+-------------+------------+------+-----+---------+-------+
| mydatetime  | datetime   | NO   | PRI | NULL    |       |
| mytimestamp | int(11)    | NO   | PRI | 0       |       |
| Rad1h       | float(8,2) | NO   |     | 0.00    |       |
| PPPP        | float(8,2) | NO   |     | 0.00    |       |
| FF          | float(5,2) | NO   |     | 0.00    |       |
| TTT         | float(5,2) | NO   |     | 0.00    |       |
| Rad1wh      | float(8,2) | NO   |     | 0.00    |       |
| Rad1Energy  | float(8,2) | NO   |     | 0.00    |       |
| ACSim       | float(8,2) | NO   |     | 0.00    |       |
| DCSim       | float(8,2) | NO   |     | 0.00    |       |
| CellTempSim | float(5,2) | NO   |     | 0.00    |       |
+-------------+------------+------+-----+---------+-------+
```
