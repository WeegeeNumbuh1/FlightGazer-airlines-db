#!/bin/bash
# Create/remove systemd service and timer that automatically
# runs the tar1090 patcher every day and upon startup
BASEDIR="$(cd "$(dirname -- "$0")" && pwd)"
SERVICE_PATH=/etc/systemd/system/flightgazer-airlinesdb-patcher.service
TIMER_PATH=/etc/systemd/system/flightgazer-airlinesdb-patcher.timer

echo "***** FlightGazer-airlines-db tar1090 patcher service installer *****"

service_heredoc() {
	cat <<- EOF > $SERVICE_PATH
	[Unit]
	Description=FlightGazer airlines database patcher for tar1090
	Documentation="https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db"

	[Service]
	User=root
	Type=oneshot
	Nice=19
	CPUSchedulingPolicy=idle
	IOSchedulingClass=idle
	ExecStart=/bin/bash "${BASEDIR}/tar1090_patcher.sh"
EOF
}

timer_heredoc() {
	cat <<- EOF > $TIMER_PATH
	[Unit]
	Description=Patches tar1090 with the FlightGazer airlines database daily or at startup
	Documentation="https://github.com/WeegeeNumbuh1/FlightGazer-airlines-db"

	[Timer]
	OnBootSec=5min
	OnCalendar=*-*-* 06:00:00
	Persistent=true
	RandomizedDelaySec=300

	[Install]
	WantedBy=timers.target
EOF
}

if [ "$(id -u)" -ne 0 ]; then
	>&2 echo ">>> ERROR: This script must be run as root."
	sleep 1s
	exit 1
fi

if systemctl list-unit-files flightgazer-airlinesdb-patcher.timer >/dev/null; then
	echo "Detected existing service, uninstalling."
	systemctl stop flightgazer-airlinesdb-patcher.timer >/dev/null 2>&1
	rm -f $TIMER_PATH >/dev/null 2>&1
	rm -f $SERVICE_PATH >/dev/null 2>&1
	systemctl daemon-reload
	systemctl reset-failed
	echo "Done."
else
	echo "Installing aircraft database patcher service."
	service_heredoc
	timer_heredoc
	systemctl daemon-reload
	systemctl enable flightgazer-airlinesdb-patcher.timer
	systemctl start flightgazer-airlinesdb-patcher.timer
	echo "Note: Don't move this directory (${BASEDIR}), it will break the service."
	echo ""
	echo "Run this script again to uninstall the service."
	echo "Done."
fi
exit 0