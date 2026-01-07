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

col = "usage_stats.username"
data = {f"columns[0][name]": col}
try:
    response = session.post(query_url, data=data, headers=headers, timeout=5)
    result = response.json()
    
    if "error" not in result and result.get("recordsFiltered", 0) > 0:
        records = result.get("recordsFiltered", 0)
        sample = result['data'][0][0] if result['data'] else None
        print(f"✓ {col:<40} {records:>6} records (sample: {sample})")
    elif "error" not in result:
        print(f"? {col:<40} 0 records")
    else:
        print(f"❌ {col:<40} Error: {result['error'][:60]}")
except Exception as e:
    print(f"❌ {col:<40} Exception: {str(e)[:60]}")
