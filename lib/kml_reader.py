# KML reading and parsing utilities for DWD forecast
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests
import zipfile
import urllib.request
import shutil
import time
import datetime
import logging

# ---------------------------------------------------------------------------
# DWD MOSMIX element reference
# Maps raw dwd:elementName values (as they appear in the KML) to a
# (description, unit) tuple.  Source: DWD MOSMIX KML format description.
# https://www.dwd.de/DE/leistungen/met_verfahren_mosmix_snow/mosmix_kml_formatbeschreibung.pdf
# ---------------------------------------------------------------------------
MOSMIX_ELEMENT_INFO = {
    # --- fields currently extracted by this module ---
    "TTT":    ("Air temperature 2 m above ground",          "K (converted to °C on read)"),
    "FF":     ("Wind speed 10 m above ground",              "m/s"),
    "PPPP":   ("Surface pressure reduced to sea level",     "Pa"),
    "Rad1h":  ("Global radiation, last hour",               "kJ/m²"),
    # --- additional forecast elements of interest ---
    "DD":     ("Wind direction 10 m above ground",          "degrees (0–360)"),
    "FX1":    ("Maximum wind gust within last hour",        "m/s"),
    "N":      ("Total cloud cover",                         "% (0–100)"),
    "RR1c":   ("Total precipitation last hour",             "kg/m²"),
    "SunD1":  ("Sunshine duration last hour",               "s"),
    "VV":     ("Visibility",                                "m"),
    "Td2":    ("Dew point temperature 2 m above ground",    "K"),
    "RRSF":   ("Snow fraction of total precipitation",      "1 (fraction 0–1)"),
}


def get_url_for_latest(urlpath, ext=''):
    try:
        page = requests.get(urlpath).text
    except Exception as ErrorGetWebdata:
        logging.error("%s %s", ",GetURLForLatest Error getting data from the internet:", ErrorGetWebdata)
        return [], 0
    soup = BeautifulSoup(page, 'html.parser')
    soup_reduced = soup.find_all('pre')[0]
    counter = 0
    mynewtime = 0
    for elements in soup_reduced:
        elements = str(elements)
        if (counter > 0):
            words = elements.split()
            mytime = words[0] + "-" + words[1]
            logging.debug("%s %s", ",GetURLForLatest :DWD Filetimestamp found :", mytime)
            # Try parsing with seconds, fallback to without seconds
            try:
                mynewtime = time.mktime(datetime.datetime.strptime(mytime, "%d-%b-%Y-%H:%M:%S").timetuple())
            except ValueError:
                try:
                    mynewtime = time.mktime(datetime.datetime.strptime(mytime, "%d-%b-%Y-%H:%M").timetuple())
                except Exception as e:
                    logging.error("GetURLForLatest timestamp parse error: %s", e)
                    mynewtime = 0
            logging.debug("%s %s", ",GetURLForLatest :DWD Filetimestamp found :", mynewtime)
        if (elements.find("LATEST") > 0):
            counter = 1
    myurl = [urlpath + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return myurl, mynewtime


def extract_kml_from_zip(url, file_name="temp1.gz", target_subdir="KML"):
    # Define absolute paths based on the script location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    archive_path = os.path.join(base_dir, file_name)
    target_dir = os.path.join(base_dir, target_subdir)

    try:
        # 1. Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        logging.info("Target directory verified: %s", target_dir)

        # 2. Download with explicit stream handling
        logging.info("Downloading from %s", url)
        with urllib.request.urlopen(url) as response:
            with open(archive_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        # 3. Extract logic
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            first_file = zip_ref.namelist()[0]
            zip_ref.extractall(target_dir)
            logging.info("Extracted %s to %s", first_file, target_dir)
        return os.path.join(target_dir, first_file)

    except urllib.error.URLError as e:
        logging.error("Network error: %s", e.reason)
    except PermissionError as e:
        logging.error("Permission Denied: Ensure write access to %s. Error: %s", base_dir, e)
    except zipfile.BadZipFile:
        logging.error("Downloaded file is not a valid zip: %s", archive_path)
    except Exception as e:
        logging.error("Unexpected error during KML extraction: %s", e)
    finally:
        # Cleanup the temp zip to prevent lock issues on next run
        if os.path.exists(archive_path):
            os.remove(archive_path)
            logging.debug("Cleaned up temporary file: %s", archive_path)

    return None

def parse_kml_file(kml_path):
    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
        return tree, root
    except Exception as e:
        logging.error("Error parsing KML file: %s", e)
        return None, None


def extract_mosmixdata(root, station):
    """Extract forecast data and station coordinates for *station* from a parsed MOSMIX KML root.

    The DWD ``dwd:elementName`` attribute in each ``dwd:Forecast`` element holds
    the raw field code (e.g. ``TTT``, ``FF``).  We read those directly so every
    extracted value is traceable to the DWD MOSMIX specification
    (see :data:`MOSMIX_ELEMENT_INFO` for the full reference).

    Returns
    -------
    mosmixdata : list[list]
        Six parallel lists (columns):
        [0] ISO-8601 UTC timestamp strings
        [1] Human-readable timestamp strings (space-separated, Z stripped)
        [2] Rad1h – global radiation last hour (kJ/m²)
        [3] TTT   – air temperature 2 m above ground, converted to °C
        [4] PPPP  – sea-level pressure (Pa)
        [5] FF    – wind speed 10 m above ground (m/s)
    coordinates : dict or None
        ``{"lon": float, "lat": float, "alt": float}`` extracted from the KML
        ``<kml:Point><kml:coordinates>`` element, or ``None`` if not found.
    """
    ns = {'dwd': 'https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd',
          'gx': 'http://www.google.com/kml/ext/2.2',
          'kml': 'http://www.opengis.net/kml/2.2',
          'atom': 'http://www.w3.org/2005/Atom',
          'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'}
    # dwd:elementName attribute in the dwd namespace
    dwd_element_name_attr = '{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}elementName'

    timestamps = root.findall(
        'kml:Document/kml:ExtendedData/dwd:ProductDefinition/dwd:ForecastTimeSteps/dwd:TimeStep', ns)
    timevalue = [child.text for child in timestamps]
    Rad1h = TTT = PPPP = FF = None
    coordinates = None

    for elem in root.findall('./kml:Document/kml:Placemark', ns):
        name_elem = elem.find('kml:name', ns)
        if name_elem is None or name_elem.text != station:
            continue

        # --- extract geographic coordinates ---
        point_elem = elem.find('kml:Point/kml:coordinates', ns)
        if point_elem is not None and point_elem.text:
            parts = point_elem.text.strip().split(',')
            try:
                coordinates = {
                    'lon': float(parts[0]),
                    'lat': float(parts[1]),
                    'alt': float(parts[2]) if len(parts) > 2 else 0.0,
                }
                logging.info(
                    "Station %s coordinates from KML: lon=%.4f lat=%.4f alt=%.1f m",
                    station, coordinates['lon'], coordinates['lat'], coordinates['alt']
                )
            except (ValueError, IndexError) as e:
                logging.warning("Could not parse coordinates for station %s: %s", station, e)

        # --- extract forecast values ---
        myforecastdata = elem.find('kml:ExtendedData', ns)
        if myforecastdata is None:
            continue
        for subelem in myforecastdata:
            # Use the proper XML attribute, not fragile string-on-dict hacking
            element_name = subelem.get(dwd_element_name_attr)
            if element_name is None:
                continue
            value_text = subelem[0].text if len(subelem) > 0 else None
            if not value_text:
                continue
            if element_name == 'FF':
                FF = list(value_text.split())
            elif element_name == 'Rad1h':
                Rad1h = list(value_text.split())
            elif element_name == 'TTT':
                # TTT is in Kelvin; convert to °C (DWD offset is 273.15 K, but
                # the original code used 273.13 — keep the same value for
                # backward-compatibility with existing output)
                TTT = [round(float(v) - 273.13, 2) for v in value_text.split()]
            elif element_name == 'PPPP':
                PPPP = list(value_text.split())
        break  # stop scanning once the target station is found

    # Compose the mosmixdata columns
    mosmixdata = [[0] * len(timevalue) for _ in range(6)]
    for idx, ts in enumerate(timevalue):
        mosmixdata[0][idx] = ts
        mosmixdata[1][idx] = ts.replace('T', ' ').replace('Z', '')
        mosmixdata[2][idx] = Rad1h[idx] if Rad1h else 0
        mosmixdata[3][idx] = TTT[idx] if TTT else 0
        mosmixdata[4][idx] = PPPP[idx] if PPPP else 0
        mosmixdata[5][idx] = FF[idx] if FF else 0
    return mosmixdata, coordinates


def merge_mosmixdata(mosmix_s, mosmix_l):
    """Merge MOSMIX_S and MOSMIX_L data arrays.

    Both arguments are lists of 6 equal-length lists (columns):
        [0] ISO-8601 UTC timestamp strings (e.g. '2026-03-20T15:00:00.000Z')
        [1] human-readable timestamp strings
        [2] Rad1h values
        [3] TTT (temperature, °C) values
        [4] PPPP (pressure) values
        [5] FF (wind speed) values

    MOSMIX_S (updated hourly) takes priority for overlapping timestamps.
    MOSMIX_L fills in the extended forecast window (up to 240 h) beyond MOSMIX_S.
    Returns a merged list of the same structure, sorted by ISO-8601 timestamp (column 0).
    """
    s_timestamps = set(mosmix_s[0])
    merged = [list(col) for col in mosmix_s]
    for idx, ts in enumerate(mosmix_l[0]):
        if ts not in s_timestamps:
            for col in range(len(merged)):
                merged[col].append(mosmix_l[col][idx])
    # ISO-8601 strings sort lexicographically, so a plain sort is correct
    rows = sorted(zip(*merged), key=lambda r: r[0])
    return [list(col) for col in zip(*rows)]


def connvertINTtimestamptoDWD(inputstring):
    """
    Convert a UNIX timestamp (float/int) to DWD UTC string format: YYYY-MM-DDTHH:MM:SS.sssZ
    """
    import time
    mysecondtime = (time.strftime('%Y-%m-%dT%H:%M:%S.%f', time.localtime(inputstring))[:-3]) + "Z"
    return mysecondtime
