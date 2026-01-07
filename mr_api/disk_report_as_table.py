#!/usr/bin/env python3
"""
Try querying disk_report as if it's a separate table/module in datatables
Maybe there's a way to specify which table to query
"""

import requests
import os

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'

# Try different ways to specify module/table
print("Trying to access disk_report as separate data source...\n")

tests = [
    # Add module parameter
    {
        'name': 'With module=disk_report',
        'url': base + '/datatables/data?module=disk_report',
        'data': {'columns[0][name]': 'mount_point', 'columns[1][name]': 'free', 'draw': 1, 'length': 1, 'start': 0}
    },
    # Try postdata with module
    {
        'name': 'POST with module=disk_report in data',
        'url': base + '/datatables/data',
        'data': {'module': 'disk_report', 'columns[0][name]': 'mount_point', 'columns[1][name]': 'free', 'draw': 1, 'length': 1, 'start': 0}
    },
    # Try with table parameter
    {
        'name': 'With table=disk_report',
        'url': base + '/datatables/data?table=disk_report',
        'data': {'columns[0][name]': 'mount_point', 'columns[1][name]': 'free', 'draw': 1, 'length': 1, 'start': 0}
    },
    # Try direct field names without module prefix
    {
        'name': 'Bare column names (disk_report)',
        'url': base + '/datatables/data',
        'data': {'columns[0][name]': 'mount_point', 'columns[1][name]': 'free', 'draw': 1, 'length': 1, 'start': 0}
    },
]

for test in tests:
    try:
        r = session.post(test['url'], data=test['data'], timeout=5, verify=False)
        
        print(f"Test: {test['name']}")
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            
            if data.get('data') and len(data['data']) > 0:
                print(f"  ✓ GOT DATA: {data['data'][0]}")
            elif 'error' in data:
                print(f"  Error: {data['error'][:80]}")
            else:
                print(f"  Response keys: {list(data.keys())}")
        print()
    except Exception as e:
        print(f"  Exception: {e}\n")
