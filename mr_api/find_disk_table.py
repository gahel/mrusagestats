#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try different possible disk tables and columns
test_patterns = [
    ("disks", "disks.serial_number"),
    ("diskusage", "diskusage.serial_number"),
    ("disk", "disk.serial_number"),
    ("storage", "storage.serial_number"),
    ("filesystem", "filesystem.serial_number"),
    ("volumes", "volumes.serial_number"),
    ("munkiinfo", "munkiinfo.serial_number"),
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

print("Searching for disk/storage tables:\n")

for table, col in test_patterns:
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" not in result:
            count = result.get("recordsFiltered", 0)
            print(f"✓ {table:<20} has data ({count} records)")
        else:
            error = result.get('error', '')[:60]
            if 'not found' in error.lower():
                print(f"❌ {table:<20} does not exist")
            else:
                print(f"⚠️  {table:<20} {error}")
    except Exception as e:
        print(f"❌ {table:<20} Connection error")
