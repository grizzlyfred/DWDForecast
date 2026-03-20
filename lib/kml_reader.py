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
    # Extracts timevalue, Rad1h, TTT, PPPP, FF arrays for the given station from the KML root
    ns = {'dwd': 'https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd',
          'gx': 'http://www.google.com/kml/ext/2.2',
          'kml': 'http://www.opengis.net/kml/2.2',
          'atom': 'http://www.w3.org/2005/Atom',
          'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'}
    timestamps = root.findall('kml:Document/kml:ExtendedData/dwd:ProductDefinition/dwd:ForecastTimeSteps/dwd:TimeStep', ns)
    timevalue = [child.text for child in timestamps]
    Rad1h = TTT = PPPP = FF = None
    for elem in root.findall('./kml:Document/kml:Placemark', ns):
        mylocation = elem.find('kml:name', ns).text
        if mylocation == station:
            myforecastdata = elem.find('kml:ExtendedData', ns)
            for subelem in myforecastdata:
                attrib = str(subelem.attrib)
                if ": 'FF'" in attrib:
                    FF = list(subelem[0].text.split())
                if ": 'Rad1h'" in attrib:
                    Rad1h = list(subelem[0].text.split())
                if ": 'TTT'" in attrib:
                    TTT = list(subelem[0].text.split())
                    for i in range(len(TTT)):
                        TTT[i] = round(float(TTT[i]) - 273.13, 2)
                if ": 'PPPP'" in attrib:
                    PPPP = list(subelem[0].text.split())
    # Compose the mosmixdata array as in the original
    mosmixdata = []
    for _ in range(6):
        mosmixdata.append([0] * len(timevalue))
    for idx in range(len(timevalue)):
        # The second column is a human-readable timestamp, but we just copy the original string for now
        mosmixdata[0][idx] = timevalue[idx]
        mosmixdata[1][idx] = timevalue[idx].replace('T', ' ').replace('Z', '')
        mosmixdata[2][idx] = Rad1h[idx] if Rad1h else 0
        mosmixdata[3][idx] = TTT[idx] if TTT else 0
        mosmixdata[4][idx] = PPPP[idx] if PPPP else 0
        mosmixdata[5][idx] = FF[idx] if FF else 0
    return mosmixdata


def connvertINTtimestamptoDWD(inputstring):
    """
    Convert a UNIX timestamp (float/int) to DWD UTC string format: YYYY-MM-DDTHH:MM:SS.sssZ
    """
    import time
    mysecondtime = (time.strftime('%Y-%m-%dT%H:%M:%S.%f', time.localtime(inputstring))[:-3]) + "Z"
    return mysecondtime
