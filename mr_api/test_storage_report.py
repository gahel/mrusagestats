#!/usr/bin/env python3
"""
Fetch disk data using report/storage endpoint for each machine
"""

import requests
import json
import subprocess
import os
from urllib.parse import urljoin
from datetime import datetime

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

# First, get list of machines from machines.json
machines_file = 'machines.json'
if os.path.exists(machines_file):
    with open(machines_file, 'r') as f:
        machines = json.load(f)
    
    print(f"Testing /report/storage endpoint with {len(machines)} machines...\n")
    
    success_count = 0
    for i, machine in enumerate(machines[:5]):  # Test first 5
        serial = machine.get('serial_number')
        hostname = machine.get('hostname')
        
        url = urljoin(base_url, f'report/storage')
        
        try:
            r = session.post(url, data={'serial': serial}, headers=headers)
            print(f"\n[{i+1}] {hostname} ({serial})")
            print(f"    Status: {r.status_code}")
            
            # Try to decode PHP serialized data or JSON
            if r.text.startswith('a:'):
                # PHP serialized - try simple parsing
                print(f"    Response type: PHP serialized")
                print(f"    Response: {r.text[:200]}")
            else:
                try:
                    data = r.json()
                    print(f"    Response type: JSON")
                    print(f"    Keys: {list(data.keys())}")
                except:
                    print(f"    Response: {r.text[:200]}")
            
            if r.status_code == 200:
                success_count += 1
        except Exception as e:
            print(f"    Error: {e}")
    
    print(f"\n✓ Successful responses: {success_count}/5")
else:
    print("machines.json not found")
