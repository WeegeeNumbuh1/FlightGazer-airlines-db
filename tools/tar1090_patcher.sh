#!/bin/bash
{
# patches the operators.js database on an existing tar1090 instance
# with the one from this repo.
# Assumes the only one instance at the default location!
# (multiple instances are not tested)
# by WeegeeNumbuh1

export PYTHONUNBUFFERED=1
TAR1090DIR='/usr/local/share/tar1090/html'
TAR1090DBVER=''
TAR1090DBDIR=''
TAR1090DBDIRFALLBACK='/usr/local/share/tar1090/git-db/db'

echo "***** FlightGazer-airlines-db Operators database patcher for tar1090 *****"

if [ `id -u` -ne 0 ]; then
	>&2 echo ">>> ERROR: This script must be run as root."
	sleep 1s
	exit 1
fi

if [ ! -d "${TAR1090DIR}" ]; then
    >&2 echo ">>> ERROR: tar1090 does not exist at ${TAR1090DIR}"
    sleep 1s
    exit 1
fi

TAR1090DBVER=$(sed -nE 's/.*let databaseFolder *= *"([^"]+)".*/\1/p' "${TAR1090DIR}/index.html")
if [ -z "${TAR1090DBVER}" ]; then
    echo "Could not find current database being used by tar1090."
    echo "Using fallback directory, ${TAR1090DBDIRFALLBACK}"
    TAR1090DBDIR="$TARTAR1090DBDIRFALLBACK"
else
    TAR1090DBDIR="${TAR1090DIR}/${TAR1090DBVER}"
    echo "Current database version detected: ${TAR1090DBVER}"
fi

if [ ! -d "${TAR1090DBDIR}" ]; then
    >&2 echo ">>> ERROR: tar1090 database directory ${TAR1090DBDIR} does not exist!"
    sleep 1s
    exit 1
fi

if [ ! -f "${TAR1090DBDIR}/operators.js" ]; then
    >&2 echo ">>> ERROR: could not find existing operators file!"
    sleep 1s
    exit 1
fi

read -r OWNER_OF_TAR1090 GROUP_OF_TAR1090 <<<$(stat -c "%U %G" "${TAR1090DBDIR}/operators.js")
echo "INFO: ${TAR1090DBDIR}/operators.js | Owner: ${OWNER_OF_TAR1090}, Group: ${GROUP_OF_TAR1090}"

echo "Fetching database and conversion tool..."
wget -q -O /tmp/operators.csv https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/operators.csv
wget -q -O /tmp/csv_to_tar1090.py https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/tools/csv_to_tar1090.py

echo "Converting..."
python3 /tmp/csv_to_tar1090.py "/tmp"
if [ ! -f '/tmp/operators.js' ]; then
    >&2 echo ">>> ERROR: failed to generate operators database!"
    echo "Cleaning up..."
    rm -f /tmp/operators.csv >/dev/null 2>&1
    rm -f /tmp/csv_to_tar1090.py >/dev/null 2>&1
    exit 1
fi
echo "Moving database to tar1090 directory..."
mv -f /tmp/operators.js "${TAR1090DBDIR}/operators.js"
chown -f ${OWNER_OF_TAR1090}:${GROUP_OF_TAR1090} "${TAR1090DBDIR}/operators.js" >/dev/null 2>&1
echo "Cleaning up..."
rm -f /tmp/operators.csv >/dev/null 2>&1
rm -f /tmp/csv_to_tar1090.py >/dev/null 2>&1
echo "********* Success. *********"
echo "You may have to clear your browser's cache and refresh the tar1090 page to see the changes."
exit 0
}