#!/usr/bin/env python3
"""
Check what /report/disk_report returns
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

url = urljoin(CONFIG['base_url'], '/report/disk_report')

# Try with different parameters
tests = [
    {},
    {"draw": 1, "length": 5, "start": 0},
    {"serial": "C3W0FX49WN"},
    {"columns[0][name]": "mount", "columns[1][name]": "free"},
]

print("Testing /report/disk_report endpoint:\n")

for i, params in enumerate(tests):
    try:
        r = session.post(url, data=params, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
        
        print(f"Request {i+1} with params: {params}")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('content-type')}")
        print(f"  Response length: {len(r.text)}")
        print(f"  First 200 chars: {r.text[:200]}")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
