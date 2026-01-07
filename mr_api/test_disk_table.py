#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# From ReportItems we saw "disk_report" = "/usr/local/munkireport/scripts/cache/disk.plist"
# So the table might be called "disk" without the "_report"
columns_to_try = [
    "disk.serial_number",
    "disk.timestamp",
    "disk.id",
    "disk.hostname",
    "disk.drive",
    "disk.mount",
    "disk.total",
    "disk.used",
    "disk.free",
    "disk.available",
    "disk.capacity",
    "disk.percent_free",
    "disk.percent_used",
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

print("Testing 'disk' table columns:\n")
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
    print(f"✓ Found {len(found)} columns in disk table!")
else:
    print("❌ No data found in disk table either")
