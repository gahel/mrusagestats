#!/usr/bin/env python3
"""
Use the EXACT format from documentation:
/module/{modulename}/report/{serialnumber}
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

# Get machines
r = session.post(
    f"{base}/index.php?/datatables/data",
    data={'columns[0][name]': 'machine.serial_number', 'columns[1][name]': 'machine.hostname', 
          'draw': 1, 'length': 3, 'start': 0},
    timeout=5, verify=False
)

machines = r.json()['data']
print(f"Testing specific endpoint format with {len(machines)} machines\n")

# Try the exact format: /module/{module}/report/{serial}
for serial, hostname in machines:
    print(f"Machine: {hostname} ({serial})")
    
    # Try disk_report module
    url = f"{base}/index.php?/module/disk_report/report/{serial}"
    
    try:
        r = session.get(url, timeout=5, verify=False)
        print(f"  GET /module/disk_report/report/{serial}")
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200 and r.text and not r.text.startswith('<!'):
            print(f"  ✓ Got response!")
            try:
                j = r.json()
                print(f"  JSON type: {type(j)}")
                if isinstance(j, dict):
                    print(f"  Keys: {list(j.keys())}")
                    print(f"  Data: {str(j)[:200]}")
                elif isinstance(j, list):
                    print(f"  List length: {len(j)}")
                    if len(j) > 0:
                        print(f"  First item: {j[0]}")
            except Exception as e:
                print(f"  Response text: {r.text[:200]}")
        else:
            print(f"  Status {r.status_code} or empty response")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
