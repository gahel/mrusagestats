#!/usr/bin/env python3
"""
Get complete raw response and inspect all fields
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

url = urljoin(CONFIG['base_url'], '/datatables/data')

# Get with many possible disk/storage fields
COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
    # Try every possible disk field we haven't tested
    "disk.free",
    "disk.total",
    "disk.size",
    "storage_free",
    "freespace",
    "disk_space_free",
    "disk_space_total",
]

query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
query_data.update({
    "draw": 1,
    "length": 1,
    "start": 0,
})

r = session.post(url, data=query_data, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])

print(f"Status: {r.status_code}\n")
print(f"Response text:\n{r.text}\n")

if r.status_code == 200:
    try:
        data = r.json()
        print(f"JSON keys: {list(data.keys())}")
        if data.get('error'):
            print(f"Error in response: {data['error']}")
        if data.get('data'):
            print(f"Data rows: {len(data['data'])}")
            print(f"First row columns: {len(data['data'][0])}")
            print("\nFirst row values:")
            for i, val in enumerate(data['data'][0]):
                col = COLUMNS[i] if i < len(COLUMNS) else f"unknown[{i}]"
                print(f"  [{i}] {col:<30} = {str(val)[:60]}")
    except Exception as e:
        print(f"JSON parse error: {e}")
