#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try all variations
tables = [
    "disk_report",
    "disk_reports", 
    "diskspace",
    "disk_space",
    "storage",
    "storages",
    "volumes",
    "drives",
    "partitions",
    "filesystems",
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

print("Testing table names:\n")

for table in tables:
    col = f"{table}.serial_number"
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=3)
        result = response.json()
        
        if "error" in result:
            error_msg = result['error']
            if "not found" in error_msg.lower():
                print(f"❌ {table:<20} - Table does not exist")
            else:
                # Check if column doesn't exist
                if "Unknown column" in error_msg:
                    print(f"⚠️  {table:<20} - Table exists but serial_number not a column")
                else:
                    print(f"⚠️  {table:<20} - {error_msg[:40]}")
        else:
            records = result.get("recordsFiltered", 0)
            print(f"✓ {table:<20} - Found! ({records} records)")
    except Exception as e:
        print(f"❌ {table:<20} - Error")
