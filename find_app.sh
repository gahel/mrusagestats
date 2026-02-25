#!/bin/sh
#
# Script to find all machines with a specific app installed via munkireport datatables API
#
# Usage: ./find_app.sh [appname]
# Default app: Alfred5

MR_BASE_URL='https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'
MR_DATA_QUERY='/datatables/data'
MR_LOGIN='localuser'
MR_PASSWORD=$(security find-generic-password -a localuser -s munkireport-api -w)

APPNAME="${1:-Alfred5}"

CLIENT_COLUMNS=(
    "managedinstalls.name"
    "machine.serial_number"
    "machine.hostname"
    "machine.machine_desc"
    "reportdata.timestamp"
    "reportdata.reg_timestamp"
    "machine.os_version"
    "machine.physical_memory"
    "reportdata.remote_ip"
    "reportdata.console_user"
    "reportdata.long_username"
    "diskreport.totalsize"
    "diskreport.freespace"
    "diskreport.percentage"
    "machine.computer_name"
    "machine.buildversion"
    "munkireport.manifestname"
    "mdm_status.mdm_enrolled"
    "usage_stats.thermal_pressure"
    "usage_stats.cpu_idle"
    "usage_stats.cpu_sys"
    "usage_stats.cpu_user"
    "usage_stats.load_avg"
    "usage_stats.gpu_name"
    "usage_stats.gpu_freq_hz"
    "usage_stats.gpu_freq_mhz"
    "usage_stats.gpu_freq_ratio"
    "usage_stats.gpu_busy"
)

columns_to_query() {
    declare -a COLUMNS=("${!1}")
    MR_QUERY=""
    COL=0
    for i in "${COLUMNS[@]}"; do
        MR_QUERY="${MR_QUERY}columns[${COL}][name]=${i}&"
        COL=$((COL+1))
    done
    # Add search filter for appname on managedinstalls.name (column 0)
    MR_QUERY="${MR_QUERY}columns[0][search][value]=${APPNAME}&"
}

COOKIE_JAR=$(curl -s --cookie-jar - --data "login=${MR_LOGIN}&password=${MR_PASSWORD}" ${MR_BASE_URL}/auth/login)
SESSION_COOKIE=$(echo $COOKIE_JAR | sed -n 's/.*PHPSESSID[[:space:]]/PHPSESSID=/p')
CSRF_TOKEN=$(echo "$COOKIE_JAR" | sed -n 's/.*CSRF-TOKEN[[:space:]]/X-CSRF-TOKEN: /p')

columns_to_query CLIENT_COLUMNS[@]
OUTPUT=$(curl -s -H "$CSRF_TOKEN" --cookie "$SESSION_COOKIE" --data $MR_QUERY ${MR_BASE_URL}${MR_DATA_QUERY})

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="find_app_${APPNAME}_${TIMESTAMP}.json"
echo "$OUTPUT" > "$FILENAME"

echo $OUTPUT
