#!/usr/bin/env python3
"""
Try /report/disk_report with serial as part of URL path
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

# Get a machine serial first
machines_url = urljoin(CONFIG['base_url'], '/datatables/data')
query_data = {
    "columns[0][name]": "machine.serial_number",
    "draw": 1,
    "length": 1,
    "start": 0,
}

try:
    r = session.post(machines_url, data=query_data, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
    data = r.json()
    if data.get('data'):
        serial = data['data'][0][0]
        print(f"Using machine serial: {serial}\n")
        
        # Try different URL patterns
        patterns = [
            f'/report/disk_report/{serial}',
            f'/report/disk_report?serial={serial}',
            f'/disk_report/{serial}',
            f'/machine/{serial}/disk_report',
        ]
        
        for pattern in patterns:
            url = CONFIG['base_url'].rstrip('?') + '/index.php?' + pattern
            try:
                r = session.post(url, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
                
                print(f"Pattern: {pattern}")
                print(f"  Status: {r.status_code}")
                
                if r.status_code == 200:
                    try:
                        # Try to parse as JSON
                        j = r.json()
                        print(f"  JSON: {list(j.keys())}")
                        if j.get('data'):
                            print(f"  Data: {j['data'][:2] if isinstance(j['data'], list) else str(j['data'])[:100]}")
                    except:
                        # Try to parse as PHP serialized
                        if r.text.startswith('a:'):
                            print(f"  PHP serialized: {r.text[:100]}")
                        else:
                            print(f"  Response: {r.text[:100]}")
                else:
                    print(f"  Error response")
                print()
            except Exception as e:
                print(f"  Error: {e}\n")
except Exception as e:
    print(f"Error: {e}")
