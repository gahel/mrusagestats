#!/usr/bin/env python3
"""
Get fresh session cookie by logging in with Azure AD
"""

import requests
import os
import keyring
import sys
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net",
    "keychain_account": "gaute.helfjord@spk.no",
    "timeout": 30,
    "verify_ssl": False
}

def get_credentials():
    """Hent kredentialer fra Keychain"""
    account = CONFIG['keychain_account']
    password = keyring.get_password(account, account)
    
    if not password:
        print(f"❌ Passord for '{account}' ikke funnet i Keychain")
        sys.exit(1)
    
    return account, password

def get_fresh_session():
    """
    Login to Munki Report and get fresh PHPSESSID cookie
    Handles Azure AD SSO flow
    """
    print("🔐 Getting Fresh Session Cookie\n")
    
    username, password = get_credentials()
    print(f"Logging in as: {username}\n")
    
    session = requests.Session()
    session.verify = CONFIG['verify_ssl']
    
    # Step 1: Access the main page to trigger Azure AD redirect
    print("Step 1: Accessing Munki Report main page...")
    try:
        response = session.get(
            CONFIG['base_url'],
            timeout=CONFIG['timeout'],
            allow_redirects=True
        )
        print(f"  Status: {response.status_code}")
        
        # Check for Microsoft login page
        if 'login.microsoftonline.com' in response.url or 'Microsoft' in response.text[:1000]:
            print("  ✓ Redirected to Azure AD login")
        
        print(f"  Current URL: {urlparse(response.url).netloc}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Step 2: Look for the login form and submit credentials
    print("\nStep 2: Submitting Azure AD credentials...")
    try:
        # Parse the page to find form URL
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find a form action URL
        form = soup.find('form', {'id': 'credentials'})
        if form:
            form_url = form.get('action', '')
            if form_url and not form_url.startswith('http'):
                form_url = urljoin(response.url, form_url)
        else:
            # If no specific form, try common Azure AD endpoints
            form_url = None
        
        # Try different credential submission endpoints
        endpoints_to_try = [
            'https://login.microsoftonline.com/common/login',
            response.url,
            urljoin(CONFIG['base_url'], '/api/auth'),
            urljoin(CONFIG['base_url'], '/auth/login'),
        ]
        
        if form_url:
            endpoints_to_try.insert(0, form_url)
        
        success = False
        for endpoint in endpoints_to_try:
            try:
                print(f"  Trying: {urlparse(endpoint).path}...", end=" ")
                creds_response = session.post(
                    endpoint,
                    data={
                        'loginfmt': username,
                        'passwd': password,
                        'login': username,
                        'password': password,
                    },
                    timeout=CONFIG['timeout'],
                    allow_redirects=True
                )
                
                if creds_response.status_code == 200:
                    print("✓")
                    response = creds_response
                    success = True
                    break
                else:
                    print(f"({creds_response.status_code})")
            except Exception as e:
                print(f"(Error: {str(e)[:30]})")
                continue
        
        if not success:
            print("  ⚠️  Credential submission may have failed, continuing anyway...")
    
    except Exception as e:
        print(f"  ⚠️  Error parsing form: {e}")
    
    # Step 3: Navigate to data endpoint to ensure login is complete
    print("\nStep 3: Accessing API endpoint to verify login...")
    try:
        test_response = session.get(
            urljoin(CONFIG['base_url'], '/datatables/data'),
            timeout=CONFIG['timeout'],
            allow_redirects=True
        )
        print(f"  Status: {test_response.status_code}")
        
        if test_response.status_code == 200 or test_response.status_code == 400:
            print("  ✓ API endpoint accessible")
        elif test_response.status_code == 403:
            print("  ⚠️  Still getting 403, might need additional auth")
        else:
            print(f"  Status: {test_response.status_code}")
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Step 4: Extract and save cookies
    print("\nStep 4: Extracting session cookies...")
    cookies = dict(session.cookies)
    
    if not cookies:
        print("  ❌ No cookies found!")
        return False
    
    print(f"  Found {len(cookies)} cookies:")
    for key, val in cookies.items():
        print(f"    - {key}: {val[:40]}..." if len(val) > 40 else f"    - {key}: {val}")
    
    if 'PHPSESSID' not in cookies:
        print("\n  ⚠️  Warning: PHPSESSID not found in cookies")
        print("      The login may have failed. Try using the web UI manually.")
    
    # Save cookies
    try:
        cookie_file = os.path.expanduser("~/.mr_session_cookie")
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        with open(cookie_file, 'w') as f:
            f.write(cookie_str)
        os.chmod(cookie_file, 0o600)
        
        print(f"\n✓ Session cookies saved to {cookie_file}")
        return True
    
    except Exception as e:
        print(f"\n❌ Error saving cookies: {e}")
        return False

if __name__ == "__main__":
    get_fresh_session()
