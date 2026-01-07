#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Explore performance and fan_temps tables for thermal/load data
explore_tables = {
    "performance": [
        "performance.serial_number",
        "performance.timestamp",
        "performance.cpu_load",
        "performance.load",
        "performance.load_average",
        "performance.thermal",
        "performance.thermal_pressure",
        "performance.cpu",
        "performance.memory",
        "performance.disk",
    ],
    "fan_temps": [
        "fan_temps.serial_number",
        "fan_temps.timestamp",
        "fan_temps.thermal_pressure",
        "fan_temps.cpu_temp",
        "fan_temps.gpu_temp",
        "fan_temps.fan_speed",
        "fan_temps.load",
    ],
    "usage_stats": [
        "usage_stats.serial_number",
        "usage_stats.timestamp",
        "usage_stats.thermal_pressure",
        "usage_stats.load",
        "usage_stats.cpu_load",
    ],
}

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

print("Exploring available columns for thermal/load data:\n")

for table, columns in explore_tables.items():
    print(f"## {table}:")
    found = []
    for col in columns:
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=5)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                # Show sample value
                sample = result['data'][0][0] if result['data'] else None
                print(f"  ✓ {col} (sample: {sample})")
                found.append(col)
            elif "error" not in result:
                print(f"  ? {col} (no data)")
        except Exception as e:
            pass
    
    if found:
        print(f"  → Available: {', '.join([c.split('.')[-1] for c in found])}")
    print()
