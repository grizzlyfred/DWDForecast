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

Once you find the closest station, note the number and change the Python script or config file to your needs.

Next, change the solar system's key characteristics such as location, azimuth, elevation, inverter, panels, etc. See `config.json` for more details.

## Running the Script
```bash
python3 dwdforecast.py
```

