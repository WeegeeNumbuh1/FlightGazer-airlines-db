print("******** FlightGazer-airlines-db to python exporter ********")
# by: WeegeeNumbuh1

from time import perf_counter
import csv
from io import StringIO
from pathlib import Path
from argparse import ArgumentParser
import sys

current_dir = Path(__file__).resolve().parent
output = Path(current_dir, 'operators_export.py')
local_db_default = Path(current_dir.parent, 'operators.csv')
use_local = False
fg_db_verstr = 'Unknown'
parser = ArgumentParser(
    description = (
        "Python script for transforming the FlightGazer-airlines-db to a valid python lookup table. "
        "Only supports mapping the ICAO prefix to a single specified column."),
    epilog="Report bugs to WeegeeNumbuh1 <https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db>"
)
parser.add_argument(
    "type",
    type=str,
    nargs='?',
    default='friendly',
    help = (
        "[Optional] The mapping value. "
        "Valid entries: 'friendly', 'company', 'country', 'telephony'. "
        "Default: 'friendly'"
    ),
)
parser.add_argument(
    "-e", "--export",
    required=False,
    type=str,
    default=output,
    help = (
        "[Optional] Path to where the data will be exported. "
        f"(currently \'{output}\')"
    ),
)
parser.add_argument(
    "-l", "--local",
    required=False,
    nargs="?",
    default=-1,
    const=local_db_default,
    type=str,
    help = (
        "[Optional] Path to the current database. Skips fetching from online "
        "if the file is present. Using this flag without a path will assume "
        f"\'{local_db_default}\'"
    )
)

args = parser.parse_args()

extract_column: str = args.type
var_definition = None
extract_column_literal = ""
match (extract_column or '').lower().strip():
    case "friendly":
        var_definition = 'icao_to_name'
        extract_column_literal = 'FriendlyName'
    case "company":
        var_definition = 'icao_to_company'
        extract_column_literal = 'Company'
    case "country":
        var_definition = 'icao_to_country'
        extract_column_literal = 'Country'
    case "telephony":
        var_definition = 'icao_to_telephony'
        extract_column_literal = 'Telephony'
    case _:
        var_definition = 'icao_to_name'
        extract_column_literal = 'FriendlyName'
        print("Warning: Did not receive a valid export option.")
print(f"Extracting \'{extract_column_literal}\' data from the database.")

path_check = Path(args.export)
if (path_check.absolute().parent).exists():
    if not output.resolve() == path_check.resolve():
        output = path_check
else:
    print(f"\nCurrent filepath is invalid: \'{path_check}\'")
    print("Try to make the directory structure first.")
    sys.exit(1)

if args.local == -1:
    print("Going to fetch online version.")
else:
    if (local_db_path := Path(args.local)).exists():
        print(f"Using \'{local_db_path.absolute()}\'")
        local_db_default = local_db_path
        use_local = True
        fg_db_verstr = 'Offline - Indeterminate'
        if (local_ver := Path(local_db_path.parent, 'version')).exists():
            with open(local_ver, 'rb') as lv:
                try:
                    fg_db_verstr = lv.read(10).decode().strip()
                except Exception:
                    pass
                else:
                    print(f"Using database version: {fg_db_verstr}")

    else:
        print(f"Warning: Could not find provided database at \'{local_db_path}\'")
        print("Going to use online version.")

def fg_db_loader() -> dict:
    """ Parses a local FlightGazer airlines database. """
    csv_start = perf_counter()
    with open(local_db_default, 'r', encoding='utf-8') as db:
        csv_reader = csv.DictReader(db)
        try:
            data = {row['3Ltr']: row for row in csv_reader}
        except KeyError as e:
            print(f"Failed to parse CSV: {e}")
            return {}
    print(f"Processed {len(data)} entries in {(perf_counter() - csv_start) * 1000:.3} ms.")
    return data

def fg_db_fetcher() -> dict:
    """ Grab and parse the FlightGazer airlines database.
    Returns a dictionary in a form similar to the tar1090-db """
    """ Header: '3Ltr','Company','Country','Telephony','FriendlyName' """
    global fg_db_verstr
    try:
        import requests
    except ImportError:
        print("This script requires the 'requests' module.")
        print("You can install it using 'pip install requests'.")
        sys.exit(1)

    fetcher_session = requests.Session()
    fg_db = 'https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db/raw/refs/heads/master/operators.csv'
    fg_db_ver = 'https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db/raw/refs/heads/master/version'
    download_start = perf_counter()
    print("Fetching the FlightGazer-airlines-db database...")
    try:
        dataset2 = fetcher_session.get(fg_db, timeout=5)
        dataset2.raise_for_status()
        download_end = (perf_counter() - download_start)
        if dataset2.status_code != 200:
            raise requests.HTTPError(f'Got status code {dataset2.status_code}') from None
    except Exception as e:
        print(f"Failed to get data: {e}")
        return {}
    download_size = len(dataset2.content)
    print(f"Successfully downloaded {(download_size / (1024 * 1024)):.2f} "
         f"MiB of data in {download_end:.2f} seconds.")
    try:
        db_ver = fetcher_session.get(fg_db_ver, timeout=5)
        fg_db_verstr = db_ver.text.strip()
        print(f"Using database version: {fg_db_verstr}")
    except Exception:
        pass
    csv_start = perf_counter()
    csv_reader = csv.DictReader(StringIO(dataset2.text))
    try:
        data = {row['3Ltr']: row for row in csv_reader}
    except KeyError as e:
        print(f"Failed to parse CSV: {e}")
        return {}
    print(f"Processed {len(data)} entries in {(perf_counter() - csv_start) * 1000:.3} ms.")
    return data

if use_local:
    ops = fg_db_loader()
    if not ops:
        print("Failed to parse local database. Cannot continue.")
        sys.exit(1)
else:
    ops = fg_db_fetcher()
    if not ops:
        print("Failed to download database. Cannot continue.")
        sys.exit(1)

print(f"Writing to \'{output.absolute()}\'...")
start = perf_counter()
with open(output, 'w', encoding='utf-8') as f:
    f.write(f'# Data generated from the FlightGazer-airlines-db\n')
    f.write(f'# (https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db),\n')
    f.write(f'# and is licensed under the Open Data Commons Open Database License v1.0.\n')
    f.write(f'# Used FlightGazer-airlines-db: {fg_db_verstr}\n')
    f.write(f'{var_definition} = {{\n')
    for icao, data in ops.items():
        f.write(f'    \"{icao}\": \"{data[f'{extract_column_literal}']}\",\n')
    f.write('}')
print(f"Wrote {(output.stat().st_size / 1024):.3f} KiB in {(perf_counter() - start) * 1000:.3} ms.")
print("Done.")
sys.exit(0)