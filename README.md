# dwdforecast

## Introduction

This library provides a Python interface to access DWD weather forecast data to project solar power generation. It extracts the following data from a MOSMIX file (see specifications below):

- Rad1h
- TTT
- PPPP
- FF

It uses pvlib to leverage the parameters above in conjunction with a configurable solar system and presents hourly forecasts for the next 10 days. Forecast data contains:

- ACSim: Simulated AC of solar system
- DCSim: Simulated DC of solar system
- CellTempSim: Temperature of solar cells [°C]
- Rad1Energy: Simplified calculation of solar system's power generation

Tested with Python version 3.10.5, 3.9.2 (OLD: 3.6.2, 3.7.3)

### Tested Platforms
- Raspberry Pi
- Windows

## Installation
Clone or download the repo and use `dwdforecast.py`.

## Configuration
To adapt to your needs, familiarize yourself with the content of the data to be parsed (Keyword: Mosmix):
- [MOSMIX Data Format](https://www.dwd.de/DE/leistungen/opendata/help/schluessel_datenformate/kml/mosmix_elemente_pdf.pdf?__blob=publicationFile&v=3)

List of available (virtual) weather stations:
- [MOSMIX Stations](https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication&nn=495490)

Check the closest weather station to your location:
- [Find Your Station](https://wettwarn.de/mosmix/mosmix.html)

Once you find the closest station, note the number and update the `config.json` file to your needs.

### JSON Configuration File
The `config.json` file contains all the necessary parameters to customize the script for your solar system and weather station. Below is an example structure of the file:

```json
{
  "DWD": {
    "DWDStation": "P755",
    "DWDStationURL": "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/P755/kml"
  },
  "SolarSystem": {
    "Longitude": 11.5755,
    "Latitude": 48.1374,
    "Altitude": 519,
    "Elevation": 30,
    "Azimuth": 180,
    "NumPanels": 10,
    "NumStrings": 2,
    "Albedo": 0.2,
    "TEMPERATURE_MODEL": "sapm",
    "InverterName": "SMA_America__SB10000TL_US__240V_",
    "ModuleName": "LG Electronics Inc. LG335E1C-A5",
    "SimpleMultiplicationFactor": 1.0,
    "TemperatureOffset": 0.0,
    "MyTimezone": "Europe/Berlin"
  },
  "Processing": {
    "Sleeptime": 3600
  },
  "Output": {
    "PrintOutput": 1,
    "CSVOutput": 1,
    "DBOutput": 0,
    "CSVFile": "output.csv",
    "DBUser": "user",
    "DBPassword": "password",
    "DBHost": "localhost",
    "DBName": "weather",
    "DBPort": 3306,
    "DBTable": "dwd"
  }
}
```

Update the fields to match your solar system's specifications and database settings. This eliminates the need to modify the Python script directly.

## Running the Script
```bash
python3 dwdforecast.py
```
