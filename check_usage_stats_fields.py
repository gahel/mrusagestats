#!/usr/bin/env python3

import subprocess
import json
import sys
import os

# Test various usage_stats fields from collect_usage_stats.py
potential_fields = [
    "usage_stats.thermal_pressure",
    "usage_stats.package_watts", 
    "usage_stats.gpu_busy",
    "usage_stats.freq_hz",
    "usage_stats.gpu_freq_mhz",
    "usage_stats.backlight",
    "usage_stats.keyboard_backlight",
    "usage_stats.ibyte_rate",
    "usage_stats.obyte_rate", 
    "usage_stats.rbytes_per_s",
    "usage_stats.wbytes_per_s"
]

# Let's also try some potential load/CPU fields
cpu_load_fields = [
    "usage_stats.loadavg1",
    "usage_stats.loadavg5", 
    "usage_stats.loadavg15",
    "usage_stats.cpu_usage",
    "usage_stats.cpu_percent",
    "usage_stats.load_average"
]

all_fields = potential_fields + cpu_load_fields

# Build temporary script to test these fields
test_script = '''#!/bin/bash
MR_BASE_URL='https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'
MR_DATA_QUERY='/datatables/data'
MR_LOGIN='localuser'
MR_PASSWORD=$(security find-generic-password -a localuser -s munkireport-api -w)

# Authenticate
COOKIE_JAR=$(curl -s --cookie-jar - --data "login=${MR_LOGIN}&password=${MR_PASSWORD}" ${MR_BASE_URL}/auth/login)
SESSION_COOKIE=$(echo $COOKIE_JAR | sed -n 's/.*PHPSESSID[[:space:]]/PHPSESSID=/p')
CSRF_TOKEN=$(echo "$COOKIE_JAR" | sed -n 's/.*CSRF-TOKEN[[:space:]]/X-CSRF-TOKEN: /p')

# Test known good fields first
QUERY="columns[0][name]=machine.hostname&''' + '&'.join([f'columns[{i+1}][name]={field}' for i, field in enumerate(potential_fields)]) + '''&length=5"

curl -s -H "$CSRF_TOKEN" --cookie "$SESSION_COOKIE" --data "$QUERY" ${MR_BASE_URL}${MR_DATA_QUERY}
'''

with open('/tmp/test_fields.sh', 'w') as f:
    f.write(test_script)

os.chmod('/tmp/test_fields.sh', 0o755)

# Run the test
try:
    result = subprocess.run(['/tmp/test_fields.sh'], capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)
    
    print("🔍 Analysis of usage_stats fields:\n")
    
    if 'data' in data and len(data['data']) > 0:
        # Check first few records
        for i, record in enumerate(data['data'][:3]):
            hostname = record[0] if len(record) > 0 else f"Machine_{i}"
            print(f"📊 {hostname}:")
            
            for j, field in enumerate(potential_fields):
                if j + 1 < len(record):
                    value = record[j + 1]
                    if value and str(value) != '0' and str(value) != '':
                        print(f"  ✅ {field}: {value}")
                    else:
                        print(f"  ❌ {field}: {value} (likely unused)")
            print()
            
        # Summary of which fields have data
        print("\n📈 Summary - Fields with actual data:")
        has_data = []
        no_data = []
        
        for j, field in enumerate(potential_fields):
            has_values = False
            for record in data['data']:
                if j + 1 < len(record) and record[j + 1] and str(record[j + 1]) not in ['0', '']:
                    has_values = True
                    break
            
            if has_values:
                has_data.append(field)
            else:
                no_data.append(field)
        
        print("\n✅ Fields with data:")
        for field in has_data:
            print(f"   - {field}")
            
        print("\n❌ Fields with no/zero data:")
        for field in no_data:
            print(f"   - {field}")
    else:
        print("❌ No data returned")
        print("Response:", result.stdout)

except Exception as e:
    print(f"❌ Error: {e}")
    if 'result' in locals():
        print("stdout:", result.stdout[:500])
        print("stderr:", result.stderr[:500])

finally:
    # Cleanup
    if os.path.exists('/tmp/test_fields.sh'):
        os.remove('/tmp/test_fields.sh')