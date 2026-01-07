#!/usr/bin/env python3
"""
Test script based on MunkiReport API documentation
Systematically test columns to find disk data
"""

import requests
import json
import os

# Configuration
base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
session = requests.Session()

# Get existing session cookie instead of logging in again
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        cookie_str = f.read().strip()
        if cookie_str.startswith("PHPSESSID="):
            phpsessid = cookie_str.split("=", 1)[1]
            session.cookies.set('PHPSESSID', phpsessid)
else:
    print("No session cookie found!")
    exit(1)

auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"

# Test different column combinations
test_sets = [
    {
        'name': 'Basic machine data',
        'columns': [
            "machine.serial_number",
            "machine.hostname",
            "machine.machine_desc",
            "reportdata.timestamp",
            "reportdata.console_user",
        ]
    },
    {
        'name': 'With all existing fields',
        'columns': [
            "machine.serial_number",
            "machine.hostname",
            "machine.machine_desc",
            "machine.cpu",
            "machine.physical_memory",
            "machine.os_version",
            "reportdata.console_user",
            "reportdata.timestamp",
            "usage_stats.thermal_pressure",
            "usage_stats.cpu_idle",
        ]
    },
    {
        'name': 'Trying disk fields - attempt 1',
        'columns': [
            "machine.serial_number",
            "machine.hostname",
            "disk_report.volume_name",
            "disk_report.free_bytes",
        ]
    },
    {
        'name': 'Trying disk fields - attempt 2',
        'columns': [
            "machine.serial_number",
            "machine.hostname",
            "reportdata.storage_free",
            "reportdata.storage_total",
        ]
    },
    {
        'name': 'Trying disk fields - attempt 3',
        'columns': [
            "machine.serial_number",
            "machine.hostname",
            "usage_stats.storage_free",
            "usage_stats.storage_total",
        ]
    },
]

headers = {}
if "CSRF-TOKEN" in session.cookies:
    headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}

for test_set in test_sets:
    print(f"\n{'='*80}")
    print(f"Testing: {test_set['name']}")
    print(f"{'='*80}")
    
    def generate_query():
        q = {f"columns[{i}][name]": c for i, c in enumerate(test_set['columns'])}
        q['draw'] = 1
        q['length'] = 2
        q['start'] = 0
        return q
    
    try:
        query_data = session.post(query_url, data=generate_query(), headers=headers, timeout=5)
        
        print(f"Status: {query_data.status_code}")
        
        if query_data.status_code == 200:
            result = query_data.json()
            
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Records found: {result.get('recordsTotal', 0)}")
                
                if result.get('data') and len(result['data']) > 0:
                    print(f"\nColumns: {test_set['columns']}")
                    print(f"\nFirst row:")
                    for i, col in enumerate(test_set['columns']):
                        val = result['data'][0][i] if i < len(result['data'][0]) else 'N/A'
                        print(f"  {col:<40} = {str(val)[:60]}")
        else:
            print(f"HTTP Error {query_data.status_code}")
    
    except Exception as e:
        print(f"Exception: {e}")

print(f"\n{'='*80}")
print("Test complete")
