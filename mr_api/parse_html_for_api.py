#!/usr/bin/env python3
"""
Get the HTML page and search for API calls that fetch disk data
"""

import requests
import re
import os

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net'

url = base + '/show/report/disk_report/storage'

r = session.get(url, timeout=5, verify=False)

print("Searching for API calls in page...\n")

# Search for fetch, $.ajax, XMLHttpRequest, etc.
patterns = [
    r'fetch\(["\']([^"\']+)["\']',
    r'\.get\(["\']([^"\']+)["\']',
    r'\.post\(["\']([^"\']+)["\']',
    r'\.ajax\({[^}]*url:["\']([^"\']+)["\']',
    r'xhr\.open\([^,]+,["\']([^"\']+)["\']',
    r'/datatables/\w+',
    r'/api/[^"\'\s]+',
    r'/module/[^"\'\s]+',
    r'/show/[^"\'\s]+',
    r'/report/[^"\'\s]+',
]

found_endpoints = set()

for pattern in patterns:
    matches = re.findall(pattern, r.text, re.IGNORECASE)
    found_endpoints.update(matches)

# Remove duplicates and sort
found_endpoints = sorted(set(found_endpoints))

if found_endpoints:
    print(f"Found {len(found_endpoints)} potential API endpoints:\n")
    for endpoint in found_endpoints:
        if not endpoint.startswith('http'):  # Filter out full URLs
            print(f"  {endpoint}")
else:
    print("No API endpoints found in HTML")
    
# Also search for "free", "disk", "storage" in script tags
print("\n\nSearching for data references...\n")

script_pattern = r'<script[^>]*>(.*?)</script>'
scripts = re.findall(script_pattern, r.text, re.DOTALL | re.IGNORECASE)

for i, script in enumerate(scripts):
    if 'free' in script.lower() or 'disk' in script.lower() or 'storage' in script.lower():
        print(f"Script {i} contains disk/free/storage references:")
        # Find lines with these keywords
        for line in script.split('\n'):
            if any(keyword in line.lower() for keyword in ['free', 'disk', 'storage', 'datatables', '/api', '/module']):
                print(f"  {line.strip()[:100]}")
        print()
