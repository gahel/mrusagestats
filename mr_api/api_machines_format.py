#!/usr/bin/env python3
"""
Try formats like /api/machines/{serial} for getting machine+module data
"""

import requests
import json
import os

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net'

# Get a machine serial
r = session.post(
    f"{base}/index.php?/datatables/data",
    data={'columns[0][name]': 'machine.serial_number', 'columns[1][name]': 'machine.hostname', 
          'draw': 1, 'length': 1, 'start': 0},
    timeout=5, verify=False
)

serial, hostname = r.json()['data'][0][:2]
print(f"Machine: {hostname} ({serial})\n")

# Try /api/machines/{serial}/module or /machines/{serial}/module formats
patterns = [
    f"/api/machines/{serial}/disk_report",
    f"/machines/{serial}/disk_report",
    f"/machines/{serial}",
    f"/api/machines/{serial}",
    f"/api/machines",
    f"/machines",
]

for pattern in patterns:
    url = base + pattern
    try:
        r = session.get(url, timeout=5, verify=False)
        print(f"GET {pattern}")
        print(f"  Status: {r.status_code}")
        
        if 200 <= r.status_code < 300 and r.text and not r.text.startswith('<!'):
            try:
                j = r.json()
                if isinstance(j, dict):
                    keys = list(j.keys())[:5]
                    print(f"  ✓ JSON: keys={keys}")
                    if j.get('disk_report'):
                        print(f"    Has disk_report!")
                elif isinstance(j, list):
                    print(f"  ✓ List with {len(j)} items")
                    if len(j) > 0:
                        print(f"    First: {str(j[0])[:100]}")
            except:
                print(f"  Response: {r.text[:80]}")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
