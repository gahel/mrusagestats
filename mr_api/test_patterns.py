#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try common column patterns for each report type
test_patterns = [
    ("usage_stats", [
        "usage_stats.serial_number",
        "usage_stats.timestamp",
        "usage_stats.uptime",
        "usage_stats.cpu",
        "usage_stats.memory",
        "usage_stats.disk",
    ]),
    ("users", [
        "users.serial_number",
        "users.name",
        "users.uid",
    ]),
    ("power", [
        "power.serial_number",
        "power.battery_percent",
        "power.battery_health",
        "power.ac_power",
    ]),
    ("warranty", [
        "warranty.serial_number",
        "warranty.warranty_end_date",
        "warranty.product_name",
    ]),
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

print("Testing column patterns:\n")
for table, columns in test_patterns:
    print(f"## {table}:")
    for col in columns:
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=5)
            result = response.json()
            
            if "error" in result:
                print(f"  ❌ {col}")
            else:
                print(f"  ✓ {col}")
        except Exception as e:
            print(f"  ❌ {col} (error)")
    print()
