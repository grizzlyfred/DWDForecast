# DWD Forecast Script

## Introduction

This library provides a Python interface to access weather forecast data
published as "open data" by DWD (Deutscher Wetterdienst), the German national
meteorological service. The project extracts selected parameters from MOSMIX
forecast files for a chosen station:

- Rad1h: hourly global radiation [W/m²]
- TTT: air temperature (Kelvin in the source; converted to °C in processing)
- PPPP: surface pressure [hPa]
- FF: wind speed [m/s]

The library uses pvlib together with a configurable PV system description to
produce a local hourly forecast for the next 10 days. Forecast outputs include:

- ACSim: simulated AC power of the PV system
- DCSim: simulated DC power of the PV system
- CellTempSim: simulated PV cell temperature [°C]
- Rad1Energy: simplified hourly energy estimate (Wh), suitable for
  aggregating daily yield estimates


## Overview

This script extracts weather forecast data from DWD MOSMIX data for a given
station and processes it for PV system analysis.

## Usage Modes

### Standard Mode (Default)

- How to use: run the script without any command-line arguments:

```bash
python dwdforecast.py
```

- Behavior:
  - Performs a single polling attempt to fetch and process the latest DWD
    forecast data.
  - Outputs results as configured (CSV, print, database, etc.).
  - Exits after the attempt.

### Server Mode (Polling / Daemon)

- How to use: run the script with any command-line argument(s):

```bash
python dwdforecast.py --server
```

- Behavior:
  - Starts a background polling thread that checks for new DWD forecast data
    at regular intervals (as configured).
  - Suitable for continuous operation or integration as a service.
  - The polling interval and cooldown are configurable in `config.json`.

## Configuration

All configuration is handled via `config.json`; see that file for available
options.

**Example:**

```json
{
  "DWD": {
    "DWDStation": "A123",
    "DWDStationURL": "http://opendata.dwd.de/.../A123/kml/"
  },
  "SolarSystem": {
    "ModuleName": "...",
    "InverterName": "..."
  },
  "Output": {
    "CSVOutput": 1,
    "PrintOutput": 1,
    "DBOutput": 0,
    "CSVFile": "output.csv"
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

### DWD MOSMIX data & station list

To adapt the script to your needs, familiarize yourself with the MOSMIX data
format (keyword: "MOSMIX") used by DWD. Useful links:

- MOSMIX documentation (DWD):
  https://www.dwd.de/DE/leistung…_blob=publicationFile&v=3
- List of available (virtual) weather stations:
  https://www.dwd.de/DE/leistung…=nasPublication&nn=495490
- MOSMIX station finder / preview:
  https://wettwarn.de/mosmix/mosmix.html

Once you find the closest station, note the station identifier and set
`DWD.DWDStation` and `DWD.DWDStationURL` in `config.json`. The script contains
inline comments and sensible defaults to help you get started.

## Modularization

The codebase is split into logical modules:

- `dwdforecast.py` — main entry point, handles configuration and orchestration
- `lib/config_utils.py` — configuration loading and access
- `lib/kml_reader.py` — downloading and parsing DWD KML/KMZ files
- `lib/data_processing.py` — DataFrame and pvlib processing
- `lib/db.py` — database operations
- `lib/poller.py` — polling / threading logic
- `lib/data_output.py` — output utilities (CSV, print, etc.)

## Logging

Logging is fully configurable via `config.json`. By default logs are written to
`/tmp/dwd_kml.log`.

## Output Formats

Whenever the script writes a CSV file, it also writes a JSON file (with the
same base name) containing the same data in records format. This ensures that
both CSV and JSON are available for downstream use or inspection.

Example: if your output is `output.csv` you will also get `output.json` in the
same directory.

## Notes on Dependencies and Workarounds

### SciPy Chandrupatla Algorithm

If you encounter issues related to `scipy.optimize._chandrupatla` (used
internally by SciPy for root-finding and optimization), some workarounds or
patches may be required for certain edge cases or division-by-zero errors.
If you experience unexpected errors or warnings from this module, consult the
SciPy documentation or consider updating SciPy to the latest version.

If a workaround or patch is applied to your local
`scipy.optimize._chandrupatla.py`, please document the change and keep a
backup of the original file.

## Tested on

This project runs on modern operating systems. Modern single-board computers
(SBCs), such as the Raspberry Pi, are capable of running the script when a
supported Python (3.13+) version is installed.

## Installation

Clone the repository and install dependencies (recommended: use a virtual
environment).

For macOS / Linux / Raspberry Pi:

```bash
# Clone the repo
git clone https://github.com/kilianknoll/DWDForecast.git
cd DWDForecast

# Create and activate a virtual environment (Python 3.10+ recommended)
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For Windows (PowerShell):

```powershell
git clone https://github.com/kilianknoll/DWDForecast.git
cd DWDForecast
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Notes for SBCs (Raspberry Pi etc.):

- Ensure system packages required for building Python packages are installed
  (example for Debian/Raspbian):

```bash
sudo apt update && \
  sudo apt install -y build-essential python3-dev python3-venv \
  libxml2-dev libxslt1-dev
```

- Then follow the macOS/Linux steps above to create a virtualenv and install
  Python packages.

## Quick run

After installation, run the script with:

```bash
python dwdforecast.py
```

## Features

- The library provides a class that reads the selected DWD weather station
  and produces the parsed forecast values described above.

- Operation modes:
  - Simple (single-shot): the script performs one fetch+process cycle and
    exits. This is suitable for scheduled runs (recommended for production).
  - Continuous (poller): the script runs a background polling loop and
    repeatedly checks for updates. Use this only when you need a long-
    running process and ensure it is managed by a service supervisor.

- Deployment recommendation:
  - For reliability and simplicity we recommend using the Simple (single-
    shot) mode and scheduling periodic runs with a systemd timer or a cron
    job. This approach reduces long-running process complexity and improves
    robustness (restarts, logging, resource limits).
  - If you prefer Continuous mode, run the script under a supervisor (for
    example systemd) and configure appropriate polling intervals and cooldown
    values in `config.json`.

- Output options (configurable, see `config.json`):
  - Print to console/log
  - CSV output (plus accompanying JSON)
  - Upload to MariaDB (or other database via configuration)
  - Future: InfluxDB (see TODO.md)
    - Planned options:
      - Built-in uploader: extend `lib/data_output.py` to write directly to
        InfluxDB using an appropriate client library.
      - Separate tool/agent: a small standalone uploader that reads the
        generated CSV/JSON and writes to InfluxDB (recommended if you want a
        decoupled ingestion pipeline and easier retries/backfills).
    - See `TODO.md` for tasks and notes related to InfluxDB integration.

## Disclaimer

.. Warning::

Please note that you are responsible to operate this program and comply with
regulations imposed on you by other website providers (such as the DWD site
being polled).

Therefore, the author does not provide any guarantee or warranty concerning
correctness, functionality or performance and does not accept liability for
damage caused by this module, examples, or mentioned information.

**Thus, use it at your own risk!**

## License

See `LICENSE.md` for details. Original copyright (C) 2020 Kilian Knoll.
Modernization and modularization (C) 2026 Sven Witterstein
