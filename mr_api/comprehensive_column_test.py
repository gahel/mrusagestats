#!/usr/bin/env python3
"""
Systematically test EVERY reasonable disk column name one by one
If it works, print it. If it doesn't, just move on.
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

# Every conceivable disk/storage column name
test_columns = [
    # Direct attempts
    "storage.free", "storage.size", "storage.used", "storage.total",
    "disk.free", "disk.size", "disk.used", "disk.total",
    "disk_report.free", "disk_report.size", "disk_report.total",
    "hdd.free", "hdd.size", "hdd.total",
    
    # reportdata namespace
    "reportdata.storage_free", "reportdata.storage_total",
    "reportdata.hdd_free", "reportdata.hdd_total",
    "reportdata.disk_free", "reportdata.disk_total",
    
    # machine namespace 
    "machine.storage_free", "machine.storage_total",
    "machine.disk_free", "machine.disk_total",
    
    # usage_stats namespace
    "usage_stats.storage_free", "usage_stats.storage_total",
    "usage_stats.disk_free", "usage_stats.disk_total",
    
    # Simple names
    "free", "size", "total", "used",
    "freespace", "diskspace", "volume",
    
    # mount/partition names
    "mount.free", "mount.total", "mount.size",
    "partition.free", "partition.total",
]

print("Testing all possible disk column names...\n")
found = []

for col_name in test_columns:
    try:
        query_data = {
            'columns[0][name]': 'machine.serial_number',
            'columns[1][name]': col_name,
            'draw': 1,
            'length': 1,
            'start': 0
        }
        
        r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)
        
        if r.status_code == 200:
            data = r.json()
            
            # Check if we got actual data (not an error)
            if data.get('data') and len(data['data']) > 0 and len(data['data'][0]) > 1:
                value = data['data'][0][1]
                print(f"✓ {col_name:<40} = {value}")
                found.append((col_name, value))
    except:
        pass

if found:
    print(f"\n✓✓✓ Found {len(found)} disk columns!")
else:
    print(f"\n✗ No disk columns found in /datatables/data")
