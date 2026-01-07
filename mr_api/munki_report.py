#!/usr/bin/env python3
"""
Munki Report API Script
Henter maskiner med høy thermal pressure og viser usage stats
"""

import requests
import json
import sys
import os
import keyring
from typing import List, Dict, Optional
from urllib.parse import urljoin
from datetime import datetime

# Konfigurasjon
CONFIG = {
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?",  # MR v5 format
    "keychain_account": "gaute.helfjord@spk.no",  # Din Azure AD e-postadresse (brukes som søkenøkkel)
    "timeout": 10,
    "verify_ssl": False,  # For testing, sett til True i produksjon
    "msal_client_id": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",  # Default Azure CLI client ID
    "msal_tenant_id": "common"
}

# Kolonner vi ønsker å hente
COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.console_user",
    "reportdata.timestamp",
    "usage_stats.thermal_pressure",
    "usage_stats.cpu_idle",
]


def get_credentials() -> tuple[str, str]:
    """Henter brukernavn og passord fra Keychain eller miljøvariabler"""
    
    # Sjekk miljøvariabler først
    username = os.environ.get('MR_USERNAME')
    password = os.environ.get('MR_PASSWORD')
    
    if username and password:
        return username, password
    
    account = CONFIG['keychain_account']
    
    # Prøv å hente passord fra Keychain
    password = keyring.get_password(account, account)
    
    if not password:
        print(f"❌ Passord for '{account}' ikke funnet i Keychain eller som MR_PASSWORD")
        print(f"\nAlternativer:")
        print(f"  1. Sett miljøvariabler: MR_USERNAME=user MR_PASSWORD=pass python3 munki_report.py")
        print(f"  2. Lagre i Keychain: security add-generic-password -s '{account}' -a '{account}' -w")
        sys.exit(1)
    
    return account, password


def get_session_from_cookie() -> Optional[requests.Session]:
    """Prøver å bruke eksisterende session cookie fra MR_SESSION_COOKIE miljøvariabel"""
    
    # Sjekk miljøvariabel først
    cookie_str = os.environ.get('MR_SESSION_COOKIE')
    
    # Hvis ikke miljøvariabel, prøv å hente fra fil
    if not cookie_str:
        cookie_file = os.path.expanduser("~/.mr_session_cookie")
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r') as f:
                    cookie_str = f.read().strip()
            except:
                pass
    
    if not cookie_str:
        return None
    
    session = requests.Session()
    
    # Parse cookie string (format: "PHPSESSID=xxx; OTHER=yyy")
    for cookie_pair in cookie_str.split(';'):
        if '=' in cookie_pair:
            key, value = cookie_pair.strip().split('=', 1)
            session.cookies.set(key, value)
    
    return session


def save_session_cookie(session: requests.Session):
    """Lagre session cookie til fil for senere bruk"""
    try:
        phpsessid = session.cookies.get('PHPSESSID', '')
        if phpsessid:
            cookie_file = os.path.expanduser("~/.mr_session_cookie")
            with open(cookie_file, 'w') as f:
                f.write(f'PHPSESSID={phpsessid}')
            # Sett permissions til 600 (read/write kun for owner)
            os.chmod(cookie_file, 0o600)
            print(f"✓ Session cookie lagret til {cookie_file}")
    except Exception as e:
        print(f"⚠️  Kunne ikke lagre session cookie: {e}", file=sys.stderr)


def setup_credentials():
    """Interaktiv oppsett av kredentialer"""
    service = CONFIG['keychain_service']
    username = CONFIG['keychain_username']
    
    print("🔐 Munki Report API - Keychain Setup\n")
    print(f"Dette vil lagre dine Munki Report-kredentialer i macOS Keychain")
    print(f"Service: {service}")
    print(f"Bruker: {username}\n")
    
    password = input("Skriv inn Munki Report-passordet for denne brukeren: ")
    
    if not password:
        print("Avbrutt.")
        sys.exit(1)
    
    try:
        keyring.set_password(service, username, password)
        print(f"\n✓ Passord lagret i Keychain!")
        print(f"Du kan nå kjøre scriptet normalt: python3 munki_report.py")
    except Exception as e:
        print(f"❌ Feil ved lagring i Keychain: {e}", file=sys.stderr)
        sys.exit(1)


def authenticate(username: str, password: str) -> requests.Session:
    """Autentiserer med Azure AD og returnerer en session"""
    session = requests.Session()
    
    try:
        # Prøv først med MSAL hvis det er installert
        try:
            import msal
            print("Bruker MSAL for Azure AD autentisering...")
            
            app = msal.PublicClientApplication(
                client_id=CONFIG['msal_client_id'],
                authority=f"https://login.microsoftonline.com/{CONFIG['msal_tenant_id']}"
            )
            
            # Resource ID for Munki Report API (må være riktig tenant ID)
            # Hent access token med Resource Owner Password Credentials flow
            result = app.acquire_token_by_username_password(
                username=username,
                password=password,
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if not result or 'access_token' not in result:
                print(f"Advarsel: MSAL autentisering mislyktes, prøver fallback", file=sys.stderr)
                raise Exception("MSAL failed")
            
            # Bruk access token
            session.headers['Authorization'] = f"Bearer {result['access_token']}"
            print("✓ Azure AD autentisert med MSAL")
            return session
        
        except ImportError:
            print("Advarsel: msal ikke installert, bruker fallback", file=sys.stderr)
        except Exception as e:
            print(f"Advarsel: MSAL mislyktes ({e}), bruker fallback", file=sys.stderr)
        
        # Fallback: Prøv direkte API login med cookies
        print("Forsøker direkte API autentisering...")
        auth_url = urljoin(CONFIG['base_url'], '/auth/login')
        
        response = session.post(
            auth_url,
            data={
                'login': username,
                'password': password
            },
            timeout=CONFIG['timeout'],
            verify=CONFIG['verify_ssl']
        )
        
        # Hvis 302 redirect, follow it
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"✓ Autentisering redirect mottatt ({response.status_code})")
            return session
        
        if response.status_code == 200:
            print("✓ Autentisering OK")
            return session
        
        # Hvis ikke success, prøv allikevel da cookies kan være satt
        if 'PHPSESSID' in session.cookies:
            print("✓ PHPSESSID mottatt fra autentisering")
            return session
        
        print(f"⚠️  Autentisering returnerte status {response.status_code}, prøver allikevel...")
        return session
    
    except requests.exceptions.RequestException as e:
        print(f"Advarsel ved autentisering: {e}", file=sys.stderr)
        print("Vil prøve med eksisterende cookies allikevel", file=sys.stderr)
        return session


def get_machines(session: requests.Session) -> List[Dict]:
    """Henter liste over alle maskiner fra Munki Report"""
    try:
        # MR v5: /datatables/data
        query_url = urljoin(CONFIG['base_url'], '/datatables/data')
        
        # Generer query fra kolonner
        query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
        
        # Hent CSRF-token fra session cookies
        csrf_token = session.cookies.get("CSRF-TOKEN")
        headers = {"x-csrf-token": csrf_token} if csrf_token else {}
        
        response = session.post(
            query_url,
            data=query_data,
            headers=headers,
            timeout=CONFIG['timeout'],
            verify=CONFIG['verify_ssl']
        )
        
        # Debug 403
        if response.status_code == 403:
            print(f"Debug 403: {response.text[:500]}", file=sys.stderr)
        
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        return data.get('data', [])
    
    except requests.exceptions.RequestException as e:
        print(f"Feil ved henting av maskiner: {e}", file=sys.stderr)
        return []


def filter_non_nominal(machines: List[List]) -> List[List]:
    """Filtrerer maskiner med høy thermal pressure (Heavy/Critical)"""
    high_thermal = []
    
    for machine in machines:
        # machine er en liste: [serial, hostname, desc, user, timestamp, thermal_pressure]
        if len(machine) > 5:
            thermal = str(machine[5]).lower()
            # Filtrer etter High/Heavy/Critical thermal pressure
            if thermal in ["heavy", "high", "critical"]:
                high_thermal.append(machine)
    
    return high_thermal


def find_thermal_issues(session: requests.Session) -> tuple:
    """Finner maskiner med høy thermal pressure"""
    
    print("Henter maskiner fra Munki Report...")
    machines = get_machines(session)
    
    if not machines:
        print("Ingen maskiner funnet")
        return [], []
    
    print(f"Hentet {len(machines)} maskiner, analyserer thermal pressure...\n")
    
    # Filtrer maskiner med høy thermal pressure
    high_thermal = filter_non_nominal(machines)
    
    return high_thermal, machines  # Returner både high_thermal og all machines for stats


def print_results(issues: List[List], all_machines: List[List] = None, session: Optional[requests.Session] = None):
    """Skriver ut resultater på pent format med health status rapport"""
    
    # Print high thermal machines
    if not issues:
        print("\n✓ Alle maskiner har normal thermal pressure\n")
    else:
        print(f"\n⚠️  Fant {len(issues)} maskin(er) med HIGH thermal pressure:\n")
        print(f"{'Serial':<20} {'Hostname':<25} {'Bruker':<20} {'Thermal':<15} {'Sist rapport':<20}")
        print("-" * 100)
        
        now = int(datetime.now().timestamp())
        
        for machine in issues:
            serial = str(machine[0])[:20] if len(machine) > 0 else "unknown"
            hostname = str(machine[1])[:25] if len(machine) > 1 else "unknown"
            user = str(machine[3])[:20] if len(machine) > 3 else "unknown"
            thermal = str(machine[5])[:15] if len(machine) > 5 else "unknown"
            
            # Format timestamp
            last_report = "unknown"
            if len(machine) > 4:
                try:
                    timestamp = int(machine[4])
                    age_seconds = now - timestamp
                    
                    if age_seconds < 3600:
                        last_report = f"{int(age_seconds / 60)} min siden"
                    elif age_seconds < 86400:
                        last_report = f"{int(age_seconds / 3600)} timer siden"
                    elif age_seconds < 604800:
                        last_report = f"{int(age_seconds / 86400)} dager siden"
                    else:
                        last_report = f"{int(age_seconds / 604800)} uker siden"
                except (ValueError, TypeError):
                    pass
            
            print(
                f"{serial:<20} {hostname:<25} {user:<20} {thermal:<15} {last_report:<20}"
            )
    
    # ===== DISK SPACE =====
    if all_machines:
        print("\n" + "="*80)
        print("💾 DISK SPACE STATUS")
        print("="*80 + "\n")
        print("⚠️  Disk data ikke tilgjengelig via /datatables/data API")
        print("    (disk_report tabell finnes ikke i databasen)")
        print("\n    Sjekk Storage Report i Munki Report web UI for disk space detaljer")
        print("    URL: https://app-munkireport-prod-norwayeast-001.azurewebsites.net")
        print(f"\n    Total maskiner å sjekke: {len(all_machines)}")

    
    # Print comprehensive health status
    if all_machines:
        print("\n" + "="*80)
        print("🏥 HEALTH STATUS - Maskinpark Overview")
        print("="*80 + "\n")
        
        # ========== THERMAL PRESSURE STATS ==========
        thermal_counts = {}
        for machine in all_machines:
            if len(machine) > 5:
                thermal = str(machine[5])
                thermal_counts[thermal] = thermal_counts.get(thermal, 0) + 1
        
        total = len(all_machines)
        
        print("🌡️  THERMAL PRESSURE")
        print("-" * 40)
        for thermal, count in sorted(thermal_counts.items(), key=lambda x: -x[1]):
            percentage = (count / total) * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"{thermal:<15} {count:3d} ({percentage:5.1f}%) {bar}")
        
        # ========== CPU LOAD STATS ==========
        cpu_loads = []
        for machine in all_machines:
            if len(machine) > 6:
                try:
                    idle_str = str(machine[6]).replace('%', '').strip()
                    idle_percent = float(idle_str)
                    cpu_load = 100 - idle_percent
                    cpu_loads.append(cpu_load)
                except (ValueError, TypeError):
                    pass
        
        print("\n\n⚙️  CPU LOAD")
        print("-" * 40)
        
        if cpu_loads:
            avg_cpu = sum(cpu_loads) / len(cpu_loads)
            max_cpu = max(cpu_loads)
            min_cpu = min(cpu_loads)
            
            print(f"Average Load: {avg_cpu:5.1f}%")
            print(f"Min Load:     {min_cpu:5.1f}%")
            print(f"Max Load:     {max_cpu:5.1f}%")
            
            # Distribution
            ranges = [
                (0, 25, "Low (0-25%)"),
                (25, 50, "Moderate (25-50%)"),
                (50, 75, "High (50-75%)"),
                (75, 100, "Very High (75-100%)"),
            ]
            
            print("\nDistribution:")
            for min_val, max_val, label in ranges:
                count = sum(1 for cpu in cpu_loads if min_val <= cpu < max_val)
                if count > 0:
                    pct = (count / len(cpu_loads)) * 100
                    bar = "█" * int(pct / 2)
                    print(f"{label:<20} {count:3d} ({pct:5.1f}%) {bar}")
        
        # ========== DISK SPACE STATS ==========
        print("\n\n💾 DISK SPACE STATUS")
        print("-" * 40)
        
        # Fetch disk stats from module endpoint
        if session:
            try:
                url = CONFIG['base_url'].rstrip('?') + '/module/disk_report/get_stats'
                disk_resp = session.get(url, timeout=5, verify=CONFIG['verify_ssl'])
                if disk_resp.status_code == 200:
                    disk_data = disk_resp.json()
                    stats = disk_data.get('stats', {})
                    thresholds = disk_data.get('thresholds', {})
                    
                    success = stats.get('success', 0)
                    warning = stats.get('warning', 0)
                    danger = stats.get('danger', 0)
                    
                    print(f"✓ {success} machines  >= {thresholds.get('warning', 10)}GB free")
                    if warning > 0:
                        print(f"⚠️  {warning} machines  {thresholds.get('danger', 5)}-{thresholds.get('warning', 10)}GB free")
                    if danger > 0:
                        print(f"🔴 {danger} machines < {thresholds.get('danger', 5)}GB free")
                    
                    if warning == 0 and danger == 0:
                        print("✓ All machines have adequate disk space!")
            except Exception as e:
                print(f"⚠️  Could not fetch disk stats: {e}")
        else:
            print("⚠️  Session not available for disk stats")
        
        # ========== ACTIVITY STATS ==========
        print("\n\n📡 ACTIVITY STATUS (last report)")
        print("-" * 40)
        
        now = int(datetime.now().timestamp())
        time_ranges = [
            (3600, "< 1 hour"),
            (86400, "< 1 day"),
            (604800, "< 1 week"),
            (2592000, "< 1 month"),
            (9999999999, "> 1 month")
        ]
        
        activity_counts = {label: 0 for _, label in time_ranges}
        
        for machine in all_machines:
            if len(machine) > 4:
                try:
                    timestamp = int(machine[4])
                    age_seconds = now - timestamp
                    
                    for max_age, label in time_ranges:
                        if age_seconds <= max_age:
                            activity_counts[label] += 1
                            break
                except (ValueError, TypeError):
                    pass
        
        for _, label in time_ranges:
            count = activity_counts[label]
            if count > 0:
                percentage = (count / total) * 100
                bar_length = int(percentage / 2)
                bar = "█" * bar_length
                print(f"{label:<15} {count:3d} ({percentage:5.1f}%) {bar}")
        
        # ========== SUMMARY ==========
        print("\n\n📋 SUMMARY")
        print("-" * 40)
        print(f"Total machines:     {total}")
        print(f"Normal thermal:     {thermal_counts.get('Nominal', 0)}")
        print(f"Heavy thermal:      {thermal_counts.get('Heavy', 0)}")
        if cpu_loads:
            print(f"Avg CPU load:       {avg_cpu:.1f}%")
        print(f"Recent activity:    {activity_counts['< 1 hour']} last hour")
        
        print()


def main():
    """Hovedfunksjon"""
    
    print("🔍 Munki Report - Thermal Pressure Checker\n")
    
    # Prøv først å bruke eksisterende session cookie
    print("Prøver å bruke session cookie fra MR_SESSION_COOKIE...")
    session = get_session_from_cookie()
    
    if session:
        print("✓ Bruker eksisterende session cookie\n")
        
        # Test om cookien er gyldig
        try:
            print("Tester session cookie...")
            test_resp = session.get(
                CONFIG['base_url'].rstrip('?') + '/datatables/data',
                timeout=CONFIG['timeout'],
                verify=CONFIG['verify_ssl']
            )
            
            if test_resp.status_code == 200:
                print("✓ Session cookie er gyldig!\n")
                # Bruk denne sessionnen
                high_thermal, all_machines = find_thermal_issues(session)
                print_results(high_thermal, all_machines, session)
                return
            elif test_resp.status_code == 403:
                print("✗ Session cookie er utløpt eller API har problemer\n")
        except Exception as e:
            print(f"✗ Feil ved testing av cookie: {e}\n")
    
    # Hvis ingen gyldig cookie, prøv med brukernavn/passord
    print("Henter kredentialer fra Keychain...")
    username, password = get_credentials()
    
    # Autentiser
    print("Autentiserer...")
    session = authenticate(username, password)
    print("✓ Autentisert\n")
    
    # Prøv å hente maskiner
    print("Henter maskiner fra Munki Report...")
    high_thermal, all_machines = find_thermal_issues(session)
    
    # Hvis ingen maskiner, fallback til machines.json
    if not all_machines:
        print("⚠️  Fikk ingen maskiner fra API, bruker machines.json...\n")
        try:
            with open("machines.json", 'r') as f:
                import json
                parsed_machines = json.load(f)
            
            # Konverter til raw format for print_results
            all_machines = [
                [
                    m.get('serial_number'),
                    m.get('hostname'),
                    m.get('description'),
                    m.get('console_user'),
                    m.get('last_report', {}).get('timestamp'),
                    m.get('thermal_pressure'),
                    f"{m.get('cpu', {}).get('idle_percent', 0)}%"
                ]
                for m in parsed_machines
            ]
            high_thermal = [m for m in all_machines if len(m) > 5 and m[5] == 'Heavy']
            print(f"✓ Lastet {len(all_machines)} maskiner fra machines.json\n")
        except FileNotFoundError:
            print("❌ Kunne ikke hente maskiner fra API eller machines.json")
            sys.exit(1)
    
    print_results(high_thermal, all_machines, session)
    
    # Lagre session cookie automatisk for neste gang
    print("\n" + "="*80)
    save_session_cookie(session)
    print("="*80)


if __name__ == "__main__":
    main()
