#!/usr/bin/env python3
"""
Munki Report - Get Session Cookie from Browser
Åpner nettleseren og viser instruksjoner
"""

import subprocess
import os

def open_browser_and_guide():
    """Åpne Munki Report og guide bruker gjennom å hente PHPSESSID"""
    
    print("=" * 80)
    print("🔐 Munki Report - Get Session Cookie")
    print("=" * 80)
    print()
    print("Nettleseren åpnes nå. Gjør følgende:")
    print()
    print("1. Vent på at siden laster helt (du logges inn automatisk)")
    print()
    print("2. Når du er logget inn, åpne Developer Tools:")
    print("   • macOS: Cmd + Option + I")
    print("   • Windows/Linux: F12")
    print()
    print("3. Gå til 'Application' tab (eller 'Storage' i Firefox)")
    print()
    print("4. I venstre menu, finn 'Cookies' og ekspander")
    print()
    print("5. Klikk på: https://app-munkireport-prod-norwayeast-001.azurewebsites.net")
    print()
    print("6. Finn 'PHPSESSID' i listen og kopiér hele verdien")
    print()
    print("7. Lim inn verdien under")
    print()
    print("=" * 80)
    print()
    
    # Åpne nettleseren
    url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net"
    print(f"📱 Åpner: {url}\n")
    
    try:
        subprocess.run(['open', url])  # macOS
    except:
        try:
            subprocess.run(['xdg-open', url])  # Linux
        except:
            subprocess.run(['start', url])  # Windows
    
    # Spør bruker om PHPSESSID
    phpsessid = input("Lim inn PHPSESSID verdi: ").strip()
    
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
    open_browser_and_guide()
