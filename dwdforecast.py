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
import sys
from lib import kml_reader, data_processing, db, poller, data_output, config_utils
from lib.kml_reader import extract_mosmixdata, connvertINTtimestamptoDWD
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS



def main():
    print("[dwdforecast] Starting up...")
    # Load config using utility (property-style access)
    config = config_utils.load_config_accessor('config.json')
    # Logging config from config file, with defaults
    log_file = getattr(config.Logging, 'File', '/tmp/dwd_kml.log')
    log_level_str = getattr(config.Logging, 'Level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s %(levelname)s [%(module)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    print("[dwdforecast] PVLIB system will be initialized in the PVLIB module.")
    if config.Output.DBOutput:
        print("[dwdforecast] Database output enabled.")
    last_kml_url = None
    last_kml_filename = None
    # Polling function
    def poll_func():
        nonlocal last_kml_url, last_kml_filename
        print("[dwdforecast] Checking for new DWD forecast data...")
        urls, newtime = kml_reader.get_url_for_latest(config.DWD.DWDStationURL, ext='kmz')
        if not urls:
            print("[dwdforecast] No KML URLs found. Last known file:", last_kml_url)
            logging.warning("No KML URLs found. Last known file: %s", last_kml_url)
            return None
        kml_zip_url = urls[-1]
        kml_filename = kml_zip_url.split('/')[-1]
        if kml_filename == last_kml_filename:
            print(f"[dwdforecast] No new KML file on server. Last file: {kml_filename}")
            logging.info("No new KML file on server. Last file: %s", kml_filename)
            return None
        last_kml_url = kml_zip_url
        last_kml_filename = kml_filename
        print(f"[dwdforecast] Downloading: {kml_zip_url}")
        kml_path = kml_reader.extract_kml_from_zip(kml_zip_url)
        if not kml_path:
            print("[dwdforecast] Failed to extract KML file. Last known file:", last_kml_url)
            logging.warning("Failed to extract KML file. Last known file: %s", last_kml_url)
            return None
        print(f"[dwdforecast] Parsing KML: {kml_path}")
        tree, root = kml_reader.parse_kml_file(kml_path)
        if not tree:
            print("[dwdforecast] Failed to parse KML file. Last known file:", last_kml_url)
            logging.warning("Failed to parse KML file. Last known file: %s", last_kml_url)
            return None
        print("[dwdforecast] Extracting weather data...")
        mosmixdata = extract_mosmixdata(root, config.DWD.DWDStation)
        print("[dwdforecast] Processing data with PVLIB...")
        df, mc_weather, modelchain = data_processing.process_with_pvlib(mosmixdata, config)
        # Output
        if config.Output.CSVOutput:
            data_output.write_dataframe_to_csv(df, config_utils.get_csv_file_candidates(config._data))
        if config.Output.PrintOutput:
            print("[dwdforecast] Logging combined results to dwd_debug.txt.")
            logging.info("Here are the combined results from DWD - as well as PVLIB:")
            logging.info("%s", df)
        if config.Output.DBOutput:
            print("[dwdforecast] Writing results to database...")
            db.write_dataframe(df, config)
        print("[dwdforecast] Cycle complete.")
        return newtime


    # Standard mode: 1 polling attempt if no arguments
    if len(sys.argv) == 1:
        print("[dwdforecast] Standard mode: single polling attempt.")
        poll_func()
        print("[dwdforecast] Finished polling attempt. Exiting.")
        return
    # Server mode: start poller thread if arguments are given
    myQueue1 = queue.Queue()
    poll_thread = poller.PollerThread(myQueue1, poll_func, interval=config.Processing.Sleeptime, cooldown=3600)
    poll_thread.start()
    print("[dwdforecast] Poller started. Exiting main thread.")
    # The poller module is now responsible for any waiting or server-like operation.


if __name__ == "__main__":
    main()
