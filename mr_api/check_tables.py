#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try to get performance table with just serial_number to see if it has data
test_cols = {
    "performance": ["performance.serial_number", "performance.timestamp"],
    "disk_report": ["disk_report.serial_number", "disk_report.timestamp"],
    "fan_temps": ["fan_temps.serial_number", "fan_temps.timestamp"],
    "security": ["security.serial_number"],
    "power": ["power.serial_number", "power.timestamp"],
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

print("Checking which tables have data:\n")

for table, columns in test_cols.items():
    data = {f"columns[{i}][name]": c for i, c in enumerate(columns)}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" not in result:
            count = result.get("recordsFiltered", 0)
            status = "✓" if count > 0 else "?"
            print(f"{status} {table:<20} ({count} records)")
        else:
            print(f"❌ {table:<20} Error: {result['error'][:50]}")
    except Exception as e:
        print(f"❌ {table:<20} Connection error")
