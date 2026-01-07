#!/usr/bin/env python3
"""
Deep dive into inventory and related modules
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

# Try inventory module with ALL field names that might exist
possible_fields = [
    'id', 'serial_number', 'hostname', 'free', 'used', 'total', 'size', 'space',
    'volume', 'mount', 'path', 'name', 'filesystem', 'device', 'capacity',
    'available', 'utilization', 'percent', 'percentage', 'hdd_free', 'hdd_total',
    'memory_free', 'memory_total', 'disk_free', 'disk_total',
]

print("Testing inventory module columns:\n")

for field in possible_fields:
    try:
        query_data = {
            'columns[0][name]': 'machine.serial_number',
            'columns[1][name]': f'inventory.{field}',
            'draw': 1,
            'length': 1,
            'start': 0,
        }
        
        r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)
        data = r.json()
        
        if data.get('data') and len(data['data']) > 0:
            val = data['data'][0][1]
            print(f"✓ inventory.{field:<25} = {val}")
        elif 'error' not in data or ('Table' not in data.get('error','') and 'Unknown column' not in data.get('error','')):
            pass  # Skip errors, just show working ones
    except:
        pass

print("\n\nTesting smart_stats module columns:\n")

for field in possible_fields:
    try:
        query_data = {
            'columns[0][name]': 'machine.serial_number',
            'columns[1][name]': f'smart_stats.{field}',
            'draw': 1,
            'length': 1,
            'start': 0,
        }
        
        r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)
        data = r.json()
        
        if data.get('data') and len(data['data']) > 0:
            val = data['data'][0][1]
            print(f"✓ smart_stats.{field:<25} = {val}")
    except:
        pass
