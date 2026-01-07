#!/usr/bin/env python3
"""
Test the disk_report module endpoints that were found in the HTML
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

# Try the disk_report module endpoints
endpoints = [
    '/module/disk_report/get_stats',
    '/module/disk_report/get_volume_type',
    '/module/disk_report/get_disk_type',
    '/module/disk_report/get_smart_stats',
]

print("Testing disk_report module endpoints...\n")

for endpoint in endpoints:
    url = base + endpoint
    
    for method_name, method_func in [("GET", session.get), ("POST", session.post)]:
        try:
            r = method_func(url, timeout=5, verify=False)
            
            if r.status_code == 200 and r.text and not r.text.startswith('<!'):
                print(f"✓ {method_name} {endpoint}")
                print(f"  Status: {r.status_code}")
                
                # Try JSON
                try:
                    data = r.json()
                    print(f"  ✓✓ JSON Response!")
                    print(f"  Type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"  Keys: {list(data.keys())}")
                        print(f"  Data: {str(data)[:300]}")
                    elif isinstance(data, list):
                        print(f"  List: {len(data)} items")
                        if len(data) > 0:
                            print(f"  First item: {data[0]}")
                except Exception as e:
                    print(f"  Response: {r.text[:200]}")
                print()
        except:
            pass
