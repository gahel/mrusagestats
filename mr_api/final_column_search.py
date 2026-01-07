#!/usr/bin/env python3
"""
Final attempt - try querying machines with any storage/disk column names
that might actually exist in the database schema
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

# List of potential column names - trying EVERY variation
potential_columns = [
    "storage.free",
    "storage.size", 
    "storage.total",
    "disk.free",
    "disk.size",
    "disk.total",
    "disk_report.free",
    "disk_report.size",
    "disk_report.total",
    "disk_report.hdd_free",
    "disk_report.hdd_total",
    "filesystem.free",
    "filesystem.size",
    "volume.free",
    "volume.size",
    "mount.free",
    "mount.size",
    "partition.free",
    "partition.size",
    "drive.free",
    "drive.size",
]

print("Testing potential disk/storage column names...\n")

found_columns = []

for col in potential_columns:
    try:
        r = session.post(
            base + '/datatables/data',
            data={
                'columns[0][name]': 'machine.serial_number',
                'columns[1][name]': col,
                'draw': 1,
                'length': 1,
                'start': 0
            },
            timeout=5,
            verify=False
        )
        
        if r.status_code == 200:
            j = r.json()
            if j.get('data') and len(j['data']) > 0:
                val = j['data'][0][1]
                print(f"✓✓✓ {col:<25} = {val}")
                found_columns.append((col, val))
            elif 'error' not in j or 'Base table' not in j.get('error',''):
                pass  # SQL error about table, skip
    except:
        pass

if found_columns:
    print(f"\n✓ Found {len(found_columns)} working columns!")
else:
    print("\n✗ No storage columns found via /datatables/data")
