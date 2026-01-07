#!/usr/bin/env python3
import requests
import subprocess
import json
from datetime import datetime

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

columns = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.timestamp",
    "reportdata.console_user",
    "machine.os_version",
    "machine.physical_memory",
    "reportdata.remote_ip",
    "diskreport.totalsize",
    "diskreport.freespace",
    "diskreport.percentage",
    "machine.computer_name",
    "machine.buildversion",
    "munkireport.manifestname",
    "mdm_status.mdm_enrolled",
    "usage_stats.thermal_pressure",
]

# authenticate and get a session cookie
auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False
auth_request = session.post(auth_url, data={"login": login, "password": password})

if auth_request.status_code != 200:
    print("Invalid url!")
    raise SystemExit

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}
def generate_query():
    q = {f"columns[{i}][name]": c for i, c in enumerate(columns)}
    return q


query_data = session.post(query_url, data=generate_query(), headers=headers)
result = query_data.json()

# Save JSON report
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"get_data_{timestamp}.json"
with open(filename, 'w') as f:
    json.dump(result, f, indent=2)

print(json.dumps(result))

