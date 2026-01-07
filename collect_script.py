#!/usr/bin/env python3
"""
GitHub Actions script - collects and analyzes usage stats
"""
import os
import requests
import json
from datetime import datetime
from collections import defaultdict

# Get password from env
password = os.environ.get('MR_PASSWORD')
if not password:
    print("Error: MR_PASSWORD not set")
    exit(1)

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"

columns = [
    "machine.serial_number",
    "machine.hostname",
    "usage_stats.timestamp",
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
    "usage_stats.wbytes_per_s",
]

print("Collecting usage stats...")

# Authenticate
auth_url = f"{base_url}/auth/login"
query_url = f"{base_url}/datatables/data"
session = requests.Session()
session.verify = False

auth_request = session.post(auth_url, data={"login": login, "password": password})

if auth_request.status_code != 200:
    print(f"Authentication failed: {auth_request.status_code}")
    exit(1)

headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}
query_data = {f"columns[{i}][name]": c for i, c in enumerate(columns)}

response = session.post(query_url, data=query_data, headers=headers)
result = response.json()

# Save snapshot
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"usage_stats_{timestamp}.json"

with open(filename, 'w') as f:
    json.dump({
        "collected_at": datetime.now().isoformat(), 
        "records": result['recordsFiltered'], 
        "data": result['data']
    }, f, indent=2)

# Append to history
history_file = "usage_stats_history.jsonl"
with open(history_file, 'a') as f:
    for row in result['data']:
        record = {
            "collected_at": datetime.now().isoformat(),
            "serial_number": row[0],
            "hostname": row[1],
            "timestamp": row[2],
            "thermal_pressure": row[3],
            "package_watts": row[4],
            "gpu_busy": row[5],
            "freq_hz": row[6],
            "gpu_freq_mhz": row[7],
            "backlight": row[8],
            "keyboard_backlight": row[9],
            "ibyte_rate": row[10],
            "obyte_rate": row[11],
            "rbytes_per_s": row[12],
            "wbytes_per_s": row[13],
        }
        f.write(json.dumps(record) + '\n')

print(f"✓ Saved {result['recordsFiltered']} records to {filename}")

# Generate dashboard
print("Generating dashboard...")

def read_jsonl(filename):
    records = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records

records = read_jsonl(history_file)
machines = defaultdict(list)
for record in records:
    hostname = record.get('hostname', 'Unknown')
    machines[hostname].append(record)

machine_list = sorted(machines.keys())
total_records = len(records)
unique_machines = len(machine_list)
max_watts = max((r.get('package_watts', 0) for r in records), default=0)

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Usage Stats Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; background: #0d1117; color: #c9d1d9; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ background: #161b22; padding: 30px 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #30363d; }}
        h1 {{ color: #58a6ff; margin-bottom: 10px; }}
        .timestamp {{ color: #8b949e; font-size: 14px; }}
        
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; }}
        .stat-label {{ color: #8b949e; font-size: 12px; text-transform: uppercase; }}
        .stat-value {{ color: #58a6ff; font-size: 28px; font-weight: bold; margin-top: 10px; }}
        
        table {{ width: 100%; border-collapse: collapse; background: #161b22; margin-top: 20px; }}
        th {{ background: #0d1117; color: #58a6ff; padding: 12px; text-align: left; border-bottom: 1px solid #30363d; }}
        td {{ padding: 12px; border-bottom: 1px solid #30363d; }}
        tr:hover {{ background: #0d1117; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 MacBook Usage Statistics</h1>
            <div class="timestamp">Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Records</div>
                <div class="stat-value">{total_records:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Machines</div>
                <div class="stat-value">{unique_machines}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Max Power (W)</div>
                <div class="stat-value">{max_watts:.2f}</div>
            </div>
        </div>
        
        <h2 style="color: #58a6ff; margin: 30px 0 20px 0;">Machine Statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>Hostname</th>
                    <th>Avg Power (W)</th>
                    <th>Avg GPU %</th>
                    <th>Records</th>
                </tr>
            </thead>
            <tbody>
"""

for hostname in machine_list:
    machine_records = machines[hostname]
    watts = [r.get('package_watts', 0) for r in machine_records if isinstance(r.get('package_watts'), (int, float))]
    gpu_busy = [r.get('gpu_busy', 0) for r in machine_records if isinstance(r.get('gpu_busy'), (int, float))]
    
    avg_watts = sum(watts) / len(watts) if watts else 0
    avg_gpu = sum(gpu_busy) / len(gpu_busy) if gpu_busy else 0
    
    html += f"""                <tr>
                    <td><strong>{hostname}</strong></td>
                    <td>{avg_watts:.2f}</td>
                    <td>{avg_gpu:.1f}%</td>
                    <td>{len(machine_records)}</td>
                </tr>
"""

html += """            </tbody>
        </table>
    </div>
</body>
</html>
"""

with open('index.html', 'w') as f:
    f.write(html)

print("✓ Generated index.html")
