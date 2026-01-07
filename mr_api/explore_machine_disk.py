#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Try machine table columns
explore_columns = [
    "machine.serial_number",
    "machine.disk_free",
    "machine.disk_used",
    "machine.disk_available",
    "machine.disk_capacity",
    "machine.disk_size",
    "machine.storage_free",
    "machine.storage_used",
    "machine.free_space",
    "machine.hdd_free",
    "machine.ssd_free",
    "machine.volume_available",
    "machine.volume_size",
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

print("Exploring machine table for disk columns:\n")

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

if not found:
    print("❌ No disk columns in machine table")
    print("\nTrying reportdata...")
    
    explore_columns2 = [
        "reportdata.disk_free",
        "reportdata.disk_used",
        "reportdata.disk_available",
    ]
    
    for col in explore_columns2:
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=5)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                print(f"✓ {col}")
        except Exception:
            pass
