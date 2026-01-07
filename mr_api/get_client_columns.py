#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Map ReportItems to likely table names
tables = [
    "applications",
    "appusage",
    "ard",
    "bluetooth",
    "certificate",
    "detectx",
    "disk_report",
    "displays_info",
    "extensions",
    "fan_temps",
    "filevault_status",
    "findmymac",
    "firewall",
    "fonts",
    "gpu",
    "managedinstalls",
    "mdm_status",
    "munki_facts",
    "munkiinfo",
    "network",
    "network_shares",
    "performance",
    "power",
    "printer",
    "profile",
    "security",
    "softwareupdate",
    "sophos",
    "timemachine",
    "usage_stats",
    "usb",
    "user_sessions",
    "users",
    "warranty",
    "wifi",
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

print("# Available CLIENT_COLUMNS from ReportItems:\n")
print("CLIENT_COLUMNS = [")

successful = []
for table in tables:
    # Try with table.serial_number
    col = f"{table}.serial_number"
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" not in result and result.get("recordsFiltered", 0) >= 0:
            successful.append(col)
            print(f'    "{col}",')
    except Exception:
        pass

print("]")
print(f"\n# Total: {len(successful)} available columns")
print("\n# Usage:")
print("# for col in CLIENT_COLUMNS:")
print("#     print(col)")
