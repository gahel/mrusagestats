#!/usr/bin/env python3
"""
Debug Munki Report API - finn riktig endpoint og format
"""

import requests
import os
from urllib.parse import urljoin

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net",
    "timeout": 10,
    "verify_ssl": False
}

def test_endpoints(session):
    """Test forskjellige endpoints"""
    
    endpoints = [
        "/api/v1/machines",
        "/api/machines",
        "/machines",
        "/datatables/data",
        "/report/data",
        "/machines/data",
    ]
    
    for endpoint in endpoints:
        url = urljoin(CONFIG['base_url'], endpoint)
        print(f"\nTesting: {endpoint}")
        print(f"URL: {url}")
        
        try:
            # Prøv GET først
            resp = session.get(url, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
            print(f"  GET  → {resp.status_code}")
            if resp.status_code == 200:
                print(f"    ✓ WORKS! Response: {resp.text[:100]}")
        except:
            pass
        
        try:
            # Prøv POST
            resp = session.post(url, timeout=CONFIG['timeout'], verify=CONFIG['verify_ssl'])
            print(f"  POST → {resp.status_code}")
            if resp.status_code == 200:
                print(f"    ✓ WORKS! Response: {resp.text[:100]}")
        except:
            pass

# Bruk eksisterende cookie
cookie_file = os.path.expanduser("~/.mr_session_cookie")
if os.path.exists(cookie_file):
    with open(cookie_file, 'r') as f:
        cookie_str = f.read().strip()
    
    session = requests.Session()
    for cookie_pair in cookie_str.split(';'):
        if '=' in cookie_pair:
            key, value = cookie_pair.strip().split('=', 1)
            session.cookies.set(key, value)
    
    print(f"✓ Using session cookie: {cookie_str[:30]}...\n")
    test_endpoints(session)
else:
    print("❌ No session cookie found")
