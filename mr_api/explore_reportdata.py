#!/usr/bin/env python3
import requests
import subprocess
import json

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Common reportdata columns to test
test_columns = [
    "reportdata.serial_number",
    "reportdata.timestamp",
    "reportdata.console_user",
    "reportdata.remote_ip",
    "reportdata.machine_group",
    "reportdata.archive_status",
    "reportdata.os_version",
    "reportdata.hardware_version",
    "reportdata.report_type",
    "reportdata.uptime",
    "reportdata.memory",
    "reportdata.cpu",
    "reportdata.disk",
    "reportdata.battery",
    "reportdata.power_state",
    "reportdata.sleep_time",
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

print("Testing reportdata columns:\n")
for i, col in enumerate(test_columns):
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" in result:
            print(f"❌ {col}: {result['error']}")
        elif result.get("recordsFiltered", 0) > 0:
            # Show first record value
            first_value = result['data'][0][0] if result['data'] else None
            print(f"✓ {col}: OK (sample: {first_value})")
        else:
            print(f"⚠️  {col}: No data")
    except Exception as e:
        print(f"❌ {col}: Connection error - {str(e)}")
