#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Explore disk-related columns
explore_columns = {
    "disk_report": [
        "disk_report.serial_number",
        "disk_report.timestamp",
        "disk_report.disk_size",
        "disk_report.disk_used",
        "disk_report.disk_free",
        "disk_report.disk_available",
        "disk_report.percentage_used",
        "disk_report.percentage_free",
        "disk_report.drive",
    ],
    "usage_stats": [
        "usage_stats.disk",
        "usage_stats.disk_free",
        "usage_stats.disk_used",
        "usage_stats.disk_available",
    ],
}

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

print("Exploring disk-related columns:\n")

for table, columns in explore_columns.items():
    print(f"## {table}:")
    found = []
    for col in columns:
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=5)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                sample = result['data'][0][0] if result['data'] else None
                found.append(col)
                print(f"  ✓ {col:<40} (sample: {sample})")
            elif "error" not in result:
                found.append(col)
                print(f"  ? {col:<40} (no data)")
        except Exception as e:
            pass
    print()
