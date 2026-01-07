#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try storage table with many column variations
columns_to_try = [
    "storage.serial_number",
    "storage.timestamp",
    "storage.id",
    "storage.hostname",
    "storage.drive",
    "storage.mount",
    "storage.path",
    "storage.device",
    "storage.partition",
    "storage.total",
    "storage.used",
    "storage.free",
    "storage.available",
    "storage.capacity",
    "storage.free_space",
    "storage.available_space",
    "storage.used_space",
    "storage.percent",
    "storage.percent_free",
    "storage.percent_used",
    "storage.type",
    "storage.filesystem",
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

print("Testing storage table columns:\n")
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
    except Exception:
        pass

if found:
    print("\n" + "=" * 70)
    print(f"✓ Found {len(found)} columns in storage table!")
    print("\nAvailable columns:")
    for col in found:
        print(f"  - {col}")
else:
    print("❌ No data found in storage table with tested columns")
