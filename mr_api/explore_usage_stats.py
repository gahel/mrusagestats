#!/usr/bin/env python3
import requests
import subprocess

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

# Explore more detailed columns in usage_stats and performance
explore_columns = {
    "usage_stats": [
        "usage_stats.serial_number",
        "usage_stats.timestamp",
        "usage_stats.thermal_pressure",
        "usage_stats.hdd",
        "usage_stats.hdd_read_speed",
        "usage_stats.hdd_write_speed",
        "usage_stats.ssd",
        "usage_stats.ssd_read_speed",
        "usage_stats.ssd_write_speed",
        "usage_stats.cpu_temp",
        "usage_stats.gpu_temp",
        "usage_stats.fan_speed",
        "usage_stats.load",
        "usage_stats.load_average",
        "usage_stats.battery_health",
        "usage_stats.battery_percent",
        "usage_stats.memory_used",
        "usage_stats.memory_available",
        "usage_stats.cpu",
        "usage_stats.memory",
        "usage_stats.disk",
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

print("Exploring detailed usage_stats columns:\n")

for table, columns in explore_columns.items():
    found = []
    for col in columns:
        data = {f"columns[0][name]": col}
        try:
            response = session.post(query_url, data=data, headers=headers, timeout=5)
            result = response.json()
            
            if "error" not in result and result.get("recordsFiltered", 0) > 0:
                found.append(col.split('.')[-1])
        except Exception:
            pass
    
    print(f"Available columns in {table}:")
    for col in found:
        print(f"  - {col}")
