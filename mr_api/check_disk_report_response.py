#!/usr/bin/env python3
"""
Check detailed response for the columns that didn't throw "Unknown column" error
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

base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'

query_data = {
    'columns[0][name]': 'disk_report.volume_name',
    'columns[1][name]': 'disk_report.free_bytes',
    'draw': 1,
    'length': 10,
    'start': 0,
    'module': 'disk_report'
}

r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)

print(f"Status: {r.status_code}\n")

if r.status_code == 200:
    data = r.json()
    print(f"Response keys: {list(data.keys())}")
    print(f"recordsTotal: {data.get('recordsTotal')}")
    print(f"recordsFiltered: {data.get('recordsFiltered')}")
    print(f"Data length: {len(data.get('data', []))}")
    
    if data.get('error'):
        print(f"Error: {data['error']}")
    
    if data.get('data'):
        print(f"\nFirst 3 rows:")
        for i, row in enumerate(data['data'][:3]):
            print(f"  {i}: {row}")
    
    if data.get('sql'):
        print(f"\nSQL: {data['sql']}")
