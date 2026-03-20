#
#  Copyright (C) 2020  Kilian Knoll kilian.knoll@gmx.de
#  Modernized and modularized in 2026 by Sven Witterstein to investigate missing DWD station data.
#
#  License: See LICENSE.md for details (GPLv3+ and modernization notice).
#

import logging
import queue
import sys
from lib import kml_reader, data_processing, db, poller, data_output, config_utils
from lib.kml_reader import extract_mosmixdata



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
    mosmix_type = getattr(config.DWD, 'MOSMIXType', 'L').upper()
    last_kml_url = {}       # {label: url}
    last_kml_filename = {}  # {label: filename}
    last_mosmixdata = {}    # {label: mosmixdata} – cache for cross-source merging

    def _fetch_mosmix(url, label, station):
        """Download, extract and parse a single MOSMIX KMZ file.

        Returns (mosmixdata, is_new, newtime).
        On failure or no new file, mosmixdata falls back to the cached value and is_new is False.
        """
        urls, newtime = kml_reader.get_url_for_latest(url, ext='kmz')
        if not urls:
            print(f"[dwdforecast] No KML URLs found for MOSMIX_{label}.")
            logging.warning("No KML URLs found for MOSMIX_%s at %s", label, url)
            return last_mosmixdata.get(label), False, 0
        kml_zip_url = urls[-1]
        kml_filename = kml_zip_url.split('/')[-1]
        if kml_filename == last_kml_filename.get(label):
            logging.info("No new KML file for MOSMIX_%s. Last: %s", label, kml_filename)
            return last_mosmixdata.get(label), False, 0
        print(f"[dwdforecast] Downloading MOSMIX_{label}: {kml_zip_url}")
        kml_path = kml_reader.extract_kml_from_zip(kml_zip_url)
        if not kml_path:
            logging.warning("Failed to extract KML for MOSMIX_%s", label)
            return last_mosmixdata.get(label), False, 0
        tree, root = kml_reader.parse_kml_file(kml_path)
        if not tree:
            logging.warning("Failed to parse KML for MOSMIX_%s", label)
            return last_mosmixdata.get(label), False, 0
        last_kml_url[label] = kml_zip_url
        last_kml_filename[label] = kml_filename
        mosmixdata = extract_mosmixdata(root, station)
        last_mosmixdata[label] = mosmixdata
        return mosmixdata, True, newtime

    # Polling function
    def poll_func():
        print("[dwdforecast] Checking for new DWD forecast data...")
        if mosmix_type == 'BOTH':
            station_primary = getattr(config.DWD, 'DWDStationPrimary',
                                      getattr(config.DWD, 'DWDStation', ''))
            station_secondary = getattr(config.DWD, 'DWDStationSecondary', station_primary)
            data_l, new_l, newtime_l = _fetch_mosmix(config.DWD.DWDStationURL, 'L', station_secondary)
            data_s, new_s, newtime_s = _fetch_mosmix(config.DWD.DWDStationURL_S, 'S', station_primary)
            if not new_l and not new_s:
                print("[dwdforecast] No new KML files on server. Skipping cycle.")
                return None
            if data_l is not None and data_s is not None:
                print("[dwdforecast] Merging MOSMIX_S (near-term) and MOSMIX_L (extended) data...")
                mosmixdata = kml_reader.merge_mosmixdata(data_s, data_l)
            else:
                fallback = 'L' if data_l is not None else 'S'
                print(f"[dwdforecast] Only MOSMIX_{fallback} data available; skipping merge.")
                logging.warning("Only MOSMIX_%s data available for this cycle; merge skipped.", fallback)
                mosmixdata = data_l if data_l is not None else data_s
            newtime = newtime_s or newtime_l
        else:
            station_primary = getattr(config.DWD, 'DWDStationPrimary',
                                      getattr(config.DWD, 'DWDStation', ''))
            station_secondary = getattr(config.DWD, 'DWDStationSecondary', station_primary)
            if mosmix_type == 'S':
                station = station_primary
            elif mosmix_type == 'L':
                station = station_secondary
            else:
                logging.error(
                    "Unknown MOSMIXType '%s'; must be L, S, or BOTH. "
                    "Using primary station but this configuration is invalid and will likely fail.",
                    mosmix_type
                )
                station = station_primary
            mosmixdata, is_new, newtime = _fetch_mosmix(config.DWD.DWDStationURL, mosmix_type, station)
            if not is_new:
                print(f"[dwdforecast] No new MOSMIX_{mosmix_type} data. Skipping cycle.")
                return None
        print("[dwdforecast] Processing data with PVLIB...")
        df, mc_weather, modelchain = data_processing.process_with_pvlib(mosmixdata, config)
        # Output
        if config.Output.CSVOutput:
            data_output.write_dataframe_to_csv(df, config_utils.get_csv_file_candidates(config.as_dict))
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
    my_queue1 = queue.Queue()
    poll_thread = poller.PollerThread(my_queue1, poll_func, interval=config.Processing.Sleeptime, cooldown=3600)
    poll_thread.start()
    print("[dwdforecast] Poller started. Exiting main thread.")
    # The poller module is now responsible for any waiting or server-like operation.


if __name__ == "__main__":
    main()
