#!/bin/bash
# Wrapper script for cron to collect usage_stats every hour

cd /Users/gaute/scripts/mr_api2
/Users/gaute/scripts/mr_api2/.venv/bin/python3 collect_usage_stats.py >> /Users/gaute/scripts/mr_api2/collect_usage_stats.log 2>&1
