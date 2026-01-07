#!/usr/bin/env python3
"""
Test which fields are available in the API
"""

import requests
import json
import os
from urllib.parse import urljoin

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?",
    "timeout": 10,
    "verify_ssl": False
}

# Get session cookie
cookie_file = os.path.expanduser("~/.mr_session_cookie")
session = requests.Session()

if os.path.exists(cookie_file):
    with open(cookie_file, 'r') as f:
        cookie_str = f.read().strip()
        if cookie_str.startswith("PHPSESSID="):
            phpsessid = cookie_str.split("=", 1)[1]
            session.cookies.set('PHPSESSID', phpsessid)

# Test different field combinations
test_fields = [
    # Working baseline
    ["machine.serial_number", "machine.hostname"],
    # Try adding storage fields one at a time
    ["machine.serial_number", "machine.hostname", "storage.hdd_free"],
    ["machine.serial_number", "machine.hostname", "reportdata.hdd_free"],
    # Try full working set
    ["machine.serial_number", "machine.hostname", "machine.machine_desc", "reportdata.console_user", "reportdata.timestamp", "usage_stats.thermal_pressure", "usage_stats.cpu_idle"],
]

for fields in test_fields:
    url = urljoin(CONFIG['base_url'], 'dt_machines')
    
    columns_data = [{"name": field} for field in fields]
    
    payload = {
        "columns": columns_data,
        "draw": 1,
        "length": 5,
        "start": 0,
    }
    
    try:
        print(f"\nTesting: {fields}")
        r = session.post(url, data=payload, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
        data = r.json()
        print(f"  Status: {r.status_code}, Got {data.get('recordsTotal', 0)} records")
        if data.get('data'):
            print(f"  First row has {len(data['data'][0])} fields: {data['data'][0][:3]}...")
    except Exception as e:
        print(f"  Error: {e}")
