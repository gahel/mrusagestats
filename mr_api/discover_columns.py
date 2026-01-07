#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# ReportItems from MunkiReport preferences
report_items = [
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
    "filevault_escrow",
    "filevault_status",
    "findmymac",
    "firewall",
    "fonts",
    "gpu",
    "installhistory",
    "inventory",
    "location",
    "managedinstalls",
    "mdm_status",
    "munki_facts",
    "munkiinfo",
    "munkireport",
    "munkireportinfo",
    "network",
    "network_shares",
    "performance",
    "power",
    "printer",
    "profile",
    "security",
    "softwareupdate",
    "sophos",
    "supported_os",
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

print("# CLIENT_COLUMNS = [")
print("Available columns from ReportItems:\n")

successful_columns = []
for item in report_items:
    data = {f"columns[0][name]": item}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" not in result and result.get("recordsFiltered", 0) >= 0:
            successful_columns.append(item)
            print(f'    "{item}",')
    except Exception as e:
        pass

print("# ]")
print(f"\n# Total available columns: {len(successful_columns)}")
