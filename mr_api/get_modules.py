#!/usr/bin/env python3
"""
Get list of installed modules to see what's available for data tables
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

# From Postman collection, check installed modules
url = urljoin(CONFIG['base_url'], '/install/dump_modules/env')

try:
    r = session.post(url, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
    print(f"Status: {r.status_code}")
    print(f"\nResponse:\n{r.text}")
except Exception as e:
    print(f"Error: {e}")
