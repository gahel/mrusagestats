#!/usr/bin/env python3
"""
Query disk_report and parse PHP serialized response
"""

import requests
import os
import re
from urllib.parse import urljoin

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

# Get machines list for testing
base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'
r = session.post(
    urljoin(base, '/datatables/data'),
    data={'columns[0][name]': 'machine.serial_number', 'columns[1][name]': 'machine.hostname', 
          'draw': 1, 'length': 2, 'start': 0},
    timeout=5, verify=False
)

machines = r.json()['data']
print(f"Found {len(machines)} machines\n")

# Try to get disk data for first 2 machines by querying the report endpoint directly
# Maybe it returns data in a different format than we expect
base_url = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net'

for serial, hostname in machines[:2]:
    print(f"Machine: {hostname} ({serial})")
    
    # Try GET on report endpoint
    url = f"{base_url}/report/disk_report/{serial}"
    r = session.get(url, timeout=5, verify=False)
    
    print(f"  GET {url}")
    print(f"    Status: {r.status_code}, Type: {r.headers.get('content-type')[:30]}")
    print(f"    Data: {r.text[:200]}")
    print()
