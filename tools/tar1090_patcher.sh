#!/bin/bash
{
# Patches the operators.js database on an existing tar1090 instance
# or running ultrafeeder docker with the one from this repo.
# Assumes the only one instance at the default location!
# (multiple instances are not tested)
# by WeegeeNumbuh1

export PYTHONUNBUFFERED=1
BASEDIR="$(cd "$(dirname -- "$0")" && pwd)"
TAR1090DIR='/usr/local/share/tar1090/html'
TAR1090DIR_ULTRAFEEDER='/usr/local/share/tar1090/html-webroot'
TAR1090_NOW=''
TAR1090DBVER=''
TAR1090DBDIR=''
TAR1090DBDIRFALLBACK='/usr/local/share/tar1090/git-db/db'
OPS_JS=''
OPS_DB_AVAILABLE=false
OPS_DB_VERSION=''
IS_SCRIPT=true
SCRIPT_PATH=''
CONVERSION_TOOL="${BASEDIR}/csv_to_tar1090.py"
CSV_SOURCE="${BASEDIR}/../operators.csv"
WORKING_DIR="${BASEDIR}/.."
LAST_DB_CHECKFILE="${BASEDIR}/last_check"

help() {
	echo "Usage: $0 [-f | --file <path/to/operators.js>]"
}

echo "***** FlightGazer-airlines-db Operators database patcher for tar1090 *****"
while [[ $# -gt 0 ]]; do
	case "$1" in
		-f|--file)
			OPS_JS="$2"
			shift 2
			;;
		-h|--help)
			help
			exit 0
			;;
		*)
			echo "Unknown option: $1"
			help
			exit 1
			;;
	esac
done

if [ "$(id -u)" -ne 0 ]; then
	echo ">>> ERROR: This script must be run as root."
	sleep 1s
	exit 1
fi

if [[ -z ${BASH_SOURCE[0]:-} || $0 == "bash" || $0 == "-bash" ]]; then
	echo ">>> Currently running from stdin"
	IS_SCRIPT=false
else
	SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
	if [ ! -f "$SCRIPT_PATH" ]; then
		SCRIPT_PATH=''
	fi
fi

# only do the following if the whole repo structure is in place
if [ -f "$CONVERSION_TOOL" ] && [ -f "$CSV_SOURCE" ] && [ "$IS_SCRIPT" = true ]; then
	echo "Detected existing database and conversion tool, using those."
	OPS_DB_AVAILABLE=true
	if [ -f "$LAST_DB_CHECKFILE" ]; then
		NOWTIME=$(date '+%s')
		last_check_time=$(date -r "$LAST_DB_CHECKFILE" '+%s')
	else
		NOWTIME=0
		last_check_time=0
	fi
	if [ ! -f "$LAST_DB_CHECKFILE" ] || [ $((NOWTIME - last_check_time)) -gt 604800 ]; then
		echo "Checking if there's any updates to the database online while we're at it..."
		if [ -f "${BASEDIR}/../version" ]; then
			OPS_DB_VERSION=$(head -c 20 "${BASEDIR}/../version")
			if [ -z "$OPS_DB_VERSION" ]; then
				echo "Could not determine local database version"
			else
				echo "Current version: ${OPS_DB_VERSION}"
			fi
		fi
		LATEST_VER="$(wget --timeout=5 --tries=2 -q -O - "https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db/raw/refs/heads/master/version")"
		if [ -z "$LATEST_VER" ]; then
			echo "Could not determine latest version of FlightGazer-airlines-db."
			echo "Continuing."
		else
			echo "Version online:  ${LATEST_VER}"
			touch "$LAST_DB_CHECKFILE"
		fi
		if [ ! -z "$LATEST_VER" ] && [ "$OPS_DB_VERSION" != "$LATEST_VER" ]; then
			echo "Grabbing latest database..."
			wget --timeout=5 --tries=2 -O "$CSV_SOURCE" "https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/operators.csv"
			echo -e "\033[2m"
			python3 "$CONVERSION_TOOL" "$WORKING_DIR"
			echo -e "\033[0m"
		elif [ "$OPS_DB_VERSION" != "$LATEST_VER" ]; then
			echo "No need to update database."
		fi
	fi
	if [ ! -f "${WORKING_DIR}/operators.js" ]; then
		echo "Did not detect an operators.js file, creating that first."
		echo -e "\033[2m"
		python3 "$CONVERSION_TOOL" "$WORKING_DIR"
		echo -e "\033[0m"
	fi
else
	CONVERSION_TOOL=/tmp/csv_to_tar1090.py
	CSV_SOURCE=/tmp/operators.csv
	WORKING_DIR=/tmp
fi

# check if we already have an operators.js file we can just copy over
if [ -z "$OPS_JS" ]; then
	if [ -f "${BASEDIR}/../operators.js" ]; then
		OPS_JS="${BASEDIR}/../operators.js"
		echo "Found a local copy of the operators.js file at ${OPS_JS}"
	elif [ -f "${BASEDIR}/operators.js" ]; then
		OPS_JS="${BASEDIR}/operators.js"
		echo "Found a local copy of the operators.js file at ${OPS_JS}."
	fi
else
	if [ ! -f "${OPS_JS}" ]; then
		echo "Could not find ${OPS_JS}"
		echo "Continuing with automated conversion."
		OPS_JS=''
	else
		echo "Using ${OPS_JS} directly, skipping intermediate conversion."
	fi
fi

if command -v docker >/dev/null 2>&1 && docker ps --format "{{.Names}}" | grep "ultrafeeder" >/dev/null; then
	DOCKER_RUN_SUCCESS=1
	echo "Detected a running ultrafeeder docker container. Patching that instead."
	echo ""
	echo "****** BEGIN CONTAINER OUTPUT ******"
	echo "************************************"
	echo ""
	echo -e "\033[2m"
	if [ ! -z "$OPS_JS" ]; then
		# copy the local operators.js to the container...
		echo "Copying over the operators.js file..."
		docker cp "$OPS_JS" ultrafeeder:/tmp/operators.js
		if [ "$IS_SCRIPT" = true ] && [ ! -z "$SCRIPT_PATH" ]; then
			# ...then just use this script to figure out the rest and copy it to the right place
			echo "Sending a copy of this script to the container and running it there..."
			docker cp "${SCRIPT_PATH}" ultrafeeder:/tmp/tar1090_patcher.sh 
			docker exec ultrafeeder bash /tmp/tar1090_patcher.sh -f /tmp/operators.js
			DOCKER_RUN_SUCCESS=$?
		else
			# ...or grab the online copy and use it to do the work
			echo "Fetching the online copy of this script again to run inside the container..."
			docker exec ultrafeeder bash -c "$(wget -nv -O - https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/tools/tar1090_patcher.sh)" -f /tmp/operators.js
			DOCKER_RUN_SUCCESS=$?
		fi
	else
		# old fallback; just do everything
		docker exec ultrafeeder bash -c "$(wget -nv -O - https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/tools/tar1090_patcher.sh)"
		DOCKER_RUN_SUCCESS=$?
	fi
	if [ $DOCKER_RUN_SUCCESS -eq 0 ]; then
		echo ""
		echo -e "\033[0m"
		echo "************************************"
		echo "******* END CONTAINER OUTPUT *******"
		echo ""
		echo "Exited container. Patch applied successfully."
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

# make the operators.js file
if [ -z "$OPS_JS" ]; then
	if [ "$OPS_DB_AVAILABLE" = false ]; then
		echo "Fetching database and conversion tool..."
		LATEST_VER="$(wget -q -O - "https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db/raw/refs/heads/master/version")"
		if [ -z "$LATEST_VER" ]; then
			echo "Could not determine latest version of FlightGazer-airlines-db!"
		else
			echo "Got database version: ${LATEST_VER}"
		fi
		wget -q -O /tmp/operators.csv https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/operators.csv
		wget -q -O /tmp/csv_to_tar1090.py https://raw.githubusercontent.com/WeegeeNumbuh1/FlightGazer-airlines-db/refs/heads/master/tools/csv_to_tar1090.py
	fi

	echo "Converting..."
	python3 "$CONVERSION_TOOL" "$WORKING_DIR"
	if [ ! -f "${WORKING_DIR}/operators.js" ]; then
		echo ">>> ERROR: failed to generate operators database!"
		if [ "$OPS_DB_AVAILABLE" = false ]; then
			echo "Cleaning up..."
			rm -f /tmp/operators.csv >/dev/null 2>&1
			rm -f /tmp/csv_to_tar1090.py >/dev/null 2>&1
			exit 1
		fi
	fi
	echo "Moving operators database to tar1090 directory..."
	cp -f "${WORKING_DIR}/operators.js" "${TAR1090DBDIR}/operators.js"
else
	echo "Moving operators database to tar1090 directory..."
	cp -f "$OPS_JS" "${TAR1090DBDIR}/operators.js"
fi
chown -f ${OWNER_OF_TAR1090}:${GROUP_OF_TAR1090} "${TAR1090DBDIR}/operators.js" >/dev/null 2>&1
echo "Cleaning up..."
rm -f /tmp/operators.js >/dev/null 2>&1
rm -f /tmp/operators.csv >/dev/null 2>&1
rm -f /tmp/csv_to_tar1090.py >/dev/null 2>&1
echo "********* Success. *********"
echo "You may have to clear your browser's cache and refresh the tar1090 page to see the changes."
exit 0
}