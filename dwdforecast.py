#
#  Copyright (C) 2020  Kilian Knoll kilian.knoll@gmx.de
#  Modernized and modularized in 2026 by Sven Witterstein to investigate missing DWD station data.
#
#  License: See LICENSE.md for details (GPLv3+ and modernization notice).
#

import logging
import queue
import json
import time
from lib import kml_reader, data_processing, db, poller
from lib.kml_reader import extract_mosmixdata
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS


def connvertINTtimestamptoDWD(inputstring):
    mysecondtime = (time.strftime('%Y-%m-%dT%H:%M:%S.%f', time.localtime(inputstring))[:-3]) + "Z"
    return mysecondtime


def main():
    logging.basicConfig(filename="dwd_debug.txt", level=logging.DEBUG)
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    # Extract config values
    station = config['DWD']['DWDStation']
    urlpath = config['DWD']['DWDStationURL']
    longitude = config['SolarSystem']['Longitude']
    latitude = config['SolarSystem']['Latitude']
    altitude = config['SolarSystem']['Altitude']
    pv_elevation = config['SolarSystem']['Elevation']
    pv_azimuth = config['SolarSystem']['Azimuth']
    num_panels = config['SolarSystem']['NumPanels']
    num_strings = config['SolarSystem']['NumStrings']
    albedo = config['SolarSystem']['Albedo']
    temperature_model = config['SolarSystem']['TEMPERATURE_MODEL']
    inverter = config['SolarSystem']['InverterName']
    module = config['SolarSystem']['ModuleName']
    simple_factor = config['SolarSystem']['SimpleMultiplicationFactor']
    temp_offset = config['SolarSystem']['TemperatureOffset']
    timezone = config['SolarSystem']['MyTimezone']
    sleeptime = config['Processing']['Sleeptime']
    print_output = config['Output']['PrintOutput']
    csv_output = config['Output']['CSVOutput']
    db_output = config['Output']['DBOutput']
    csv_file = config['Output']['CSVFile']
    db_user = config['Output']['DBUser']
    db_password = config['Output']['DBPassword']
    db_host = config['Output']['DBHost']
    db_name = config['Output']['DBName']
    db_port = config['Output']['DBPort']
    db_table = config['Output']['DBTable']

    # Setup PVLIB system
    temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm'][temperature_model]
    sandia_modules = pvlib.pvsystem.retrieve_sam('cecmod')
    sandia_module = sandia_modules[module]
    cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    cec_inverter = cec_inverters[inverter]
    pv_location = Location(latitude=latitude, longitude=longitude, tz=timezone, altitude=altitude)
    pv_system = PVSystem(
        surface_tilt=pv_elevation,
        surface_azimuth=pv_azimuth,
        module=sandia_module,
        inverter=cec_inverter,
        module_parameters=sandia_module,
        inverter_parameters=cec_inverter,
        albedo=albedo,
        modules_per_string=num_panels,
        racking_model="open_rack",
        temperature_model_parameters=temperature_model_parameters,
        strings_per_inverter=num_strings
    )

    # Setup DB connection if needed
    db_conn = db_cur = None
    if db_output:
        db_conn, db_cur = db.connect_db(db_user, db_password, db_host, db_port, db_name)

    # Polling function
    def poll_func():
        urls, newtime = kml_reader.get_url_for_latest(urlpath, ext='kmz')
        if not urls:
            logging.warning("No KML URLs found.")
            return None
        kml_zip_url = urls[-1]
        kml_path = kml_reader.extract_kml_from_zip(kml_zip_url)
        if not kml_path:
            logging.warning("Failed to extract KML file.")
            return None
        tree, root = kml_reader.parse_kml_file(kml_path)
        if not tree:
            logging.warning("Failed to parse KML file.")
            return None
        mosmixdata = extract_mosmixdata(root, station)
        df = data_processing.build_dataframe(mosmixdata, temp_offset)
        df, mc_weather, modelchain = data_processing.run_pvlib(df, pv_system, pv_location, simple_factor)
        # Output
        if csv_output:
            df.to_csv(csv_file)
        if print_output:
            logging.info("Here are the combined results from DWD - as well as PVLIB:")
            logging.info("%s", df)
        if db_output and db_cur:
            for _, row in df.iterrows():
                # Prepare row dict as in original
                row_dict = row.to_dict()
                if db.check_timestamp_existence(db_cur, db_table, int(row_dict['mytimestamp'])) == 0:
                    db.addsingle_row(db_cur, db_table, row_dict)
                else:
                    db.update_row(db_cur, db_table, row_dict['TTT'], row_dict['Rad1h'], row_dict['FF'], row_dict['PPPP'], row_dict['mytimestamp'], row_dict['Rad1Energy'], row_dict['ACSim'], row_dict['DCSim'], row_dict['CellTempSim'], row_dict['Rad1wh'])
        return newtime

    # Start polling thread
    myQueue1 = queue.Queue()
    poll_thread = poller.PollerThread(myQueue1, poll_func, interval=sleeptime)
    poll_thread.start()
    while myQueue1.empty():
        time.sleep(1)
    i = 0
    try:
        while i < 1:
            if not myQueue1.empty():
                quelength = myQueue1.qsize()
                for _ in range(quelength):
                    LastDWDtimestamp = myQueue1.get()
                    mylasttimestamp = connvertINTtimestamptoDWD(LastDWDtimestamp)
            i += 1
            time.sleep(1)
        time.sleep(60)
        poll_thread.event.set()
    except KeyboardInterrupt:
        poll_thread.event.set()
    except Exception as e:
        poll_thread.event.set()
        logging.error("Main loop error: %s", e)

if __name__ == "__main__":
    main()
