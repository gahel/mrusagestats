#!/usr/bin/env python3
"""
Find the API endpoint that returns the dashboard widget data
The "Free Disk Space" widget shows 107 machines with 10GB+
So this data must be accessible somewhere
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

# Try different widget/dashboard endpoints
endpoints = [
    '/index.php?/dashboard/get_widgets',
    '/index.php?/widget/get_data',
    '/index.php?/dashboard/widgets',
    '/index.php?/api/widgets',
    '/api/widgets',
    '/index.php?/module/disk_report/get_data',
    '/index.php?/disk/get_data',
    '/index.php?/storage/get_data',
    '/index.php?/report/disk_usage',
    '/index.php?/report/disk_space',
]

print("Testing dashboard/widget endpoints...\n")

for endpoint in endpoints:
    try:
        url = base + endpoint
        
        # Try both GET and POST
        for method_name, method_func in [("GET", session.get), ("POST", session.post)]:
            try:
                r = method_func(url, timeout=5, verify=False)
                
                if r.status_code == 200 and r.text and not r.text.startswith('<!'):
                    print(f"✓ {method_name} {endpoint}")
                    print(f"  Status: {r.status_code}")
                    
                    # Try to parse as JSON
                    try:
                        data = r.json()
                        if isinstance(data, dict):
                            print(f"  Keys: {list(data.keys())[:5]}")
                            if 'disk' in str(data).lower() or 'free' in str(data).lower():
                                print(f"  ✓✓ Contains disk/free data!")
                        elif isinstance(data, list):
                            print(f"  Type: List with {len(data)} items")
                        print(f"  Sample: {str(data)[:150]}\n")
                    except:
                        print(f"  Response: {r.text[:150]}\n")
            except:
                pass
    except:
        pass

print("\n" + "="*80)
print("Also trying direct module queries with search terms...")
print("="*80 + "\n")

# Try searching for disk-related data in different ways
search_endpoints = [
    '/index.php?/machines',
    '/index.php?/reports',
    '/index.php?/admin',
]

for endpoint in search_endpoints:
    try:
        r = session.get(base + endpoint, timeout=5, verify=False)
        if 'disk' in r.text.lower() or 'storage' in r.text.lower():
            print(f"✓ Found disk/storage reference in {endpoint}")
    except:
        pass
