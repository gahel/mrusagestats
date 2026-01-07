#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try generic column approach - test with "free" since we know Free Disk Space is tracked
# Maybe it's in a table we haven't tried
test_tables = [
    "disk_info", "disk_data", "system_info", "device_info",
    "computer", "computers", "inventory", "hardware",
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

print("Testing additional table names for disk free/used/available:\n")

for table in test_tables:
    for col_suffix in ["free", "used", "available", "serial_number"]:
        col = f"{table}.{col_suffix}"
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=2)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                records = result.get("recordsFiltered", 0)
                sample = result['data'][0][0] if result['data'] else None
                print(f"✓ {col:<40} {records:>5} records")
        except Exception:
            pass
