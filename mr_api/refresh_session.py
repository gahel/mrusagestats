#!/usr/bin/env python3
"""
Refresh Munki Report session cookie
Brukes for å få en frisk session cookie
"""

import requests
import os
import keyring
from urllib.parse import urljoin

CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?",
    "keychain_account": "gaute.helfjord@spk.no",
    "timeout": 10,
    "verify_ssl": False
}

def get_credentials():
    """Hent kredentialer fra Keychain"""
    account = CONFIG['keychain_account']
    password = keyring.get_password(account, account)
    
    if not password:
        print(f"❌ Passord for '{account}' ikke funnet i Keychain")
        exit(1)
    
    return account, password

def refresh_session_cookie():
    """Autentiser og lagre frisk session cookie"""
    
    print("🔐 Refreshing Munki Report session cookie...\n")
    
    username, password = get_credentials()
    
    session = requests.Session()
    
    try:
        auth_url = urljoin(CONFIG['base_url'], '/auth/login')
        print(f"Autentiserer som {username}...")
        
        response = session.post(
            auth_url,
            data={'login': username, 'password': password},
            timeout=CONFIG['timeout'],
            verify=CONFIG['verify_ssl']
        )
        
        if response.status_code != 200:
            print(f"❌ Autentisering mislyktes (status {response.status_code})")
            exit(1)
        
        # Lagre ALL cookies (ikke bare PHPSESSID)
        all_cookies = dict(session.cookies)
        print(f"\nCookies mottatt:")
        for key, val in all_cookies.items():
            print(f"  {key}: {val[:30]}..." if len(val) > 30 else f"  {key}: {val}")
        
        # Lagre cookies som header-string
        cookie_file = os.path.expanduser("~/.mr_session_cookie")
        cookie_str = "; ".join([f"{k}={v}" for k, v in all_cookies.items()])
        with open(cookie_file, 'w') as f:
            f.write(cookie_str)
        os.chmod(cookie_file, 0o600)
        print(f"\n✓ Session cookies lagret til {cookie_file}")
        print(f"✓ Total cookies: {len(all_cookies)}")
        print(f"\nDu kan nå kjøre: ./munki_report.py")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Feil: {e}")
        return False

if __name__ == "__main__":
    refresh_session_cookie()
