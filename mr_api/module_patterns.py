#!/usr/bin/env python3
"""
Try /module/disk_report/data or /module/disk_report variations
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

# Get a machine
r = session.post(
    f"{base}/index.php?/datatables/data",
    data={'columns[0][name]': 'machine.serial_number', 'columns[1][name]': 'machine.hostname', 
          'draw': 1, 'length': 1, 'start': 0},
    timeout=5, verify=False
)

serial, hostname = r.json()['data'][0][:2]
print(f"Machine: {hostname} ({serial})\n")

# Try different endpoint patterns
patterns = [
    f"/index.php?/module/disk_report/data",
    f"/index.php?/module/disk_report/{serial}",
    f"/index.php?/disk_report/data",
    f"/index.php?/disk_report/{serial}",
    f"/module/disk_report/{serial}",
    f"/api/module/disk_report/{serial}",
]

for pattern in patterns:
    url = base + pattern
    
    try:
        # Try both GET and POST
        for method_name, method in [("GET", "get"), ("POST", "post")]:
            if method == "get":
                r = session.get(url, timeout=5, verify=False)
            else:
                r = session.post(url, data={}, timeout=5, verify=False)
            
            if r.status_code == 200 and r.text and not r.text.startswith('<!') and not r.text.startswith('a:1:{s:5:"error"'):
                print(f"✓✓✓ {method} {pattern}")
                print(f"  Response: {r.text[:200]}")
                print()
    except:
        pass
