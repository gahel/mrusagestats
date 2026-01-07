#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try to find disk-related columns in munkiinfo
explore_columns = [
    "munkiinfo.serial_number",
    "munkiinfo.timestamp",
    "munkiinfo.disk_free",
    "munkiinfo.disk_used",
    "munkiinfo.disk_available",
    "munkiinfo.disk_size",
    "munkiinfo.disk_capacity",
    "munkiinfo.free_space",
    "munkiinfo.available_space",
    "munkiinfo.drive_free",
    "munkiinfo.volume_free",
    "munkiinfo.hdd_free",
    "munkiinfo.ssd_free",
    "munkiinfo.percentage_free",
    "munkiinfo.percentage_used",
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

print("Exploring munkiinfo columns:\n")

found = []
for col in explore_columns:
    data = {f"columns[0][name]": col}
    try:
        response = session.post(query_url, data=data, headers=headers, timeout=5)
        result = response.json()
        
        if "error" not in result and result.get("recordsFiltered", 0) > 0:
            sample = result['data'][0][0] if result['data'] else None
            found.append(col)
            print(f"✓ {col:<40} (sample: {sample})")
    except Exception:
        pass

if found:
    print(f"\n✓ Found {len(found)} disk-related columns")
else:
    print("\n❌ No disk-related columns found in munkiinfo")
    print("   Trying to get a sample row to see what data is available...")
    
    # Get one row to see what's in it
    data = {f"columns[0][name]": "munkiinfo.serial_number"}
    response = session.post(query_url, data=data, headers=headers, timeout=5)
    result = response.json()
    print(f"\n   Sample data available: {result.get('recordsFiltered', 0)} records")
