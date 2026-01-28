""" Script that converts the FlightGazer-airlines-db CSV into a format
that should be compatible with tar1090. """
# By: WeegeeNumbuh1

import sys
if __name__ != '__main__':
    print("This script cannot be imported as a module.")
    print("Run this directly from the command line.")
    sys.exit(1)

print("********** FlightGazer-aircraft-db to tar1090-db Generator **********\n")
from pathlib import Path
import csv
import gzip
from time import perf_counter

script_start = perf_counter()
current_path = Path(__file__).resolve().parent
write_path = Path(current_path, '..', 'operators.js')
source_path = Path(current_path, '..', 'operators.csv')

if not source_path.exists():
    print(f"ERROR: Cannot find \'{source_path}\'")
    sys.exit(1)

if write_path.exists():
    print(f"\'{write_path}\' already exists, overwriting.")

fg_ops = []
fg_ops.append("{")
csv_load = perf_counter()
default_country = 'Unknown or unassigned country'
linecount = 0
with open(source_path, newline='') as csvfile:
    # fieldnames=['3Ltr', 'Company', 'Country', 'Telephony', 'FriendlyName']
    reader = csv.DictReader(
        csvfile,
        delimiter=','
    )
    for row in reader:
        if not (country := row["Country"]):
            country = default_country
        subrow = (
            f'\"{row['3Ltr']}\":'
            '{'
            f'\"n\":\"{row["FriendlyName"]}\",'
            f'\"c\":\"{country}\",'
            f'\"r\":\"{row["Telephony"]}\"'
            '}'
        )
        fg_ops.append(subrow)
        fg_ops.append(',')
        linecount += 1
    _ = fg_ops.pop() # get rid of the closing comma
fg_ops.append('}')

print(f"Loaded {linecount} lines in {(perf_counter() - csv_load) * 1000:.2f} ms")
write_start = perf_counter()
fg_ops_str = ''.join(fg_ops).encode('utf-8')
with gzip.open(write_path, 'wb', compresslevel=9) as f:
    f.write(fg_ops_str)

print(f"Compressed {len(fg_ops_str) / 1024:.3f} KiB to "
      f"{(write_path.stat().st_size / 1024):.3f} KiB in "
      f"{(perf_counter() - write_start) * 1000:.3f} ms.")

print(f"\nTotal wall time: {perf_counter() - script_start:.3f} seconds.")
print("***** Done. *****")
sys.exit(0)