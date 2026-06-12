#!/bin/bash
{
# Patches the operators.js database on an existing tar1090 instance
# or running ultrafeeder docker with the one from this repo.
# Assumes the only one instance at the default location!
# (multiple instances are not tested)
# by WeegeeNumbuh1

export PYTHONUNBUFFERED=1
TAR1090DIR='/usr/local/share/tar1090/html'
TAR1090DIR_ULTRAFEEDER='/usr/local/share/tar1090/html-webroot'
TAR1090_NOW=''
TAR1090DBVER=''
TAR1090DBDIR=''
TAR1090DBDIRFALLBACK='/usr/local/share/tar1090/git-db/db'

echo "***** FlightGazer-airlines-db Operators database patcher for tar1090 *****"

if [ `id -u` -ne 0 ]; then
	echo ">>> ERROR: This script must be run as root."
	sleep 1s
	exit 1
fi

if command -v docker >/dev/null 2>&1; then
    if docker ps --format "{{.Names}}" | grep "ultrafeeder" >/dev/null; then
        echo "Detected a running ultrafeeder docker container. Patching that instead."
        echo "Running this script on the container itself..."
        echo ""
        echo "****** BEGIN CONTAINER OUTPUT ******"
        echo "************************************"
        echo ""
        echo -e "\033[2m"
        docker exec ultrafeeder bash -c "$(wget -nv -O - https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/tools/tar1090_patcher.sh)"
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "\033[0m"
            echo "************************************"
            echo "******* END CONTAINER OUTPUT *******"
            echo ""
            echo "Exited container. Patch applied successfully."
            # echo "Restarting container to see the changes..."
            # docker restart ultrafeeder >/dev/null
            echo "Done."
            exit 0
        else
            echo ""
            echo -e "\033[0m"
            echo "************************************"
            echo "******* END CONTAINER OUTPUT *******"
            echo ""
            echo "Exited container. Patch was unsuccessful. No changes have been made."
            exit 1
        fi
    fi
fi

if [ -d "${TAR1090DIR}" ]; then
    TAR1090_NOW="${TAR1090DIR}"
elif [ -d "${TAR1090DIR_ULTRAFEEDER}" ]; then
    TAR1090_NOW="${TAR1090DIR_ULTRAFEEDER}"
else
    echo ">>> ERROR: Could not find tar1090!"
    echo "Checked: ${TAR1090DIR} and ${TAR1090DIR_ULTRAFEEDER}"
    sleep 1s
    exit 1
fi

TAR1090DBVER=$(sed -nE 's/.*let databaseFolder *= *"([^"]+)".*/\1/p' "${TAR1090_NOW}/index.html")
if [ -z "${TAR1090DBVER}" ]; then
    echo "Could not find current database being used by tar1090."
    echo "Using fallback directory, ${TAR1090DBDIRFALLBACK}"
    TAR1090DBDIR="$TARTAR1090DBDIRFALLBACK"
else
    TAR1090DBDIR="${TAR1090_NOW}/${TAR1090DBVER}"
    echo "Current database version detected: ${TAR1090DBVER}"
fi

if [ ! -d "${TAR1090DBDIR}" ]; then
    echo ">>> ERROR: tar1090 database directory ${TAR1090DBDIR} does not exist!"
    sleep 1s
    exit 1
fi

if [ ! -f "${TAR1090DBDIR}/operators.js" ]; then
    echo ">>> ERROR: could not find existing operators file!"
    sleep 1s
    exit 1
fi

read -r OWNER_OF_TAR1090 GROUP_OF_TAR1090 <<<$(stat -c "%U %G" "${TAR1090DBDIR}/operators.js")
echo "INFO: ${TAR1090DBDIR}/operators.js | Owner: ${OWNER_OF_TAR1090}, Group: ${GROUP_OF_TAR1090}"

echo "Fetching database and conversion tool..."
LATEST_VER="$(wget -q -O - "https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db/raw/refs/heads/master/version")"
if [ -z $LATEST_VER ]; then
	echo "Could not determine latest version of FlightGazer-airlines-db!"
    echo "This may not work..."
else
	echo "Current database version: ${LATEST_VER}"
fi
wget -q -O /tmp/operators.csv https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/operators.csv
wget -q -O /tmp/csv_to_tar1090.py https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/tools/csv_to_tar1090.py

echo "Converting..."
python3 /tmp/csv_to_tar1090.py "/tmp"
if [ ! -f '/tmp/operators.js' ]; then
    echo ">>> ERROR: failed to generate operators database!"
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