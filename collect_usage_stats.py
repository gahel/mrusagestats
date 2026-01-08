#!/usr/bin/env python3
"""
Collect usage_stats data hourly for trend analysis
Saves timestamped JSON files for tracking system performance over time
"""
import requests
import subprocess
import json
from datetime import datetime
import os

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Key performance indicators to collect
columns = [
    "machine.serial_number",
    "machine.hostname",
    "usage_stats.timestamp",
    "usage_stats.thermal_pressure",
    "usage_stats.package_watts",
    "usage_stats.gpu_busy",
    "usage_stats.gpu_freq_mhz",
    "usage_stats.backlight",
    "usage_stats.keyboard_backlight",
    "usage_stats.ibyte_rate",
    "usage_stats.obyte_rate",
    "usage_stats.rbytes_per_s",
    "usage_stats.wbytes_per_s",
    "usage_stats.rops_per_s",
    "usage_stats.wops_per_s",
    "usage_stats.freq_hz",
    "usage_stats.freq_ratio",
    "usage_stats.cpu_idle",
    "usage_stats.cpu_sys",
    "usage_stats.cpu_user",
    "usage_stats.load_avg",
]

# authenticate
auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False

try:
    auth_request = session.post(auth_url, data={"login": login, "password": password})
    
    if auth_request.status_code != 200:
        print(f"Authentication failed: {auth_request.status_code}")
        raise SystemExit
    
    headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}
    
    # Build query
    query_data = {f"columns[{i}][name]": c for i, c in enumerate(columns)}
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching usage_stats data...")
    response = session.post(query_url, data=query_data, headers=headers)
    result = response.json()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        raise SystemExit
    
    # Save data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"usage_stats_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "collected_at": datetime.now().isoformat(),
            "records": result['recordsFiltered'],
            "data": result['data']
        }, f, indent=2)
    
    # Also append to running history file
    history_file = "usage_stats_history.jsonl"
    with open(history_file, 'a') as f:
        for row in result['data']:
            record = {
                "collected_at": datetime.now().isoformat(),
                "serial_number": row[0],
                "hostname": row[1],
                "timestamp": row[2],
                "thermal_pressure": row[3],
                "package_watts": row[4],
                "gpu_busy": row[5],
                "gpu_freq_mhz": row[6],
                "backlight": row[7],
                "keyboard_backlight": row[8],
                "ibyte_rate": row[9],
                "obyte_rate": row[10],
                "rbytes_per_s": row[11],
                "wbytes_per_s": row[12],
                "rops_per_s": row[13],
                "wops_per_s": row[14],
                "freq_hz": row[15],
                "freq_ratio": row[16],
                "cpu_idle": row[17],
                "cpu_sys": row[18],
                "cpu_user": row[19],
                "load_avg": row[20],
            }
            f.write(json.dumps(record) + '\n')
    
    print(f"✓ Saved {result['recordsFiltered']} records to {filename}")
    print(f"✓ Appended to {history_file}")
    
except Exception as e:
    print(f"Error: {e}")
    raise SystemExit
