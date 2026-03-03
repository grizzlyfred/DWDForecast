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

## Configuration Reference (with Comments)

- **ProcessingConfiguration**: Controls the main operation mode of the script. Possible values:
  - `Simple`: The script pulls data from DWD once, performs calculations, creates the specified output, and then terminates.
  - `Complex`: The script runs in an endless loop, looks for updates on the DWD site, performs calculations when updates are received, and creates the specified outputs. Use this for continuous/daemon operation.

Below is a full reference for all configuration options, including detailed comments and explanations as found in the original INI file. Use this as a guide for what each option means and how to set it in your config.json.

```
# Configuration file for dwdforecast.py
[DWD]           
    # DWD Station Name / Number
    # Use : https://wettwarn.de/mosmix/mosmix.html to find closest station to you
    # 
    #DWDStation = P1107 #Ebrach no Solar
    # K4058 = Ebrach ri. BWF oder P148 Realschule (beste) oder x246 (im Wald)
    DWDStation = P148
    # This is the matching URL for the given station
    # Please also ensure the station provides Rad1h data (some do not - without this dataset, the simulation WILL NOT WORK
    # Only use the "all_stations" if you got decent hardware
    #DWDStationURL = 'http://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_S/all_stations/kml'
    #On Raspberries & alikes, use the one for your specific station: 
    DWDStationURL = http://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/P148/kml/
[SolarSystem]
    # GPS  Longitude of your solar system (use google maps etc. to find out)
    Longitute = 10.499
    # GPS  Latitude of your solar system (use google maps etc. to find out)
    Latitude = 48.852
    #Altitude [m] of your solar system´s location
    Altitude = 330
    # Elevation [Degrees]: Inclination angle of solar panels (0 degrees would be horizontal)
    Elevation = 45
    # Azimuth [Degrees] of your panels: Orientation - where 270=West, 180=South, 90=East
    Azimuth = 190
    # NumPanels [int] Number of panels per string in the solar system
    NumPanels = 28
    # NumStrings [int] Number of strings in the solar system
    NumStrings = 3
    # Albedo of your surrondind SolarSystem´s environment [%] with 100% = 1
    # Please see below for typical values:
    # https://pvpmc.sandia.gov/model…-ground-reflected/albedo/
    Albedo = 0.14
    # TEMPERATURE_MODEL_PARAMETERS valid parameters are:
    # open_rack_glass_glass
    # close_mount_glass_glass
    # open_rack_glass_polymer
    # insulated_back_glass_polymer
    # Please also see the pvlib documentation: https://pvlib-python.readthedocs.io/en/stable/api.html?highlight=TEMPERATURE_MODEL_PARAMETERS#pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS
    # Closest match for roof mounted systems seem to be the open_rack ones:
    TEMPERATURE_MODEL = open_rack_glass_glass
    #
    # InverterName [string] - Name of the inverter of your solar system
    # Caution: special characters need to be replaced with underscores
    # CSV file used by pvlib can be found in your python installation
    # e.g: /usr/local/lib/python3.5/dist-packages/pvlib/data
    # in sam-library-cec-inverters-2019-03-05.csv
    # So Map from name in CSV file 
    # SMA America: SB10000TL-US [240V]
    # To 
    # SMA_America__SB10000TL_US__240V_
    # You can also create your own ones - but need to adjust csv file in pvlib installation
    # Kostal__Plenticore_plus_10
    #InverterName = Kostal__Plenticore_plus_10
    InverterName = SMA_America__SB10000TL_US__240V_
    
    
    # ModuleName [string] - Name of the solar modules of your solar system
    # Caution: special characters need to be replaced with underscores
    # CSV file used by pvlib can be found in your python installation
    # e.g: /usr/local/lib/python3.5/dist-packages/pvlib/data
    # in sam-library-cec-modules-2019-03-05.csv
    # So Map from name in CSV file 
    # LG Electronics Inc. LG335E1C-A5
    # To 
    # LG_Electronics_Inc__LG335E1C_A5
    ModuleName = LG_Electronics_Inc__LG335E1C_A5
    #MyTimezone [string] - Timezone of DWD data: GMT 
    #https://pvlib-python.readthedocs.io/en/stable/timetimezones.html
    MyTimezone = Europe/Berlin
    #
    #SimpleMultiplicationFactor [real]
    #A Factor that gets used to convert Rad1wh values to actual Powergen values (Rad1wh --> Rad1Energy)
    #Note: SimpleMultiplicationFactor is only being used for an approximate calculation that does not take azimuth - or elevation into account
    # SimpleMultiplicationFactor =  ModuleArea * ModuleEfficiency * InverterEfficiency
    # Modulearea [squaremeters] (e.g.)                  : 28 * 1*1.6 
    # ModuleEfficiency (from Datasheet of your panel)   : 0.196
    # InverterEfficiency (from Inverter Datasheet)      : 0.98
    # SimpleMultiplicationFactor = 0.278 * 44.8 * 0.196 * 0.98 = 8.605184
    # For the above values - this results in SimpleMultiplicationFactor below:
    # myPV 11*3*1.6*0.18 + 9*3*1.6*0.2 + 9*1.6*0.19 + 2*1.6*0.15 + 2*1.6*0.18 + 9*1.6*0.17 = 24.384 kommt mir fast wie kWp vor, passt...
    SimpleMultiplicationFactor = 24.384
    #Temperatureoffset [real in °C] : an addition to the temperature input from DWDStation
    #Some users reported different actual temperatures whereas others were fine with the temperature values calculated by pvlib
    TemperatureOffset = 0

[Processing]
    #Sleeptime [seconds] : Time we pause before we check the DWD webpage for updates
    Sleeptime = 15
    #Configuration [String] : Simple - or Complex
    #Simple : We are pulling the data from DWD  once, perform the calculations, create the specified output and then terminate the program
    #Complex: We run the program in an endless loop, look for updates on the dwd site, perform the calculations once we receive updates and create the specified outputs
    ProcessingConfiguration = Simple    
    

[Output]
    # PrintOutput of the program [int] 0 = no, 1 = yes
    PrintOutput = 0
    # CSVOutput of the program [int] 0 = no, 1 = yes
    CSVOutput = 1
    # CSVFile - in case we have set CSVOutput to 1, we also must have a file to write to
    CSVFile = /home/witti/dwd.git/outputdwdforecast.csv
    # DBOutput of the program [int] 0 = no, 1 = yes - we output result to mysql Database
    # Tested with mariaDB
    DBOutput = 0
    # DBUser [string] : Name of the database user
    DBUser = YOURDBUSER
    # DBPassword [string] : Password for database user DBUser
    DBPassword = YOURDBPASSWD
    # DBHost [string] : Host machine of database 
    DBHost = 192.168.178.28
    # DBPort [int] : The port being used to connect to the database (default 3306):
    DBPort = 3306
    # DBName [string] : Name of the database we are commiting to
    DBName = YOURDBNAME
    # DBTable [string] : Database table name that you want to commit your data to
    # Please note: The script is assuming the table below already exists
    # A Table with the following definition is what we are populating to:
    #describe dwd;
    #    +-------------+------------+------+-----+---------+-------+
    #    | Field       | Type       | Null | Key | Default | Extra |
    #    +-------------+------------+------+-----+---------+-------+
    #    | mydatetime  | datetime   | NO   | PRI | NULL    |       |
    #    | mytimestamp | int(11)    | NO   | PRI | 0       |       |
    #    | Rad1h       | float(8,2) | NO   |     | 0.00    |       |
    #    | PPPP        | float(8,2) | NO   |     | 0.00    |       |
    #    | FF          | float(5,2) | NO   |     | 0.00    |       |
    #    | TTT         | float(5,2) | NO   |     | 0.00    |       |
    #    | Rad1wh      | float(8,2) | NO   |     | 0.00    |       |
    #    | Rad1Energy  | float(8,2) | NO   |     | 0.00    |       |
    #    | ACSim       | float(8,2) | NO   |     | 0.00    |       |
    #    | DCSim       | float(8,2) | NO   |     | 0.00    |       |
    #    | CellTempSim | float(5,2) | NO   |     | 0.00    |       |
    #    +-------------+------------+------+-----+---------+-------+
    DBTable = dwd
```
