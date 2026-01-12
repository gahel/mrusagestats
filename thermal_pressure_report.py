#!/usr/bin/env python3
import requests
import subprocess
import json
from datetime import datetime

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Columns we need for the report
columns = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "usage_stats.timestamp",
    "usage_stats.thermal_pressure",
]

# authenticate and get session
auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False
auth_request = session.post(auth_url, data={"login": login, "password": password})

if auth_request.status_code != 200:
    print("Invalid url!")
    raise SystemExit

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}

# Build query
def generate_query():
    q = {f"columns[{i}][name]": c for i, c in enumerate(columns)}
    return q

# Fetch all data
print("Fetching usage_stats data...\n")
query_data = session.post(query_url, data=generate_query(), headers=headers)
result = query_data.json()

if "error" in result:
    print(f"Error: {result['error']}")
    raise SystemExit

# Process and filter data
data = result.get('data', [])
thermal_status = {
    'Nominal': [],
    'Warning': [],
    'Critical': [],
    'Unknown': []
}

for row in data:
    serial, hostname, machine_desc, timestamp, thermal_pressure = row
    
    if thermal_pressure not in thermal_status:
        thermal_status['Unknown'].append({
            'serial': serial,
            'hostname': hostname,
            'machine': machine_desc,
            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'thermal_pressure': thermal_pressure
        })
    else:
        thermal_status[thermal_pressure].append({
            'serial': serial,
            'hostname': hostname,
            'machine': machine_desc,
            'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'thermal_pressure': thermal_pressure
        })

# Print report
print("=" * 80)
print("THERMAL STATUS - MASKINER MED ANNET ENN NOMINAL")
print("=" * 80)
print()

# Critical machines
if thermal_status['Critical']:
    print(f"🔴 CRITICAL ({len(thermal_status['Critical'])} machines):")
    print("-" * 80)
    for m in thermal_status['Critical']:
        print(f"  {m['hostname']:<20} {m['serial']:<15} {m['machine']:<30} {m['timestamp']}")
    print()
else:
    print("🔴 CRITICAL: Ingen\n")

# Warning machines
if thermal_status['Warning']:
    print(f"🟡 WARNING ({len(thermal_status['Warning'])} machines):")
    print("-" * 80)
    for m in thermal_status['Warning']:
        print(f"  {m['hostname']:<20} {m['serial']:<15} {m['machine']:<30} {m['timestamp']}")
    print()
else:
    print("🟡 WARNING: Ingen\n")

# Unknown
if thermal_status['Unknown']:
    print(f"❓ UNKNOWN ({len(thermal_status['Unknown'])} machines):")
    print("-" * 80)
    for m in thermal_status['Unknown']:
        print(f"  {m['hostname']:<20} {m['serial']:<15} {m['machine']:<30} {m['timestamp']}")
    print()

print("-" * 80)
non_nominal = len(thermal_status['Critical']) + len(thermal_status['Warning']) + len(thermal_status['Unknown'])
print(f"✓ Maskiner med NOMINAL status: {len(thermal_status['Nominal'])} av {len(data)}")
print(f"⚠ Maskiner med ANNET enn nominal: {non_nominal} av {len(data)}")
if len(data) > 0:
    print(f"  - Critical: {len(thermal_status['Critical'])} ({len(thermal_status['Critical'])*100/len(data):.1f}%)")
    print(f"  - Warning: {len(thermal_status['Warning'])} ({len(thermal_status['Warning'])*100/len(data):.1f}%)")
    if thermal_status['Unknown']:
        print(f"  - Unknown: {len(thermal_status['Unknown'])} ({len(thermal_status['Unknown'])*100/len(data):.1f}%)")

# Save detailed JSON report
report = {
    'timestamp': datetime.now().isoformat(),
    'total': len(data),
    'summary': {
        'critical': len(thermal_status['Critical']),
        'warning': len(thermal_status['Warning']),
        'nominal': len(thermal_status['Nominal']),
    },
    'critical_machines': thermal_status['Critical'],
    'warning_machines': thermal_status['Warning'],
}

with open('thermal_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\nDetailed report saved to: thermal_report.json")
