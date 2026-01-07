#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Check which columns exist in managedinstalls, munkiinfo and other tables
tables_to_check = ["managedinstalls", "munkiinfo", "inventory"]

common_cols = [
    "serial_number", "timestamp", "name", "size", "free", "used", "available",
    "disk_free", "disk_used", "disk_available", "hdd", "ssd", "storage",
    "free_space", "available_space", "capacity",
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

for table in tables_to_check:
    print(f"\n{table}:")
    print("-" * 60)
    
    found = []
    for col_name in common_cols:
        col = f"{table}.{col_name}"
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=3)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                sample = result['data'][0][0] if result['data'] else None
                found.append(col_name)
                print(f"✓ {col_name:<20} {result.get('recordsFiltered', 0):>5} records  (sample: {sample})")
        except Exception:
            pass
    
    if not found:
        print("  (no columns found)")
