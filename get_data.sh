#!/bin/sh
#
# Script to run automated queries against the munkireport datatables API
#
# Results are returned in JSON format
# The actual entries are in the 'data' variable
#
# To make this work, set up a regular user in munkireport and adjust the 
# proper values below
#
# Author: Arjen van Bochoven
# Date: 2015-11-06
# Modified: 2020-03-31 Added CSRF support

# Retrieve data from munkireport
# DEBUG=1
MR_BASE_URL='https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'
MR_DATA_QUERY='/datatables/data'
MR_LOGIN='localuser'
MR_PASSWORD=$(security find-generic-password -a localuser -s munkireport-api -w)

CLIENT_COLUMNS=(
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

# Create query from columns
columns_to_query()
{
    # Pick up array as argument
    declare -a COLUMNS=("${!1}")
    
    MR_QUERY=""
    COL=0
    for i in "${COLUMNS[@]}"; do
        MR_QUERY="${MR_QUERY}columns[${COL}][name]=${i}&"
        COL=$((COL+1))
    done
}

# Authenticate and capture cookie
if [ $DEBUG ]; then echo 'Authenticating to munkireport..'; fi
COOKIE_JAR=$(curl -s --cookie-jar - --data "login=${MR_LOGIN}&password=${MR_PASSWORD}" ${MR_BASE_URL}/auth/login)
SESSION_COOKIE=$(echo $COOKIE_JAR | sed -n 's/.*PHPSESSID[[:space:]]/PHPSESSID=/p')
CSRF_TOKEN=$(echo "$COOKIE_JAR" | sed -n 's/.*CSRF-TOKEN[[:space:]]/X-CSRF-TOKEN: /p')

# Retrieve data with session cookie
columns_to_query CLIENT_COLUMNS[@]
if [ $DEBUG ]; then echo 'Retrieving client data..'; fi
OUTPUT=$(curl -s -H "$CSRF_TOKEN" --cookie "$SESSION_COOKIE" --data $MR_QUERY ${MR_BASE_URL}${MR_DATA_QUERY})

# Save JSON to file with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="get_data_${TIMESTAMP}.json"
echo "$OUTPUT" > "$FILENAME"

echo $OUTPUT

