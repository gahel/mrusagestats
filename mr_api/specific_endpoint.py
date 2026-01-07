#!/usr/bin/env python3
"""
Use the "Specific" endpoint format from MunkiReport API docs
/api/module_name to query disk_report data
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

# Get a machine serial first
r = session.post(
    f"{base}/index.php?/datatables/data",
    data={'columns[0][name]': 'machine.serial_number', 'columns[1][name]': 'machine.hostname', 
          'draw': 1, 'length': 1, 'start': 0},
    timeout=5, verify=False
)

machines = r.json()['data']
serial, hostname = machines[0][:2]
print(f"Machine: {hostname} ({serial})\n")

# Try the specific endpoint format
test_urls = [
    f"{base}/api/disk_report/{serial}",
    f"{base}/api/disk_report",
    f"{base}/api/v1/disk_report/{serial}",
    f"{base}/api/v1/disk_report",
    f"{base}/index.php?/api/disk_report/{serial}",
    f"{base}/index.php?/api/disk_report",
    f"{base}/index.php?/disk_report/get_data",
]

for url in test_urls:
    try:
        r = session.get(url, timeout=5, verify=False)
        print(f"GET {url.split('app-munkireport')[1]}")
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200 and r.text and not r.text.startswith('<!'):
            try:
                j = r.json()
                if j.get('data'):
                    print(f"  ✓ GOT DATA: {type(j['data'])}, length: {len(j['data']) if isinstance(j['data'], list) else 'N/A'}")
                    if isinstance(j['data'], list) and len(j['data']) > 0:
                        print(f"    First item: {j['data'][0]}")
                else:
                    print(f"  Keys: {list(j.keys())}")
            except:
                print(f"  Response: {r.text[:100]}")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
