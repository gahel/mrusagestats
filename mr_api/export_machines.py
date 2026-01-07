#!/usr/bin/env python3
"""
Munki Report - Export Machines to JSON
Henter all relevant data fra Munki Report og eksporterer til JSON for analyse
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
    "base_url": "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?",
    "keychain_account": "gaute.helfjord@spk.no",
    "timeout": 10,
    "verify_ssl": False
}

# Alle kolonner vi ønsker å hente
COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.console_user",
    "reportdata.timestamp",
    "usage_stats.thermal_pressure",
    "usage_stats.cpu_idle",
    "storage.hdd_free",
    "storage.hdd_total",
]


def get_credentials() -> tuple[str, str]:
    """Henter brukernavn og passord fra Keychain eller miljøvariabler"""
    username = os.environ.get('MR_USERNAME')
    password = os.environ.get('MR_PASSWORD')
    
    if username and password:
        return username, password
    
    account = CONFIG['keychain_account']
    password = keyring.get_password(account, account)
    
    if not password:
        print(f"❌ Passord for '{account}' ikke funnet i Keychain")
        sys.exit(1)
    
    return account, password


def get_session_from_cookie() -> Optional[requests.Session]:
    """Prøver å bruke eksisterende session cookie"""
    cookie_str = os.environ.get('MR_SESSION_COOKIE')
    
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
    for cookie_pair in cookie_str.split(';'):
        if '=' in cookie_pair:
            key, value = cookie_pair.strip().split('=', 1)
            session.cookies.set(key, value)
    
    return session


def save_session_cookie(session: requests.Session):
    """Lagre session cookie til fil"""
    try:
        phpsessid = session.cookies.get('PHPSESSID', '')
        if phpsessid:
            cookie_file = os.path.expanduser("~/.mr_session_cookie")
            with open(cookie_file, 'w') as f:
                f.write(f'PHPSESSID={phpsessid}')
            os.chmod(cookie_file, 0o600)
    except:
        pass


def authenticate(username: str, password: str) -> requests.Session:
    """Autentiserer og returnerer en session"""
    session = requests.Session()
    
    try:
        auth_url = urljoin(CONFIG['base_url'], '/auth/login')
        response = session.post(
            auth_url,
            data={'login': username, 'password': password},
            timeout=CONFIG['timeout'],
            verify=CONFIG['verify_ssl']
        )
        
        if response.status_code != 200:
            print(f"❌ Autentisering mislyktes (status {response.status_code})", file=sys.stderr)
            sys.exit(1)
        
        return session
    except requests.exceptions.RequestException as e:
        print(f"❌ Feil ved autentisering: {e}", file=sys.stderr)
        sys.exit(1)


def get_machines(session: requests.Session) -> List[List]:
    """Henter liste over alle maskiner fra Munki Report"""
    try:
        query_url = urljoin(CONFIG['base_url'], '/datatables/data')
        query_data = {f"columns[{i}][name]": col for i, col in enumerate(COLUMNS)}
        # Legg til standard datatable parametere
        query_data['start'] = 0
        query_data['length'] = 10000  # Hent maks 10000
        
        csrf_token = session.cookies.get("CSRF-TOKEN")
        headers = {"x-csrf-token": csrf_token} if csrf_token else {}
        
        response = session.post(
            query_url,
            data=query_data,
            headers=headers,
            timeout=CONFIG['timeout'],
            verify=CONFIG['verify_ssl']
        )
        
        if response.status_code != 200:
            print(f"❌ Status {response.status_code}: {response.text[:200]}", file=sys.stderr)
            return []
        
        data = response.json()
        machines = data.get('data', [])
        total = data.get('recordsTotal', 0)
        print(f"Hentet {len(machines)} av {total} maskiner", file=sys.stderr)
        return machines
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Feil ved henting av maskiner: {e}", file=sys.stderr)
        return []


def parse_machine_data(machine: List) -> Dict:
    """Konverterer raw machine data til strukturert dictionary"""
    
    now = int(datetime.now().timestamp())
    
    # Parse timestamp (index 4)
    last_report_timestamp = None
    last_report_age = None
    if len(machine) > 4:
        try:
            last_report_timestamp = int(machine[4])
            last_report_age = now - last_report_timestamp
        except (ValueError, TypeError):
            pass
    
    # Parse CPU (index 6)
    cpu_idle_percent = None
    cpu_load_percent = None
    if len(machine) > 6:
        try:
            idle_str = str(machine[6]).replace('%', '').strip()
            cpu_idle_percent = float(idle_str)
            cpu_load_percent = 100 - cpu_idle_percent
        except (ValueError, TypeError):
            pass
    
    # Parse disk (index 7 og 8) - prøv storage.hdd_free/hdd_total
    disk_used_gb = None
    disk_total_gb = None
    disk_free_gb = None
    disk_free_percent = None
    if len(machine) > 8:
        try:
            hdd_free = int(machine[7]) if machine[7] else 0
            hdd_total = int(machine[8]) if machine[8] else 0
            if hdd_total > 0:
                disk_free_gb = hdd_free / (1024 * 1024 * 1024)
                disk_total_gb = hdd_total / (1024 * 1024 * 1024)
                disk_used_gb = disk_total_gb - disk_free_gb
                disk_free_percent = (hdd_free / hdd_total) * 100
        except (ValueError, TypeError):
            pass
    
    parsed = {
        "serial_number": machine[0] if len(machine) > 0 else None,
        "hostname": machine[1] if len(machine) > 1 else None,
        "description": machine[2] if len(machine) > 2 else None,
        "console_user": machine[3] if len(machine) > 3 else None,
        "last_report": {
            "timestamp": last_report_timestamp,
            "age_seconds": last_report_age,
            "age_human": format_age(last_report_age) if last_report_age else None
        },
        "thermal_pressure": machine[5] if len(machine) > 5 else None,
        "cpu": {
            "idle_percent": cpu_idle_percent,
            "load_percent": cpu_load_percent
        },
        "disk": {
            "used_gb": round(disk_used_gb, 2) if disk_used_gb else None,
            "total_gb": round(disk_total_gb, 2) if disk_total_gb else None,
            "free_gb": round(disk_free_gb, 2) if disk_free_gb else None,
            "free_percent": round(disk_free_percent, 2) if disk_free_percent else None
        }
    }
    
    return parsed


def format_age(seconds: int) -> str:
    """Konverterer sekunder til menneskelesbar format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h"
    elif seconds < 604800:
        return f"{int(seconds / 86400)}d"
    else:
        return f"{int(seconds / 604800)}w"


def export_to_json(machines: List[Dict], output_file: str = "machines.json"):
    """Eksporterer data til JSON fil"""
    try:
        with open(output_file, 'w') as f:
            json.dump(machines, f, indent=2)
        print(f"✓ Eksportert {len(machines)} maskiner til {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Feil ved eksport: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Hovedfunksjon"""
    
    print("📊 Munki Report - Export Machines\n")
    
    # Prøv session cookie først
    print("Sjekker session cookie...")
    session = get_session_from_cookie()
    
    if session:
        print("✓ Bruker eksisterende session cookie\n")
        try:
            test_resp = session.get(
                CONFIG['base_url'].rstrip('?') + '/datatables/data',
                timeout=CONFIG['timeout'],
                verify=CONFIG['verify_ssl']
            )
            if test_resp.status_code != 200:
                session = None
        except:
            session = None
    
    # Hvis ikke gyldig cookie, autentiser
    if not session:
        print("Autentiserer med brukernavn/passord...")
        username, password = get_credentials()
        session = authenticate(username, password)
        print("✓ Autentisert\n")
    
    # Hent maskiner
    print("Henter maskiner fra Munki Report...")
    raw_machines = get_machines(session)
    
    if not raw_machines:
        print("❌ Ingen maskiner funnet")
        sys.exit(1)
    
    print(f"✓ Hentet {len(raw_machines)} maskiner\n")
    
    # Parse data
    print("Prosesserer data...")
    parsed_machines = [parse_machine_data(m) for m in raw_machines]
    
    # Lagre session cookie
    save_session_cookie(session)
    
    # Eksporter til JSON
    print()
    output_file = export_to_json(parsed_machines)
    
    # Skriv ut statistikk
    print("\n" + "="*60)
    print("📈 STATISTIKK")
    print("="*60)
    
    # Termisk stress
    thermal_counts = {}
    for m in parsed_machines:
        thermal = m.get('thermal_pressure', 'Unknown')
        thermal_counts[thermal] = thermal_counts.get(thermal, 0) + 1
    
    print("\n🌡️  Thermal Pressure:")
    for thermal, count in sorted(thermal_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(parsed_machines)) * 100
        print(f"   {thermal:<15} {count:3d} ({pct:5.1f}%)")
    
    # Disk space
    low_disk = [m for m in parsed_machines if m['disk']['free_gb'] and m['disk']['free_gb'] < 20]
    if low_disk:
        print(f"\n💾 Lite diskplass (<20GB ledig):")
        for m in sorted(low_disk, key=lambda x: x['disk']['free_gb'] or 0)[:10]:
            print(f"   {m['hostname']:<25} {m['disk']['free_gb']:.1f}GB ledig av {m['disk']['total_gb']:.1f}GB ({m['disk']['free_percent']:.1f}%)")
        if len(low_disk) > 10:
            print(f"   ... og {len(low_disk) - 10} flere")
    else:
        print(f"\n💾 Alle maskiner har >20GB ledig diskplass ✓")
    
    # High CPU load
    high_cpu = [m for m in parsed_machines if m['cpu']['load_percent'] and m['cpu']['load_percent'] > 75]
    if high_cpu:
        print(f"\n⚙️  Høy CPU-belastning (>75%):")
        for m in high_cpu[:5]:
            print(f"   {m['hostname']:<25} {m['cpu']['load_percent']:.1f}% load")
        if len(high_cpu) > 5:
            print(f"   ... og {len(high_cpu) - 5} flere")
    
    # Inactive machines
    old_machines = [m for m in parsed_machines if m['last_report']['age_seconds'] and m['last_report']['age_seconds'] > 2592000]
    if old_machines:
        print(f"\n⏱️  Inaktive maskiner (>30 dager):")
        for m in old_machines[:5]:
            print(f"   {m['hostname']:<25} {m['last_report']['age_human']}")
        if len(old_machines) > 5:
            print(f"   ... og {len(old_machines) - 5} flere")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
