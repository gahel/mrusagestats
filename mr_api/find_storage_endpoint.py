#!/usr/bin/env python3
"""
Try to find the storage data endpoint
Test different table/module names
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

# Base query structure but try querying storage fields directly
query_url = f"{base_url}/datatables/data"

test_columns = [
    ["storage.free", "storage.size"],
    ["storage.name", "storage.free"],
    ["machine_serial", "hdd_free", "hdd_total"],
    ["hostname", "free_space"],
]

print("Testing different column combinations:\n")

for cols in test_columns:
    query_data = {f"columns[{i}][name]": col for i, col in enumerate(cols)}
    query_data.update({
        "draw": 1,
        "length": 1,
        "start": 0,
    })
    
    try:
        r = session.post(query_url, data=query_data, headers=headers)
        
        if r.status_code == 200:
            try:
                data = r.json()
                status = "✓ Data" if data.get('data') and len(data['data']) > 0 else "✗ No data"
                print(f"{status:<15} {str(cols)}")
            except:
                print(f"✗ Invalid JSON   {str(cols)}")
        else:
            print(f"✗ Status {r.status_code:<2} {str(cols)}")
    except Exception as e:
        print(f"✗ Error          {str(cols)}")
