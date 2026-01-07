#!/usr/bin/env python3
import subprocess
import json

# Test freq_ratio vs freq_hz
test_script = '''#!/bin/bash
MR_BASE_URL='https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'
MR_DATA_QUERY='/datatables/data'
MR_LOGIN='localuser'
MR_PASSWORD=$(security find-generic-password -a localuser -s munkireport-api -w)

COOKIE_JAR=$(curl -s --cookie-jar - --data "login=${MR_LOGIN}&password=${MR_PASSWORD}" ${MR_BASE_URL}/auth/login)
SESSION_COOKIE=$(echo $COOKIE_JAR | sed -n 's/.*PHPSESSID[[:space:]]/PHPSESSID=/p')
CSRF_TOKEN=$(echo "$COOKIE_JAR" | sed -n 's/.*CSRF-TOKEN[[:space:]]/X-CSRF-TOKEN: /p')

QUERY="columns[0][name]=machine.hostname&columns[1][name]=usage_stats.freq_ratio&columns[2][name]=usage_stats.freq_hz&columns[3][name]=usage_stats.package_watts&columns[4][name]=usage_stats.rops_per_s&columns[5][name]=usage_stats.wops_per_s&length=8"

curl -s -H "$CSRF_TOKEN" --cookie "$SESSION_COOKIE" --data "$QUERY" ${MR_BASE_URL}${MR_DATA_QUERY}
'''

with open('/tmp/test_cpu_fields.sh', 'w') as f:
    f.write(test_script)

import os
os.chmod('/tmp/test_cpu_fields.sh', 0o755)

try:
    result = subprocess.run(['/tmp/test_cpu_fields.sh'], capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)
    
    print("🔍 Testing CPU/load alternatives:\n")
    
    if 'data' in data and len(data['data']) > 0:
        print("Hostname | freq_ratio | freq_hz | package_watts | disk_read_ops/s | disk_write_ops/s")
        print("-" * 80)
        
        for record in data['data'][:8]:
            hostname = record[0][:10] if record[0] else "Unknown"
            freq_ratio = record[1] if record[1] else "None"
            freq_hz = record[2] if record[2] else "None"  
            watts = record[3] if record[3] else "None"
            read_ops = record[4] if record[4] else "None"
            write_ops = record[5] if record[5] else "None"
            
            print(f"{hostname:10} | {str(freq_ratio):10} | {str(freq_hz):7} | {str(watts):13} | {str(read_ops):15} | {str(write_ops):16}")
            
        # Summary
        print(f"\n📊 Summary:")
        non_zero_freq_ratio = sum(1 for r in data['data'] if r[1] and str(r[1]) not in ['0', '0.0', 'None'])
        non_zero_freq_hz = sum(1 for r in data['data'] if r[2] and str(r[2]) not in ['0', '0.0', 'None'])
        non_zero_read_ops = sum(1 for r in data['data'] if r[4] and str(r[4]) not in ['0', '0.0', 'None'])
        non_zero_write_ops = sum(1 for r in data['data'] if r[5] and str(r[5]) not in ['0', '0.0', 'None'])
        
        print(f"✅ freq_ratio with data: {non_zero_freq_ratio}/{len(data['data'])}")
        print(f"❌ freq_hz with data: {non_zero_freq_hz}/{len(data['data'])}")
        print(f"✅ disk read ops/s with data: {non_zero_read_ops}/{len(data['data'])}")
        print(f"✅ disk write ops/s with data: {non_zero_write_ops}/{len(data['data'])}")
        
    else:
        print("❌ No data:", result.stdout)

except Exception as e:
    print(f"Error: {e}")
    if 'result' in locals():
        print("Output:", result.stdout[:300])

finally:
    if os.path.exists('/tmp/test_cpu_fields.sh'):
        os.remove('/tmp/test_cpu_fields.sh')