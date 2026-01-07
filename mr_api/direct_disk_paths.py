#!/usr/bin/env python3
"""
Try direct paths without /index.php?
"""

import requests
import json
import os

session = requests.Session()

# Get session cookie
cookie_file = os.path.expanduser("~/.mr_session_cookie")
if os.path.exists(cookie_file):
    with open(cookie_file, 'r') as f:
        cookie_str = f.read().strip()
        if cookie_str.startswith("PHPSESSID="):
            phpsessid = cookie_str.split("=", 1)[1]
            session.cookies.set('PHPSESSID', phpsessid)

base = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net"

# Get a machine serial
r = session.post(f"{base}/index.php?/datatables/data", 
                  data={"columns[0][name]": "machine.serial_number", "draw": 1, "length": 1, "start": 0},
                  verify=False)

data = r.json()
serial = data['data'][0][0]
print(f"Machine: {serial}\n")

# Try direct patterns
patterns = [
    f"{base}/report/disk_report/{serial}",
    f"{base}/disk_report",
    f"{base}/api/disk_report/{serial}",
    f"{base}/machine/{serial}",
]

for url in patterns:
    try:
        r = session.post(url, timeout=10, verify=False)
        print(f"POST {url}")
        print(f"  Status: {r.status_code}, Len: {len(r.text)}, Type: {r.headers.get('content-type', 'unknown')[:30]}")
        if 200 <= r.status_code < 300 and r.text and not r.text.startswith('<!'):
            print(f"  Content: {r.text[:150]}")
        print()
    except Exception as e:
        print(f"Error: {e}\n")
