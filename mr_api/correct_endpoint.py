#!/usr/bin/env python3
"""
Use the correct specific endpoint format from documentation:
/module/{module_name}/report/{serialnumber}
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
print(f"Testing with {len(machines)} machines\n")

# Try the correct specific endpoint format
for serial, hostname in machines:
    # Test different module names for disk data
    for module in ['disk_report', 'storage', 'disk']:
        url = f"{base}/index.php?/module/{module}/report/{serial}"
        
        try:
            r = session.get(url, timeout=5, verify=False)
            
            if r.status_code == 200 and r.text and not r.text.startswith('<!'):
                print(f"✓ {hostname} ({serial})")
                print(f"  Module: {module}")
                print(f"  URL: {url.split('app-munkireport')[1]}")
                
                # Try to parse response
                try:
                    j = r.json()
                    print(f"  JSON: {list(j.keys()) if isinstance(j, dict) else type(j)}")
                    if j and (j.get('data') or j.get('mount_point') or j.get('free')):
                        print(f"  ✓✓ HAS DATA!")
                        print(f"    {str(j)[:200]}")
                except:
                    print(f"  Response: {r.text[:150]}")
                print()
        except Exception as e:
            pass
