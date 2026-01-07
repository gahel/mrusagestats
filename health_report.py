#!/usr/bin/env python3
import requests
import subprocess
import json
from datetime import datetime

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Get thermal pressure data
columns = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.console_user",
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
def generate_query(cols):
    return {f"columns[{i}][name]": c for i, c in enumerate(cols)}

print("=" * 90)
print("SYSTEM HEALTH REPORT - Thermal Pressure & Performance Analysis")
print("=" * 90)
print()

# Get thermal data
print("Fetching thermal pressure data...\n")
query_data = session.post(query_url, data=generate_query(columns), headers=headers)
result = query_data.json()

if "error" in result:
    print(f"Error: {result['error']}")
    raise SystemExit

data = result.get('data', [])

# Categorize by thermal status
thermal_categories = {
    'Nominal': [],
    'Warning': [],
    'Critical': [],
    'Unknown': []
}

for row in data:
    serial, hostname, machine_desc, console_user, timestamp, thermal = row
    
    category = thermal if thermal in thermal_categories else 'Unknown'
    thermal_categories[category].append({
        'serial': serial,
        'hostname': hostname,
        'machine': machine_desc,
        'user': console_user,
        'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        'thermal': thermal
    })

# Print detailed report
if thermal_categories['Critical']:
    print(f"🔴 CRITICAL THERMAL ISSUES ({len(thermal_categories['Critical'])})")
    print("-" * 90)
    for m in thermal_categories['Critical']:
        print(f"  {m['hostname']:<18} {m['serial']:<15} User: {m['user']:<20}")
        print(f"    Model: {m['machine']}")
        print(f"    Last Update: {m['timestamp']}\n")

if thermal_categories['Warning']:
    print(f"🟡 WARNING THERMAL LEVELS ({len(thermal_categories['Warning'])})")
    print("-" * 90)
    for m in thermal_categories['Warning']:
        print(f"  {m['hostname']:<18} {m['serial']:<15} User: {m['user']:<20}")
        print(f"    Model: {m['machine']}")
        print(f"    Last Update: {m['timestamp']}\n")

if thermal_categories['Nominal']:
    print(f"🟢 NOMINAL THERMAL STATUS ({len(thermal_categories['Nominal'])} machines)")

# Summary statistics
print()
print("=" * 90)
print("SUMMARY STATISTICS")
print("=" * 90)
total = len(data)
print(f"Total Machines Monitored: {total}")
print(f"  Critical: {len(thermal_categories['Critical']):3d} ({len(thermal_categories['Critical'])*100/total:5.1f}%)")
print(f"  Warning:  {len(thermal_categories['Warning']):3d} ({len(thermal_categories['Warning'])*100/total:5.1f}%)")
print(f"  Nominal:  {len(thermal_categories['Nominal']):3d} ({len(thermal_categories['Nominal'])*100/total:5.1f}%)")

# Save JSON report
report = {
    'generated': datetime.now().isoformat(),
    'total_machines': total,
    'summary': {
        'critical': len(thermal_categories['Critical']),
        'warning': len(thermal_categories['Warning']),
        'nominal': len(thermal_categories['Nominal']),
    },
    'critical_machines': thermal_categories['Critical'],
    'warning_machines': thermal_categories['Warning'],
}

with open('health_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\nDetailed report saved to: health_report.json")
