#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False
auth_request = session.post(auth_url, data={"login": login, "password": password})

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}

# Test various table names
tables_to_test = ["disk", "disks", "storage", "drive", "drives", "partition", "partitions", "volume", "volumes"]

print("Testing table names for disk/storage data:\n")

for table in tables_to_test:
    col = f"{table}.serial_number"
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=2)
        result = response.json()
        
        if "error" not in result and result.get("recordsFiltered", 0) > 0:
            records = result.get("recordsFiltered", 0)
            print(f"✓ {table:<20} {records:>6} records - HAS DATA!")
        elif "error" not in result:
            print(f"? {table:<20} 0 records")
    except Exception:
        pass
