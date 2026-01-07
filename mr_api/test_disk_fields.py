#!/usr/bin/env python3
"""
Test which disk-related field names work with the API
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

url = urljoin(CONFIG['base_url'], '/datatables/data')

# Base columns that work
BASE_COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
]

# Test these disk-related field combinations
test_fields = [
    "storage.hdd_free",
    "storage.hdd_total",
    "reportdata.hdd_free",
    "reportdata.hdd_total",
    "storage.volume_free",
    "storage.volume_total",
    "reportdata.free",
    "reportdata.disk_free",
    "usage_stats.storage_free",
]

print("Testing disk-related field names:\n")

for field in test_fields:
    COLUMNS = BASE_COLUMNS + [field]
    
    # Format as the API expects
    query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
    query_data.update({
        "draw": 1,
        "length": 1,
        "start": 0,
    })
    
    try:
        r = session.post(url, data=query_data, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
        
        if r.status_code == 200:
            data = r.json()
            if data.get('data') and len(data['data']) > 0:
                print(f"✓ {field:<35} -> {data['data'][0][-1]}")
            else:
                print(f"✗ {field:<35} -> No data returned")
        else:
            print(f"✗ {field:<35} -> Status {r.status_code}")
    except Exception as e:
        print(f"✗ {field:<35} -> Error: {str(e)[:40]}")
