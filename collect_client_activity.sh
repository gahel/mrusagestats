#!/bin/bash
# Wrapper script for å samle client activity data
# Kan brukes direkte eller via cron

cd "$(dirname "$0")"
source .venv/bin/activate
python3 client_activity_collector.py >> /tmp/client_activity.log 2>&1
