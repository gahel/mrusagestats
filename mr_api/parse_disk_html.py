#!/usr/bin/env python3
"""
Fetch and parse the disk_report page HTML to find the exact datatable endpoint
"""

import requests
import json
import re
import os

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

url = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/show/report/disk_report/storage'

r = session.get(url, timeout=5, verify=False)

# Find datatable references
patterns = [
    r"'ajax'['\"]?\s*:\s*['\"]([^'\"]*)['\"]",
    r'"ajax"\s*:\s*["\']([^"\']*)["\']',
    r'dt\.ajax[.]*url\(["\']([^"\']*)["\']',
    r'DataTable.*ajax["\']?:\s*["\']([^"\']*)["\']',
    r'\/module\/\w+\/[^\s"\'<>]*',
]

html = r.text
print("Looking for datatable endpoints in disk_report/storage HTML...\n")

endpoints = set()
for pattern in patterns:
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
    for match in matches:
        endpoints.add(match.strip())

# Also find all /module/ paths
module_paths = re.findall(r'/module/[^\s"\'<>()]+', html)
for path in module_paths:
    endpoints.add(path)

# Find all /datatables/ paths  
datatable_paths = re.findall(r'/datatables/[^\s"\'<>()]+', html)
for path in datatable_paths:
    endpoints.add(path)

print("Found endpoints:")
for ep in sorted(endpoints):
    if 'disk' in ep.lower() or 'datatable' in ep.lower():
        print(f"  {ep}")

print("\n\nSearching for DataTables.net initialization code...\n")

# Look for JavaScript that initializes DataTables
if 'ajax' in html:
    # Find context around ajax
    matches = re.finditer(r'.{0,100}ajax.{0,200}', html)
    count = 0
    for match in matches:
        if count < 3:
            print(f"Context: ...{match.group()}...\n")
            count += 1

# Try to find storage table specifically
if 'storage' in html.lower():
    matches = re.finditer(r'.{0,200}storage.{0,200}', html, re.IGNORECASE)
    count = 0
    for match in matches:
        text = match.group()
        if 'datatable' in text.lower() or 'ajax' in text.lower():
            if count < 2:
                print(f"Storage context: {text}\n")
                count += 1
