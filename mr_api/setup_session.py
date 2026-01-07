#!/usr/bin/env python3
"""
Munki Report - Manual Session Cookie Setup
Kopier PHPSESSID fra nettleseren og lim inn her
"""

import os
import sys

def setup_cookie():
    """Manuell setup av session cookie"""
    
    print("=" * 80)
    print("🔐 Munki Report Session Cookie Setup")
    print("=" * 80)
    print()
    print("Instruksjoner:")
    print("1. Åpne Munki Report i nettleseren")
    print("2. Åpne Developer Tools (F12 eller Cmd+Opt+I)")
    print("3. Gå til 'Application' tab → Cookies")
    print("4. Finn PHPSESSID cookie")
    print("5. Kopier verdien og lim inn under")
    print()
    
    phpsessid = input("Lim inn PHPSESSID cookie verdi: ").strip()
    
    if not phpsessid:
        print("❌ Ingen verdi angitt")
        return False
    
    # Lagre cookie
    cookie_file = os.path.expanduser("~/.mr_session_cookie")
    with open(cookie_file, 'w') as f:
        f.write(f'PHPSESSID={phpsessid}')
    os.chmod(cookie_file, 0o600)
    
    print(f"\n✓ Session cookie lagret til {cookie_file}")
    print(f"✓ PHPSESSID: {phpsessid[:20]}...")
    print(f"\nDu kan nå kjøre: ./munki_report.py")
    return True

if __name__ == "__main__":
    setup_cookie()
