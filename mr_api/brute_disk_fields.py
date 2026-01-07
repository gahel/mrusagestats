#!/usr/bin/env python3
"""
Brute force test different disk_report field names
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

# Try different field name variations
test_fields = [
    "disk_report.mountpoint",
    "disk_report.mount",
    "disk_report.path",
    "disk_report.available",
    "disk_report.capacity",
    "disk_report.percent",
    "disk_report.hdd_free",
    "disk_report.hdd_total",
    "disk_report.free_space",
    "disk.free",
    "disk.size",
    "storage.free",
    "storage.size",
]

print("Testing individual disk fields (with machine.serial_number):\n")

for field in test_fields:
    cols = ["machine.serial_number", field]
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
                    print(f"✓ {field:<35} -> {data['data'][0][-1]}")
            except:
                pass
    except:
        pass
