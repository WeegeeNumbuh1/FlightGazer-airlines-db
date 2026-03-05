""" Script that downloads the FAA's list of ICAO airline codes and formats it into a CSV.
Additionally grabs data from other known airline 'databases' and compiles it into this CSV as well.
This was modified from the FlightGazer
(https://github.com/WeegeeNumbuh1/FlightGazer) project's `operators_generator.py` file. """

""" Programmer's notes:
This generates a CSV that *needs* manual evaluation afterwards;
the generated CSV is not fit for end-use.
To see changes on the FAA's side:
https://www.faa.gov/air_traffic/publications/atpubs/cnt_html/chap0_cam.html """
# by WeegeeNumbuh1
# Originally based on Flightgazer version v.9.9.1

import sys

if __name__ != '__main__':
    print("This script cannot be imported as a module.")
    print("Run this directly from the command line.")
    sys.exit(1)

print("********** FlightGazer-aircraft-db Operator Database Importer **********\n")

from time import perf_counter
script_start = perf_counter()
from pathlib import Path
import datetime

datenow = datetime.datetime.now(tz=datetime.timezone.utc)
date_gen_str = datenow.strftime("%Y-%m-%dT%H%M%SZ")
current_path = Path(__file__).resolve().parent
write_path = Path(current_path,
                  f'operators_to_evaluate_[{date_gen_str}].csv')
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

old_version = None
old_version_time = None

import unicodedata
import gzip
import ast
import csv
from io import StringIO
try:
    import requests
except ImportError:
    print("This script requires the 'requests' module.")
    print("You can install it using 'pip install requests'.")
    sys.exit(1)
try:
    from bs4 import BeautifulSoup as bs
except ImportError:
    print("This script requires the 'beautifulsoup4' module.")
    print("You can install it using 'pip install beautifulsoup4'.")
    sys.exit(1)
try:
    from fake_useragent import UserAgent
except ImportError:
    print("This script requires the 'fake_useragent' module.")
    print("You can install it using 'pip install fake-useragent'.")
    sys.exit(1)

FAA_source = 'https://www.faa.gov/air_traffic/publications/atpubs/cnt_html/chap3_section_3.html'
tar1090db = 'https://github.com/wiedehopf/tar1090-db/raw/refs/heads/master/db/operators.js'
tar1090db_ver = 'https://raw.githubusercontent.com/wiedehopf/tar1090-db/refs/heads/master/version'

header_str = "3Ltr,Company,Country,Telephony,tar1090-db,Wikipedia,airlines,fr24\n"

user = UserAgent(browsers=['Chrome', 'Edge', 'Firefox'], platforms='desktop')
HTML_header = {'User-Agent': str(user.random)}

def dict_lookup(
        list_of_dicts: list,
        key: str,
        search_term: str,
        return_all=False
    ) -> list[dict] | dict | None:
    """ Function pulled directly from FlightGazer. Set `return_all` to `True` to return
    all matches, if not, returns a dict of the first matching result.
    Returns `None` for no result. """
    if not search_term:
        return None
    results = []
    try:
        for dict_ in [x for x in list_of_dicts if x.get(key) == search_term]:
            if not return_all:
                return dict_
            else:
                results.append(dict_)
        if results:
            return results
        else:
            return None
    except Exception:
        return None

def strip_accents(s: str, skip_fallback: bool = False) -> str:
    """ Taken directly from FlightGazer.
    Falls back to substituting an underscore if the resultant string isn't fully ASCII,
    unless `skip_fallback` is True. This can also de-Zalgo text as a neat side-effect.
    ### Examples:
    >>> Manhattan Café -> Manhattan Cafe
    >>> Matikanetannhäuser -> ̶M̶a̶m̶b̶o̶  Matikanetannhauser
    >>> bröther may i have some ōâtš -> brother may i have some oats
    >>> “Peau Vavaʻu” -> _Peau Vava_u_

    ### References
    https://stackoverflow.com/a/518232 """
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                    if unicodedata.category(c) != 'Mn')
    if skip_fallback:
        return s
    if s.isascii():
        return s
    else:
        return ''.join([s_ if s_.isascii() else "_" for s_ in s])

def normalize(s: str) -> str:
    """ Removes excess whitespace and ensures everything is a single line """
    try:
        return " ".join(s.split()).strip()
    except Exception:
        return s

def extractor() -> dict | None:
    """ Download the compressed operators database from tar1090-db and return
    a dictionary of it for use later. Returns None for any failure. """
    """ Programmer's notes: the file is a javascript 'database' that's conveniently
    in the form of {'ABC': {'n': name, 'c': country, 'r': callsign/telephony}, ...} """
    print("> Downloading operators database from tar1090-db...")
    try:
        tar1090db_verstr = 'Unknown'
        download_start = perf_counter()
        dataset3 = requests.get(tar1090db, headers=HTML_header, timeout=5)
        download_end = (perf_counter() - download_start)
        dataset3.raise_for_status()
        if dataset3.status_code != 200:
            raise requests.HTTPError(f'Got status code {dataset3.status_code}') from None
        try:
            db_ver = requests.get(tar1090db_ver, headers=HTML_header, timeout=5)
            tar1090db_verstr = db_ver.text.strip()
        except Exception:
            pass
        download_size = len(dataset3.content)
        print(f"Successfully downloaded {(download_size / (1024 * 1024)):.2f} "
              f"MiB of data in {download_end:.2f} seconds.")
        print(f"Database version: {tar1090db_verstr}")
        print("Decompressing data...")
        decompressed = gzip.decompress(dataset3.content)
        return ast.literal_eval(decompressed.decode('utf-8'))
    except Exception as e:
        print(f"Failed to get database: {e}")
        return None

def wikipedia_fetcher() -> list[dict]:
    """ Grab data from Wikipedia for our operator friendly names.
    Returns a list of dictionaries, each with the keys
    {'IATA', 'ICAO', 'Airline', 'Call sign', 'Country/Region', 'Comments'}.
    If any error occurs, returns an empty list. """
    print("> Downloading supplementary info from Wikipedia...")
    download_start = perf_counter()
    try:
        dataset2 = requests.get('https://en.wikipedia.org/wiki/List_of_airline_codes', headers=HTML_header, timeout=5)
        dataset2.raise_for_status()
        download_end = (perf_counter() - download_start)
        if dataset2.status_code != 200:
            raise requests.HTTPError(f'Got status code {dataset2.status_code}') from None
    except Exception as e:
        print(f"Failed get data from Wikipedia: {e}")
        return []

    download_size = len(dataset2.content)
    print(f"Successfully downloaded {(download_size / (1024 * 1024)):.2f} "
         f"MiB of data in {download_end:.2f} seconds.")
    find_start = perf_counter()
    print("Sorting data...")
    html2 = dataset2.text
    soup2 = bs(html2, 'html.parser')
    data_wikipedia = []
    print("Extracting data...")
    tables = soup2.find_all('table')
    entries_to_ignore_contains = [
        'efunct', # Defunct
        'ormerly', # Formerly
        'no longer allocated'
    ]
    blank = {
        'IATA': None,
        'ICAO': None,
        'Airline': None,
        'Call sign': None,
        'Country/Region': None,
        'Comments': None
    }
    print("Validating data...")
    try:
        for table in tables:
            headers = [th.get_text(strip=True, separator=" ") for th in table.find_all('th')]
            for row in table.find_all('tr'):
                cells = [td.get_text(strip=True, separator=" ") for td in row.find_all('td')]
                if cells:
                    data_wikipedia.append({k:v for k,v in zip(headers, cells)})
        for i, entry in enumerate(data_wikipedia):
            # for telephony comparison; ensure the string is in the same case
            comment = entry.get('Comments', '')
            if any(substring in comment for substring in entries_to_ignore_contains):
                data_wikipedia[i] = blank
                continue
            if entry.get('Call sign', ''):
                data_wikipedia[i]['Call sign'] = strip_accents(entry['Call sign'].strip().upper())

    except Exception as e:
        print(f"Failed to parse data from Wikipedia: {e}")
        return []

    print(f"Parsed {len(data_wikipedia)} rows from Wikipedia "
          f"in {(perf_counter() - find_start):.2f} seconds.")
    return data_wikipedia

def fr24_reader() -> list[dict]:
    """ Parse Flightradar24's airlines list.
    Returns a list of dicts, {`3Ltr`, `Name`} """
    print("> Downloading supplementary info from Flightradar24...")
    download_start = perf_counter()
    try:
        dataset4 = requests.get('https://www.flightradar24.com/data/airlines', headers=HTML_header, timeout=5)
        dataset4.raise_for_status()
        download_end = (perf_counter() - download_start)
        if dataset4.status_code != 200:
            raise requests.HTTPError(f'Got status code {dataset4.status_code}') from None
    except Exception as e:
        print(f"Failed get data from Flightradar24: {e}")
        return []
    download_size = len(dataset4.content)
    print(f"Successfully downloaded {(download_size / (1024 * 1024)):.2f} "
         f"MiB of data in {download_end:.2f} seconds.")
    find_start = perf_counter()
    soup = bs(dataset4.text, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) != 1: # there should only be 1 main table
        print(f"Received incorrect amount of tables ({len(tables)}) than expected "
              "from Flightradar24, no data will be returned.")
        return []
    cells = []
    data_fr24 = []
    for table in tables:
        for row in table.find_all('tr'):
            cell = [td.get_text(strip=True, separator=" ") for td in row.find_all('td')]
            cells.append(cell)
    for row in cells:
        # table layout: | [margin] | logo | Name | 3Ltr | aircraft count | [margin] | == 6
        # category header: | [margin] | category (1st number or letter) | [margin] | [margin] | == 4
        if len(row) == 6:
            ltr_ = row[3].split()
            if len(ltr_) > 1: # ex: 'IATA / ICAO'
                ltr = ltr_[-1]
            else:
                ltr = ltr_[0]
            airline = {
                '3Ltr': normalize(ltr.upper()),
                'Name': strip_accents(row[2])
            }
            data_fr24.append(airline)

    print(f"Parsed {len(data_fr24)} rows from Flightradar24 "
          f"in {(perf_counter() - find_start):.2f} seconds.")
    return data_fr24

def csv_reader() -> dict:
    """ Pulls data from `airlines_csv` into a usable dict. """
    """ Headers: Code, Name, ICAO, IATA, PositioningFlightPattern, CharterFlightPattern """
    airlines_csv = 'https://github.com/tomcarman/skystats/raw/9bc0cc4e0827c89176d2805cc67cf800f099eb03/data/airlines.csv'
    download_start = perf_counter()
    print("> Pulling additional data...")
    try:
        dataset3 = requests.get(airlines_csv, headers=HTML_header, timeout=5)
        dataset3.raise_for_status()
        download_end = (perf_counter() - download_start)
        if dataset3.status_code != 200:
            raise requests.HTTPError(f'Got status code {dataset3.status_code}') from None
    except Exception as e:
        print(f"Failed get data: {e}")
        return {}
    download_size = len(dataset3.content)
    print(f"Successfully downloaded {(download_size / (1024 * 1024)):.2f} "
         f"MiB of data in {download_end:.2f} seconds.")
    csv_start = perf_counter()
    csv_reader = csv.DictReader(StringIO(dataset3.text))
    try:
        data = {row['\ufeffCode']: row for row in csv_reader}
    except KeyError:
        print(f"Failed to parse CSV: {e}")
        return {}
    print(f"Processed {len(data)} entries in {(perf_counter() - csv_start) * 1000:.3} ms.")
    return data

print("> Downloading data from the FAA...")
try:
    download1 = perf_counter()
    dataset = requests.get(FAA_source, headers=HTML_header, timeout=5)
    dataset.raise_for_status()
except Exception as e:
    print(f"Failed to get data: {e}")
    print("Cannot continue, please try again at a later time.")
    sys.exit(1)

download_size = len(dataset.content)
print(f"Successfully downloaded {(download_size / (1024 * 1024)):.2f} "
        f"MiB of data in {(perf_counter() - download1):.2f} seconds.")
print("Parsing HTML...")
parse_start = perf_counter()
html = dataset.text
soup = bs(html, 'html.parser')
print(f"Data parsed in {(perf_counter() - parse_start):.2f} seconds.")
data2 = []
friendly_available = True
data_tar1090 = extractor()
data2 = wikipedia_fetcher()
data3 = csv_reader()
data4 = fr24_reader()

print(f"Writing to {write_path}...")

write_start = perf_counter()
linecount = 0
with open(write_path, 'w', encoding='utf-8') as file:
    file.write(header_str)
    for i, table in enumerate(soup.find_all('table')):
        rows = table.find_all('tr')
        for j, row in enumerate(rows):
            cols = row.find_all('td')
            if len(cols) > 0:
                ICAO_name = strip_accents(cols[0].text.strip().upper())
                friendly = ''
                friendly2 = ''
                entry: dict = data_tar1090.get(ICAO_name, {})
                friendly = strip_accents(entry.get('n', ''))
                entry2: dict = data3.get(ICAO_name, {})
                friendly3 = strip_accents(entry2.get('Name', ''))
                if not (entry3 := dict_lookup(data4, '3Ltr', ICAO_name)):
                    friendly4 = ''
                else:
                    friendly4 = entry3.get('Name', '')
                if data2:
                    if (matching_entries := dict_lookup(
                        data2, 'ICAO', ICAO_name, return_all=True)) is not None:
                        for entry in matching_entries:
                            if cols[3].text.strip().upper() == entry.get('Call sign', ''):
                                # callsign from the FAA and Wikipedia matches, use this name
                                consideration = entry
                                friendly2 = strip_accents(entry.get('Airline', ''))
                                break
                        if consideration and not cols[2].text.strip() in consideration.get('Country/Region', '').upper():
                            # if the country does not match (name got reallocated somewhere else) don't use this result
                            friendly2 = ''

                    # would be "faster" if the normalization was done just once, but eh
                    ltr = normalize(cols[0].text)
                    company = normalize(cols[1].text)
                    country = normalize(cols[2].text)
                    telephony = normalize(cols[3].text)
                    tar1090db = normalize(friendly)
                    wikipedia = normalize(friendly2)
                    airlines = normalize(friendly3)
                    fr24 = normalize(friendly4)

                file.write(
                    f"\"{ltr}\","
                    f"\"{company}\","
                    f"\"{country}\","
                    f"\"{telephony}\","
                    f"\"{tar1090db}\","
                    f"\"{wikipedia}\","
                    f"\"{airlines}\","
                    f"\"{fr24}\"\n"
                )

        print(f"Wrote table '{alphabet[i]}' with {j} entries.")
        linecount += j

print(f"A total of {linecount} entries were written in "
      f"{(perf_counter() - write_start):.2f} seconds.")
print(f"Resulting file size: {(write_path.stat().st_size) / (1024):.3f} KiB.")

print("\nIMPORTANT: This generated CSV needs to be manually reviewed and analyzed.\n")

print(f"Total wall time: {perf_counter() - script_start:.2f} seconds.")
print("\n***** Done. *****")
sys.exit(0)