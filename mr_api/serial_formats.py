#!/usr/bin/env python3
"""
Try /report/disk_report with serial as different parameter formats
"""

import requests
import json
import os
from urllib.parse import urljoin

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net",
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

# Get a machine serial
machines_url = f"{CONFIG['base_url']}/index.php?/datatables/data"
query_data = {
    "columns[0][name]": "machine.serial_number",
    "columns[1][name]": "machine.hostname",
    "draw": 1,
    "length": 1,
    "start": 0,
}

r = session.post(machines_url, data=query_data, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
data = r.json()
serial = data['data'][0][0]
hostname = data['data'][0][1]
print(f"Machine: {hostname} ({serial})\n")

# Try with serial in different ways
tests = [
    ("GET", f"{CONFIG['base_url']}/report/disk_report/{serial}", {}),
    ("POST with serial in path", f"{CONFIG['base_url']}/index.php?/report/disk_report/{serial}", {}),
    ("POST with query param", f"{CONFIG['base_url']}/index.php?/report/disk_report", {"serial": serial}),
    ("POST with data", f"{CONFIG['base_url']}/report/disk_report", {"serial_number": serial}),
]

for method_name, url, params in tests:
    try:
        if "GET" in method_name:
            r = session.get(url, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
        else:
            r = session.post(url, data=params, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
        
        print(f"{method_name}")
        print(f"  URL: {url}")
        if params:
            print(f"  Params: {params}")
        print(f"  Status: {r.status_code}")
        
        if 'error' not in r.text.lower() and r.text and not r.text.startswith('<!'):
            print(f"  Content: {r.text[:200]}")
        else:
            print(f"  Error/HTML response")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
