#!/usr/bin/env python3
"""
Try to access disk data directly from storage endpoint
"""

import requests
import json
import subprocess
from urllib.parse import urljoin

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

# Try different endpoints that might have storage/disk data
endpoints = [
    ('dt_storage', {}),  # Storage table endpoint
    ('report/storage', {}),  # Report endpoint for storage
    ('dt_machines', {"columns": [{"name": "machine.serial_number"}, {"name": "machine.hostname"}]}),  # Known working endpoint
]

for endpoint, payload in endpoints:
    url = urljoin(base_url, endpoint)
    
    if not payload:
        payload = {
            "draw": 1,
            "length": 1,
            "start": 0,
        }
    
    try:
        print(f"\n📍 Endpoint: {endpoint}")
        r = session.post(url, data=payload, headers=headers)
        print(f"  Status: {r.status_code}")
        
        # Try to parse as JSON
        try:
            data = r.json()
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}")
                print(f"  Records: {data.get('recordsTotal', data.get('total', 'N/A'))}")
                if data.get('data'):
                    print(f"  Sample: {str(data['data'][0])[:100]}")
            else:
                print(f"  Type: {type(data)}, Length: {len(data)}")
        except:
            # Try to decode as text
            print(f"  Response (first 200 chars): {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
