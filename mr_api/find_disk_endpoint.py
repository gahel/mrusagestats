#!/usr/bin/env python3
"""
Try querying disk_report via individual machine serial number
or check if it's accessible via a different endpoint pattern
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
        
        # Now try different endpoint patterns for disk_report
        tests = [
            f'/disk_report/get_data/{serial}',
            f'/disk/get_data/{serial}',
            f'/report/disk_report',
            f'/datatables/disk_report',
            f'/datatables/{serial}/disk_report',
        ]
        
        print("Testing disk_report endpoint patterns:\n")
        
        for endpoint in tests:
            url = urljoin(CONFIG['base_url'], endpoint)
            try:
                r = session.post(url, data={}, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
                
                result = f"Status {r.status_code}"
                if r.status_code == 200:
                    try:
                        j = r.json()
                        result += f" ✓ JSON - Keys: {list(j.keys())[:3]}"
                    except:
                        result += f" - Type: {r.headers.get('content-type', 'unknown')}"
                
                print(f"{result:<50} {endpoint}")
            except Exception as e:
                print(f"Error: {str(e)[:40]:<40} {endpoint}")
except Exception as e:
    print(f"Error getting machine serial: {e}")
