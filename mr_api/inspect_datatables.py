#!/usr/bin/env python3
"""
Check what /datatables/data actually contains - get ALL columns
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

# Try requesting with NO specific columns - maybe it returns everything?
print("Test 1: Request with no columns specified\n")
r = session.post(
    base + '/datatables/data',
    data={
        'draw': 1,
        'length': 1,
        'start': 0,
    },
    timeout=5, verify=False
)

print(f"Status: {r.status_code}")
data = r.json()
print(f"Keys: {list(data.keys())}")
if data.get('data') and len(data['data']) > 0:
    print(f"First row length: {len(data['data'][0])}")
    print(f"First row: {data['data'][0]}")
print()

# Now request with just one column to see structure
print("Test 2: Request with one column\n")
r = session.post(
    base + '/datatables/data',
    data={
        'columns[0][name]': 'machine.serial_number',
        'draw': 1,
        'length': 1,
        'start': 0,
    },
    timeout=5, verify=False
)

print(f"Status: {r.status_code}")
data = r.json()
if 'error' in data:
    print(f"Error: {data['error']}")
elif data.get('data'):
    print(f"Got {len(data['data'])} rows")
    print(f"First row: {data['data'][0]}")
print()

# Try with many columns - see what comes back
print("Test 3: Request with many columns\n")

columns = [
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

query_data = {f"columns[{i}][name]": col for i, col in enumerate(columns)}
query_data.update({'draw': 1, 'length': 1, 'start': 0})

r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)

print(f"Status: {r.status_code}")
data = r.json()
if 'error' in data:
    print(f"Error: {data['error']}")
elif data.get('data'):
    print(f"Got {len(data['data'])} rows with {len(data['data'][0])} columns")
    print("\nColumn mapping:")
    for i, col in enumerate(columns):
        val = data['data'][0][i] if i < len(data['data'][0]) else 'N/A'
        print(f"  [{i}] {col:<40} = {str(val)[:80]}")
