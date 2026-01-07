#!/usr/bin/env python3
"""
Check if there's a datatable endpoint for disk_report
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

# Try disk_report as a datatable source  
query_data = {
    'columns[0][name]': 'disk.volume',
    'columns[1][name]': 'disk.free',
    'columns[2][name]': 'disk.total',
    'draw': 1,
    'length': 107,
    'start': 0,
}

url = f'{base}/index.php?/datatables/data'

print("Testing datatables with disk columns...\n")
r = session.post(url, data=query_data, timeout=5, verify=False)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"Response (first 500 chars):\n{r.text[:500]}\n")

if r.status_code == 200:
    try:
        data = r.json()
        print(f"JSON Keys: {list(data.keys())}")
        if 'recordsTotal' in data:
            print(f"Records Total: {data['recordsTotal']}")
        if 'data' in data:
            print(f"Data records: {len(data['data'])}")
            if data['data']:
                print(f"First record: {data['data'][0]}")
    except:
        pass
