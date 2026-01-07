#!/usr/bin/env python3
"""
Try /report/disk_space and /report/disk_usage with serial numbers
"""

import requests
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

# Try the endpoints with different parameter formats
tests = [
    ('GET with path', f"{base}/index.php?/report/disk_space/{serial}", 'get', {}),
    ('POST with path', f"{base}/index.php?/report/disk_space/{serial}", 'post', {}),
    ('GET with query param', f"{base}/index.php?/report/disk_space?serial={serial}", 'get', {}),
    ('POST with data param', f"{base}/index.php?/report/disk_space", 'post', {'serial': serial}),
    ('POST with serial_number param', f"{base}/index.php?/report/disk_space", 'post', {'serial_number': serial}),
    ('GET disk_usage', f"{base}/index.php?/report/disk_usage/{serial}", 'get', {}),
    ('POST disk_usage', f"{base}/index.php?/report/disk_usage/{serial}", 'post', {}),
]

for name, url, method, data in tests:
    try:
        if method == 'get':
            r = session.get(url, timeout=5, verify=False)
        else:
            r = session.post(url, data=data, timeout=5, verify=False)
        
        print(f"{name}")
        print(f"  URL: {url.split('index.php?')[1] if 'index.php?' in url else url.split('.net')[1]}")
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200 and r.text and not r.text.startswith('<!'):
            # Try JSON
            try:
                j = r.json()
                print(f"  JSON: {type(j)}")
                if j and (j.get('data') or j.get('free') or j.get('total')):
                    print(f"  ✓ HAS DISK DATA: {str(j)[:200]}")
                else:
                    print(f"  Keys: {list(j.keys()) if isinstance(j, dict) else 'N/A'}")
            except:
                # Try PHP serialized
                if r.text.startswith('a:'):
                    print(f"  PHP: {r.text[:100]}")
                else:
                    print(f"  Response: {r.text[:100]}")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
