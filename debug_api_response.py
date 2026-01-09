#!/usr/bin/env python3
"""
Debug script to see exactly what the API returns
"""
import os
import requests
import json
import subprocess
from datetime import datetime

password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"

# Test with ONLY the columns that we know work
working_columns = [
    "machine.serial_number",
    "machine.hostname",
    "usage_stats.timestamp",
    "usage_stats.thermal_pressure",
    "usage_stats.package_watts",
    "usage_stats.gpu_busy",
]

# Now test adding each new column one by one
new_columns_to_test = [
    "usage_stats.freq_hz",
    "usage_stats.freq_ratio",
    "usage_stats.gpu_freq_mhz",
    "usage_stats.backlight",
    "usage_stats.keyboard_backlight",
    "usage_stats.ibyte_rate",
    "usage_stats.obyte_rate",
    "usage_stats.rbytes_per_s",
    "usage_stats.wbytes_per_s",
    "usage_stats.cpu_idle",
    "usage_stats.cpu_sys",
    "usage_stats.cpu_user",
    "usage_stats.load_avg",
    "disk.free",
    "disk.used",
    "disk.total",
    "machine.physical_memory",
    "usage_stats.memory",
]

auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False

auth_request = session.post(auth_url, data={"login": login, "password": password})

if auth_request.status_code != 200:
    print(f"Authentication failed: {auth_request.status_code}")
    exit(1)

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}

# First: Test working columns
print("=" * 80)
print("Testing WORKING columns only:")
print("=" * 80)
query_data = {f"columns[{i}][name]": c for i, c in enumerate(working_columns)}
response = session.post(query_url, data=query_data, headers=headers)
result = response.json()

print(f"\nResponse keys: {result.keys()}")
print(f"recordsFiltered: {result.get('recordsFiltered', 'MISSING')}")
print(f"recordsTotal: {result.get('recordsTotal', 'MISSING')}")
print(f"Number of rows: {len(result.get('data', []))}")

if result.get('data'):
    print(f"First row has {len(result['data'][0])} columns")
    print(f"First row: {result['data'][0]}")

# Now test each new column to see which ones work
print("\n" + "=" * 80)
print("Testing NEW columns one by one:")
print("=" * 80)

working_new_columns = []
broken_columns = []

for test_col in new_columns_to_test:
    test_columns = working_columns + [test_col]
    query_data = {f"columns[{i}][name]": c for i, c in enumerate(test_columns)}
    response = session.post(query_url, data=query_data, headers=headers)
    result = response.json()
    
    if "error" in result:
        print(f"❌ {test_col} - API ERROR: {result['error']}")
        broken_columns.append(test_col)
    elif not result.get('data'):
        print(f"❌ {test_col} - NO DATA RETURNED")
        broken_columns.append(test_col)
    else:
        expected_cols = len(test_columns)
        actual_cols = len(result['data'][0]) if result['data'] else 0
        if actual_cols == expected_cols:
            print(f"✅ {test_col} - OK ({actual_cols} columns)")
            working_new_columns.append(test_col)
        else:
            print(f"⚠️  {test_col} - MISMATCH: expected {expected_cols}, got {actual_cols}")
            broken_columns.append(test_col)

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Working new columns ({len(working_new_columns)}):")
for col in working_new_columns:
    print(f"  ✅ {col}")

if broken_columns:
    print(f"\nBroken columns ({len(broken_columns)}):")
    for col in broken_columns:
        print(f"  ❌ {col}")

# Now test all working columns together
print("\n" + "=" * 80)
print("Testing ALL working columns together:")
print("=" * 80)

all_working = working_columns + working_new_columns
query_data = {f"columns[{i}][name]": c for i, c in enumerate(all_working)}
response = session.post(query_url, data=query_data, headers=headers)
result = response.json()

print(f"Total columns: {len(all_working)}")
print(f"Response keys: {result.keys()}")
print(f"recordsFiltered: {result.get('recordsFiltered', 'MISSING')}")
print(f"Number of data rows: {len(result.get('data', []))}")

if result.get('data'):
    print(f"First row has {len(result['data'][0])} columns (expected {len(all_working)})")
    
print("\n✅ Use these columns in collect_script.py:")
for i, col in enumerate(all_working):
    print(f"  {i}: {col}")
