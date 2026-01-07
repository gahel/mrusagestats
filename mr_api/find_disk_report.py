#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try disk_report and storage related tables
tables = ["disk_report", "storage", "disks"]

# Common columns
columns_to_try = [
    "serial_number",
    "timestamp", 
    "drive",
    "size",
    "used",
    "available",
    "free",
    "free_space",
    "percentage_free",
    "percentage_used",
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

for table in tables:
    print(f"\n{table}:")
    print("-" * 70)
    
    found = False
    for col_name in columns_to_try:
        col = f"{table}.{col_name}"
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=3)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                found = True
                sample = result['data'][0][0] if result['data'] else None
                records = result.get("recordsFiltered", 0)
                print(f"✓ {col:<40} {records:>5} records  (sample: {sample})")
        except Exception:
            pass
    
    if not found:
        print("  (no data found)")
