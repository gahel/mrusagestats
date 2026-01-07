#!/usr/bin/env python3
"""
Debug script for Munki Report API
"""

import requests
import os
import keyring
from urllib.parse import urljoin

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net",
    "keychain_account": "gaute.helfjord@spk.no",
    "timeout": 10,
    "verify_ssl": False
}

COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.console_user",
    "reportdata.timestamp",
    "usage_stats.thermal_pressure",
    "usage_stats.cpu_idle",
]

def get_session_from_cookie():
    """Get existing session cookie"""
    cookie_file = os.path.expanduser("~/.mr_session_cookie")
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r') as f:
            cookie_str = f.read().strip()
        
        session = requests.Session()
        for cookie_pair in cookie_str.split(';'):
            if '=' in cookie_pair:
                key, value = cookie_pair.strip().split('=', 1)
                session.cookies.set(key, value)
        return session
    return None

def debug_request(session):
    """Debug the API request"""
    
    query_url = urljoin(CONFIG['base_url'], '/datatables/data')
    query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
    query_data['start'] = 0
    query_data['length'] = 100
    
    print("=" * 80)
    print("🔍 DEBUG: API REQUEST")
    print("=" * 80)
    print(f"\nURL: {query_url}")
    print(f"\nCookies: {dict(session.cookies)}")
    print(f"\nData being sent:")
    for key, val in query_data.items():
        print(f"  {key}: {val}")
    
    csrf_token = session.cookies.get("CSRF-TOKEN")
    print(f"\nCSRF Token: {csrf_token}")
    
    headers = {"x-csrf-token": csrf_token} if csrf_token else {}
    print(f"Headers: {headers}")
    
    print("\n" + "=" * 80)
    print("🔄 SENDING REQUEST...")
    print("=" * 80)
    
    response = session.post(
        query_url,
        data=query_data,
        headers=headers,
        timeout=CONFIG['timeout'],
        verify=CONFIG['verify_ssl']
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, val in response.headers.items():
        print(f"  {key}: {val}")
    
    print(f"\nResponse Body ({len(response.text)} chars):")
    print(response.text[:500])
    
    print("\n" + "=" * 80)

def authenticate_and_request(username, password):
    """Authenticate first, then make request"""
    
    session = requests.Session()
    
    # Step 1: Authenticate
    print("=" * 80)
    print("🔐 STEP 1: AUTHENTICATE")
    print("=" * 80)
    
    auth_url = urljoin(CONFIG['base_url'], '/auth/login')
    print(f"\nAuth URL: {auth_url}")
    print(f"Username: {username}")
    
    auth_response = session.post(
        auth_url,
        data={'login': username, 'password': password},
        timeout=CONFIG['timeout'],
        verify=CONFIG['verify_ssl']
    )
    
    print(f"Status: {auth_response.status_code}")
    print(f"Cookies after auth: {dict(session.cookies)}")
    
    # Step 2: Make data request
    print("\n" + "=" * 80)
    print("🔄 STEP 2: FETCH DATA")
    print("=" * 80)
    
    query_url = urljoin(CONFIG['base_url'], '/datatables/data')
    query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
    query_data['start'] = 0
    query_data['length'] = 100
    
    data_response = session.post(
        query_url,
        data=query_data,
        timeout=CONFIG['timeout'],
        verify=CONFIG['verify_ssl']
    )
    
    print(f"\nStatus: {data_response.status_code}")
    print(f"Response: {data_response.text[:200]}")

# Get credentials
account = CONFIG['keychain_account']
password = keyring.get_password(account, account)

if password:
    print(f"✓ Found password in Keychain for {account}\n")
    authenticate_and_request(account, password)
else:
    print(f"❌ Password not found in Keychain")
