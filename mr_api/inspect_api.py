#!/usr/bin/env python3
"""
Inspect the raw API response to see all available fields
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

# Test with working columns
url = urljoin(CONFIG['base_url'], '/datatables/data')

COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.console_user",
    "reportdata.timestamp",
    "usage_stats.thermal_pressure",
    "usage_stats.cpu_idle",
]

# Format as the API expects
query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
query_data.update({
    "draw": 1,
    "length": 1,
    "start": 0,
})

print("Testing API call with working columns...\n")
r = session.post(url, data=query_data, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
print(f"Status: {r.status_code}")

if r.status_code == 200:
    try:
        data = r.json()
        print(f"✓ Valid JSON response")
        print(f"Keys: {list(data.keys())}")
        if data.get('data'):
            print(f"Data rows: {len(data['data'])}")
            print(f"\nFirst row ({len(data['data'][0])} fields):")
            for i, val in enumerate(data['data'][0]):
                print(f"  [{i}] {COLUMNS[i] if i < len(COLUMNS) else '?'}: {str(val)[:50]}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response: {r.text[:500]}")
else:
    print(f"Error response:\n{r.text[:500]}")
