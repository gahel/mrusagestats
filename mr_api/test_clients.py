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

# Test clients table with many column variations
columns_to_try = [
    "clients.serial_number",
    "clients.hostname",
    "clients.id",
    "clients.timestamp",
    "clients.disk_free",
    "clients.disk_used",
    "clients.disk_available",
    "clients.free",
    "clients.used",
    "clients.available",
    "clients.free_space",
    "clients.available_space",
    "clients.disk_capacity",
    "clients.total",
    "clients.capacity",
    "clients.percent_free",
    "clients.percent_used",
]

print("Testing clients table columns:\n")
print("=" * 70)

found = []
for col in columns_to_try:
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=3)
        result = response.json()
        
        if "error" not in result and result.get("recordsFiltered", 0) > 0:
            records = result.get("recordsFiltered", 0)
            sample = result['data'][0][0] if result['data'] else None
            found.append(col)
            print(f"✓ {col:<40} {records:>6} records (sample: {sample})")
        elif "error" not in result and result.get("recordsFiltered", 0) == 0:
            print(f"? {col:<40} 0 records")
    except Exception:
        pass

if found:
    print("\n" + "=" * 70)
    print(f"✓ Found {len(found)} columns in clients table!")
else:
    print("\n❌ No data found in clients table")
