#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# More reportdata columns to test
test_columns = [
    "reportdata.cpu_speed",
    "reportdata.cpu_count",
    "reportdata.ram",
    "reportdata.memory_mb",
    "reportdata.disk_capacity",
    "reportdata.disk_used",
    "reportdata.disk_free",
    "reportdata.battery_health",
    "reportdata.battery_percent",
    "reportdata.thermal_pressure",
    "reportdata.app_store_updates",
    "reportdata.system_updates",
    "reportdata.security_agent",
    "reportdata.firewall",
    "reportdata.antivirus",
    "reportdata.login_time",
    "reportdata.logout_time",
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

print("Testing more reportdata columns:\n")
for col in test_columns:
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" in result:
            print(f"❌ {col}: {result['error']}")
        elif result.get("recordsFiltered", 0) > 0:
            first_value = result['data'][0][0] if result['data'] else None
            print(f"✓ {col}: OK (sample: {first_value})")
        else:
            print(f"⚠️  {col}: No data")
    except Exception as e:
        print(f"❌ {col}: Connection error")
