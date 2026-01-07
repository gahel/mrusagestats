#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# All available report tables
tables = [
    "applications", "appusage", "ard", "bluetooth", "certificate", "detectx",
    "displays_info", "extensions", "fan_temps", "filevault_status", "findmymac",
    "firewall", "fonts", "gpu", "managedinstalls", "mdm_status", "munki_facts",
    "munkiinfo", "network", "network_shares", "profile", "security",
    "softwareupdate", "sophos", "timemachine", "usage_stats", "usb",
    "user_sessions", "users", "warranty", "wifi",
]

# Common disk column names to search for
disk_patterns = [
    "free", "used", "available", "capacity", "size", "disk",
    "storage", "volume", "space", "drive",
]

# authenticate
auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False
auth_request = session.post(auth_url, data={"login": login, "password": password})

if auth_request.status_code != 200:
    print("Invalid url!")
    raise SystemExit

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}

print("Searching all tables for disk-related columns:\n")
print("=" * 70)

found_columns = {}

for table in tables:
    for pattern in disk_patterns:
        col = f"{table}.{pattern}"
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=3)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                if table not in found_columns:
                    found_columns[table] = []
                sample = result['data'][0][0] if result['data'] else None
                found_columns[table].append(f"{pattern} (sample: {sample})")
                print(f"✓ {col:<45} {result.get('recordsFiltered', 0)} records")
        except Exception:
            pass

print("\n" + "=" * 70)
print("SUMMARY - Tables with disk-related data:")
print("=" * 70)

if found_columns:
    for table, cols in found_columns.items():
        print(f"\n{table}:")
        for col in cols:
            print(f"  - {col}")
else:
    print("\n❌ No disk-related columns found in any table")
