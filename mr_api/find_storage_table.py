#!/usr/bin/env python3
"""
Try querying storage as a separate table via datatables/data
by specifying a table parameter or module
"""

import requests
import json
import subprocess
from urllib.parse import urljoin, quote
import urllib.parse as urlparse

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Authenticate and get session
auth_url = f"{base_url}/auth/login"
session = requests.Session()
session.verify = False
auth_request = session.post(auth_url, data={"login": login, "password": password})

if auth_request.status_code != 200:
    print("Authentication failed!")
    raise SystemExit

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}

print("Testing storage data access:\n")

# Try different approaches
tests = [
    {
        "name": "Storage as separate module",
        "url": "/datatables/data",
        "query_string": "module=storage",
        "data": {
            "columns[0][name]": "storage.hostname",
            "columns[1][name]": "storage.free",
            "draw": 1,
            "length": 1,
            "start": 0,
        }
    },
    {
        "name": "Direct storage endpoint",
        "url": "/datatables/storage",
        "query_string": "",
        "data": {
            "columns[0][name]": "hostname",
            "columns[1][name]": "free",
            "draw": 1,
            "length": 1,
            "start": 0,
        }
    },
    {
        "name": "Storage with module param",
        "url": "/datatables/data",
        "query_string": "t=storage",
        "data": {
            "columns[0][name]": "free",
            "columns[1][name]": "size",
            "draw": 1,
            "length": 1,
            "start": 0,
        }
    },
]

for test in tests:
    url = base_url.rstrip('?') + '/index.php?' + test['query_string'] + test['url']
    
    try:
        r = session.post(url, data=test['data'], headers=headers)
        
        result = "✓" if r.status_code == 200 else f"✗ {r.status_code}"
        has_data = False
        
        if r.status_code == 200:
            try:
                data = r.json()
                has_data = bool(data.get('data') and len(data['data']) > 0)
                result += f" - {'✓ Got data' if has_data else '✗ No data'}"
            except:
                result += " - Invalid JSON"
        
        print(f"{result:<30} {test['name']}")
        
    except Exception as e:
        print(f"✗ Error                        {test['name']}")
