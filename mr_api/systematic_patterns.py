#!/usr/bin/env python3
"""
Systematically try all reasonable API patterns for disk_report
"""

import requests
import os
from urllib.parse import urljoin

session = requests.Session()

# Get session cookie
cookie_file = os.path.expanduser("~/.mr_session_cookie")
if os.path.exists(cookie_file):
    with open(cookie_file, 'r') as f:
        cookie_str = f.read().strip()
        if cookie_str.startswith("PHPSESSID="):
            phpsessid = cookie_str.split("=", 1)[1]
            session.cookies.set('PHPSESSID', phpsessid)

base = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"

# Get a serial for testing
r = session.post(urljoin(base, '/datatables/data'), 
                  data={"columns[0][name]": "machine.serial_number", "draw": 1, "length": 1, "start": 0},
                  verify=False)
serial = r.json()['data'][0][0]

print(f"Testing with serial: {serial}\n")

# Try different endpoint patterns
patterns = [
    ("/datatables/disk_report/data", {"columns[0][name]": "disk_report.mount_point", "columns[1][name]": "disk_report.free"}),
    ("/disk_report/datatables/data", {"columns[0][name]": "mount_point", "columns[1][name]": "free"}),
    ("/datatables/data?module=disk_report", {"columns[0][name]": "mount_point", "columns[1][name]": "free"}),
    ("/datatables/storage/data", {"columns[0][name]": "mount", "columns[1][name]": "free"}),
    ("/storage/datatables/data", {"columns[0][name]": "mount", "columns[1][name]": "free"}),
    ("/report/disk_report", {"draw": 1, "length": 10, "start": 0}),
]

for endpoint, data in patterns:
    try:
        url = urljoin(base, endpoint)
        r = session.post(url, data=data, timeout=5, verify=False)
        
        print(f"Endpoint: {endpoint}")
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            try:
                j = r.json()
                if j.get('data') and len(j.get('data', [])) > 0:
                    print(f"  ✓ GOT DATA! {len(j['data'])} rows")
                    print(f"    First row: {j['data'][0]}")
                else:
                    print(f"  JSON but no data: {list(j.keys())}")
            except:
                if r.text[:100] != '<!doc':
                    print(f"  Response: {r.text[:100]}")
                else:
                    print(f"  HTML response")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
