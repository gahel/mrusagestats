#!/usr/bin/env python3
"""
Test the correct endpoint format:
/show/report/disk_report/storage
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

# Try the exact URL pattern you provided
urls = [
    '/show/report/disk_report/storage',
    '/show/report/disk_report/data',
    '/show/report/storage',
    '/api/show/report/disk_report/storage',
]

print("Testing /show/report endpoints...\n")

for endpoint in urls:
    url = base + endpoint
    
    try:
        r = session.get(url, timeout=5, verify=False)
        
        print(f"GET {endpoint}")
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            # Try JSON first
            try:
                data = r.json()
                print(f"  ✓ JSON Response!")
                print(f"  Type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:10]}")
                    print(f"  Sample: {str(data)[:300]}")
                elif isinstance(data, list):
                    print(f"  List length: {len(data)}")
                    if len(data) > 0:
                        print(f"  First item: {data[0]}")
            except Exception as e:
                # Try HTML/text
                if 'storage' in r.text.lower() or 'disk' in r.text.lower():
                    print(f"  HTML/Text with storage/disk data")
                    print(f"  First 300 chars: {r.text[:300]}")
                else:
                    print(f"  Response type: {r.headers.get('content-type')}")
                    print(f"  First 100 chars: {r.text[:100]}")
        else:
            print(f"  Error response")
        
        print()
    except Exception as e:
        print(f"  Exception: {e}\n")
