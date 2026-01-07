#!/usr/bin/env python3
"""
Query the disk_report module for storage data
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

# Try querying disk_report module via datatables/data
url = urljoin(CONFIG['base_url'], '/datatables/data')

# Test various field names from disk_report module
test_columns = [
    ["machine.serial_number", "disk_report.mount_point", "disk_report.free"],
    ["machine.hostname", "disk_report.size", "disk_report.used"],
    ["disk_report.mount_point", "disk_report.free", "disk_report.used", "disk_report.size"],
]

print("Testing disk_report module fields:\n")

for cols in test_columns:
    query_data = {f"columns[{i}][name]": col for i, col in enumerate(cols)}
    query_data.update({
        "draw": 1,
        "length": 1,
        "start": 0,
    })
    
    try:
        r = session.post(url, data=query_data, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
        
        if r.status_code == 200:
            try:
                data = r.json()
                if data.get('data') and len(data['data']) > 0:
                    row = data['data'][0]
                    print(f"✓ Got data with {len(cols)} columns:")
                    for i, col in enumerate(cols):
                        print(f"    {col:<35} = {row[i] if i < len(row) else 'N/A'}")
                else:
                    print(f"✗ No data for columns: {cols}")
            except Exception as e:
                print(f"✗ Invalid JSON: {str(e)[:50]}")
        else:
            print(f"✗ Status {r.status_code}: {cols}")
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
    
    print()
