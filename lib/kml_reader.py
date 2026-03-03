# KML reading and parsing utilities for DWD forecast
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
            mynewtime = time.mktime(datetime.datetime.strptime(mytime, "%d-%b-%Y-%H:%M").timetuple())
            logging.debug("%s %s", ",GetURLForLatest :DWD Filetimestamp found :", mynewtime)
        if (elements.find("LATEST") > 0):
            counter = 1
    myurl = [urlpath + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return myurl, mynewtime


def extract_kml_from_zip(url, file_name="temp1.gz", targetdir="./KML"):
    try:
        with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            Myzipfilename = str(zip_ref.namelist()[0])
            zip_ref.extractall(targetdir)
        return targetdir + "/" + Myzipfilename
    except Exception as e:
        logging.error("Error extracting KML from zip: %s", e)
        return None


def parse_kml_file(kml_path):
    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
        return tree, root
    except Exception as e:
        logging.error("Error parsing KML file: %s", e)
        return None, None

