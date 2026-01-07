#!/usr/bin/env python3
"""
Try common database column names for disk_report
Most SQL columns use lowercase with underscores
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

# Try common database column naming patterns
test_pairs = [
    # Common patterns in MunkiReport
    ("disk_report.volume_name", "disk_report.free_bytes"),
    ("disk_report.volume_name", "disk_report.used_bytes"),
    ("disk_report.volume_name", "disk_report.total_bytes"),
    ("disk_report.volume", "disk_report.free"),
    ("disk_report.volume", "disk_report.used"),
    ("disk_report.volume", "disk_report.total"),
    ("disk_report.name", "disk_report.free"),
    ("disk_report.name", "disk_report.size"),
    ("disk_report.path", "disk_report.free"),
    ("disk_report.path", "disk_report.size"),
    # Try without disk_report prefix
    ("volume_name", "free_bytes"),
    ("volume", "free"),
    ("mount", "free"),
]

print("Testing common disk_report column names...\n")

for col1, col2 in test_pairs:
    try:
        query_data = {
            'columns[0][name]': col1,
            'columns[1][name]': col2,
            'draw': 1,
            'length': 1,
            'start': 0,
            'module': 'disk_report'
        }
        
        r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)
        
        if r.status_code == 200:
            data = r.json()
            
            if data.get('data') and len(data['data']) > 0:
                row = data['data'][0]
                print(f"✓ {col1:<35} {col2:<35} = {row}")
            elif 'error' not in data or 'Unknown column' not in data.get('error', ''):
                print(f"~ {col1:<35} {col2:<35} (no error about columns)")
    except Exception as e:
        pass
