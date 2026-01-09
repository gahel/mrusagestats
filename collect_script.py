#!/usr/bin/env python3
"""
GitHub Actions script - collects and analyzes usage stats
"""
import os
import requests
import json
import time
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
    "diskreport.totalsize",
    "diskreport.freespace",
    "diskreport.percentage",
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

# Check if we got an error response
if "error" in result:
    print(f"API Error: {result['error']}")
    exit(1)

# Debug: Check what keys are in the response
if "recordsFiltered" not in result:
    print(f"Warning: 'recordsFiltered' not in response. Available keys: {result.keys()}")
    print(f"Full response: {json.dumps(result, indent=2)[:500]}")
    # Try to find the count in other possible keys
    if "recordsTotal" in result:
        records_count = result["recordsTotal"]
    else:
        records_count = len(result.get("data", []))
else:
    records_count = result['recordsFiltered']

# Save snapshot
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"usage_stats_{timestamp}.json"

with open(filename, 'w') as f:
    json.dump({
        "collected_at": datetime.now().isoformat(), 
        "records": records_count, 
        "data": result.get('data', [])
    }, f, indent=2)

# Append to history
history_file = "usage_stats_history.jsonl"
with open(history_file, 'a') as f:
    for row in result.get('data', []):
        # Calculate disk usage percentage - diskreport.percentage is already calculated
        disk_used_pct = row[22] if len(row) > 22 else 0
        
        # Parse CPU values (strings with %)
        cpu_idle_val = None
        if len(row) > 15 and row[15]:
            try:
                cpu_idle_val = float(str(row[15]).replace('%', '').strip())
            except (ValueError, AttributeError):
                cpu_idle_val = None
        
        cpu_sys_val = None
        if len(row) > 16 and row[16]:
            try:
                cpu_sys_val = float(str(row[16]).replace('%', '').strip())
            except (ValueError, AttributeError):
                cpu_sys_val = None
        
        cpu_user_val = None
        if len(row) > 17 and row[17]:
            try:
                cpu_user_val = float(str(row[17]).replace('%', '').strip())
            except (ValueError, AttributeError):
                cpu_user_val = None
        
        # Parse load_avg (comma-separated string: "short, middle, long")
        load_short = None
        load_middle = None
        load_long = None
        if len(row) > 18 and row[18]:
            try:
                load_parts = str(row[18]).split(',')
                if len(load_parts) >= 1:
                    load_short = float(load_parts[0].strip())
                if len(load_parts) >= 2:
                    load_middle = float(load_parts[1].strip())
                if len(load_parts) >= 3:
                    load_long = float(load_parts[2].strip())
            except (ValueError, AttributeError, IndexError):
                pass
        
        record = {
            "collected_at": datetime.now().isoformat(),
            "serial_number": row[0],
            "hostname": row[1],
            "timestamp": row[2],
            "thermal_pressure": row[3],
            "package_watts": row[4],
            "gpu_busy": row[5],
            "freq_hz": row[6],
            "freq_ratio": row[7],
            "gpu_freq_mhz": row[8],
            "backlight": row[9],
            "keyboard_backlight": row[10],
            "ibyte_rate": row[11],
            "obyte_rate": row[12],
            "rbytes_per_s": row[13],
            "wbytes_per_s": row[14],
            "cpu_idle": cpu_idle_val,
            "cpu_sys": cpu_sys_val,
            "cpu_user": cpu_user_val,
            "load_short": load_short,
            "load_middle": load_middle,
            "load_long": load_long,
            "disk_total": row[19] if len(row) > 19 else None,
            "disk_free": row[20] if len(row) > 20 else None,
            "disk_used_pct": disk_used_pct,
        }
        f.write(json.dumps(record) + '\n')

print(f"✓ Saved {records_count} records to {filename}")
print(f"✓ Appended to {history_file}")

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
    <title>MacBook Usage Analytics - Real-time Monitoring</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; background: #0d1117; color: #c9d1d9; line-height: 1.5; }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
        
        header {{ background: linear-gradient(135deg, #161b22 0%, #0d1117 100%); padding: 40px; border-radius: 12px; margin-bottom: 30px; border: 1px solid #30363d; }}
        h1 {{ color: #58a6ff; margin-bottom: 15px; font-size: 2.5rem; font-weight: 700; }}
        .subtitle {{ color: #8b949e; font-size: 1.1rem; margin-bottom: 20px; }}
        .timestamp {{ color: #7c3aed; font-size: 0.9rem; background: rgba(124, 58, 237, 0.1); padding: 8px 16px; border-radius: 20px; display: inline-block; }}
        
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .metric-card {{ background: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; position: relative; overflow: hidden; }}
        .metric-card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #58a6ff, #7c3aed); }}
        .metric-label {{ color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
        .metric-value {{ color: #58a6ff; font-size: 2.2rem; font-weight: bold; margin-bottom: 8px; }}
        .metric-change {{ font-size: 0.9rem; }}
        .metric-up {{ color: #f85149; }}
        .metric-down {{ color: #3fb950; }}
        
        .charts-section {{ margin-bottom: 40px; }}
        .section-title {{ color: #58a6ff; font-size: 1.8rem; margin-bottom: 25px; display: flex; align-items: center; gap: 12px; }}
        .section-title::before {{ content: '📊'; font-size: 1.5rem; }}
        
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 25px; margin-bottom: 30px; }}
        .chart-container {{ background: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; position: relative; }}
        .chart-title {{ color: #f0f6fc; font-size: 1.2rem; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
        .chart-canvas {{ position: relative; height: 300px; }}
        
        .alerts-section {{ background: #161b22; border-radius: 12px; padding: 25px; margin-bottom: 30px; border: 1px solid #30363d; }}
        .alert {{ padding: 15px; margin: 10px 0; border-radius: 8px; display: flex; align-items: center; gap: 12px; }}
        .alert-critical {{ background: rgba(248, 81, 73, 0.1); border: 1px solid #f85149; }}
        .alert-warning {{ background: rgba(255, 212, 59, 0.1); border: 1px solid #ffd43b; }}
        .alert-icon {{ font-size: 1.2rem; }}
        
        .machines-table {{ background: #161b22; border-radius: 12px; overflow: hidden; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #0d1117; color: #58a6ff; padding: 18px; text-align: left; font-weight: 600; border-bottom: 2px solid #30363d; cursor: pointer; user-select: none; position: relative; }}
        th:hover {{ background: #161b22; }}
        th.sortable:after {{ content: ' ↕️'; opacity: 0.5; }}
        th.sort-asc:after {{ content: ' ⬆️'; opacity: 1; }}
        th.sort-desc:after {{ content: ' ⬇️'; opacity: 1; }}
        td {{ padding: 15px 18px; border-bottom: 1px solid #30363d; }}
        tr:hover {{ background: #0d1117; }}
        .status-nominal {{ color: #3fb950; }}
        .status-warning {{ color: #ffd43b; }}
        .status-critical {{ color: #f85149; }}
        .high-power {{ background: rgba(248, 181, 73, 0.15); }}
        .high-gpu {{ background: rgba(124, 58, 237, 0.15); }}
        
        .hostname-cell {{ display: inline-flex; align-items: center; gap: 8px; position: relative; }}
        .hostname-link {{ cursor: pointer; color: #58a6ff; transition: color 0.2s; }}
        .hostname-link:hover {{ color: #79c0ff; text-decoration: underline; }}
        .copy-btn {{ background: #238636; color: #fff; border: none; padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 0.75rem; opacity: 0; transition: opacity 0.2s, background 0.2s; white-space: nowrap; }}
        .hostname-cell:hover .copy-btn {{ opacity: 1; }}
        .copy-btn:hover {{ background: #2da043; }}
        .copy-btn.copied {{ background: #3fb950; }}
        
        /* Machine Details Modal */
        .modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.7); animation: fadeIn 0.3s ease-in; }}
        .modal.active {{ display: flex; align-items: center; justify-content: center; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .modal-content {{ background: #0d1117; border: 1px solid #30363d; border-radius: 12px; padding: 30px; max-width: 800px; width: 90%; max-height: 90vh; overflow-y: auto; animation: slideUp 0.3s ease-out; }}
        @keyframes slideUp {{ from {{ transform: translateY(20px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 1px solid #30363d; padding-bottom: 15px; }}
        .modal-header h2 {{ margin: 0; color: #58a6ff; }}
        .modal-close {{ background: none; border: none; color: #8b949e; font-size: 1.5rem; cursor: pointer; padding: 0; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; }}
        .modal-close:hover {{ color: #f85149; }}
        .detail-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px; }}
        .detail-item {{ background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }}
        .detail-label {{ color: #8b949e; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }}
        .detail-value {{ color: #f0f6fc; font-size: 1.1rem; font-weight: 500; word-break: break-all; }}
        .detail-status {{ padding: 8px 12px; border-radius: 6px; display: inline-block; font-weight: 600; }}
        .detail-status.nominal {{ background: rgba(63, 185, 80, 0.2); color: #3fb950; }}
        .detail-status.warning {{ background: rgba(255, 212, 59, 0.2); color: #ffd43b; }}
        .detail-status.heavy {{ background: rgba(248, 113, 113, 0.2); color: #f85149; }}
        .detail-status.critical {{ background: rgba(248, 81, 73, 0.2); color: #f85149; }}
        
        .footer {{ text-align: center; padding: 40px; color: #8b949e; border-top: 1px solid #30363d; margin-top: 40px; }}
        .update-frequency {{ color: #7c3aed; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🖥️ MacBook Fleet Analytics</h1>
            <div class="subtitle">Real-time monitoring of {unique_machines} MacBooks across the organization</div>
            <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Data Points</div>
                <div class="metric-value">{total_records:,}</div>
                <div class="metric-change">📈 Growing continuously</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Active Machines</div>
                <div class="metric-value">{unique_machines}</div>
                <div class="metric-change">🟢 All monitored</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Peak Power Usage</div>
                <div class="metric-value">{max_watts:.1f}W</div>
                <div class="metric-change">⚡ Max observed</div>
            </div>"""

# Calculate additional metrics
thermal_critical = sum(1 for r in records if r.get('thermal_pressure') == 'Critical')
thermal_heavy = sum(1 for r in records if r.get('thermal_pressure') == 'Heavy')
thermal_warning = sum(1 for r in records if r.get('thermal_pressure') in ['Warning', 'High'])
high_gpu_usage = sum(1 for r in records if isinstance(r.get('gpu_busy'), (int, float)) and r.get('gpu_busy', 0) > 80)

html += f"""            <div class="metric-card">
                <div class="metric-label">Thermal Alerts</div>
                <div class="metric-value">{thermal_critical + thermal_heavy + thermal_warning}</div>
                <div class="metric-change {'metric-up' if thermal_critical + thermal_heavy > 0 else 'metric-down'}">
                    {'🔥 ' + str(thermal_critical + thermal_heavy) + ' critical/heavy' if thermal_critical + thermal_heavy > 0 else '✅ All normal'}
                </div>
            </div>
        </div>"""

# Generate time-series data for charts
# Currently: Keep ALL records for complete historical timeline
# Future: Implement 7-day retention when data becomes too large
# TODO: Uncomment line below and comment current line when needed:
# recent_records = sorted(records, key=lambda x: x.get('collected_at', ''))[-7*24*60:]  # Keep last 7 days
recent_records = sorted(records, key=lambda x: x.get('collected_at', ''))

# Group by collection time for trends
from collections import defaultdict
time_groups = defaultdict(list)
for record in recent_records:
    time_key = record.get('collected_at', '')[:16]  # Group by minute
    time_groups[time_key].append(record)

time_series_data = []
for time_key in sorted(time_groups.keys()):
    group = time_groups[time_key]
    avg_watts = sum(r.get('package_watts', 0) for r in group if isinstance(r.get('package_watts'), (int, float))) / len(group)
    avg_gpu = (sum(r.get('gpu_busy', 0) for r in group if isinstance(r.get('gpu_busy'), (int, float))) / max(len([r for r in group if isinstance(r.get('gpu_busy'), (int, float))]), 1)) * 100
    
    # Calculate average for each load period (short, middle, long)
    load_short_vals = [r.get('load_short', 0) for r in group if isinstance(r.get('load_short'), (int, float))]
    load_middle_vals = [r.get('load_middle', 0) for r in group if isinstance(r.get('load_middle'), (int, float))]
    load_long_vals = [r.get('load_long', 0) for r in group if isinstance(r.get('load_long'), (int, float))]
    
    avg_load_short = sum(load_short_vals) / len(load_short_vals) if load_short_vals else 0
    avg_load_middle = sum(load_middle_vals) / len(load_middle_vals) if load_middle_vals else 0
    avg_load_long = sum(load_long_vals) / len(load_long_vals) if load_long_vals else 0
    
    cpu_idle_vals = [r.get('cpu_idle', 0) for r in group if isinstance(r.get('cpu_idle'), (int, float))]
    avg_cpu_usage = (100 - sum(cpu_idle_vals) / len(cpu_idle_vals)) if cpu_idle_vals else 0
    thermal_issues = sum(1 for r in group if r.get('thermal_pressure') in ['Warning', 'Critical', 'High'])
    
    # Build per-machine CPU usage for trend - collect unique hostnames from this group
    machine_cpu_data = {}
    unique_hostnames = set(r.get('hostname') for r in group if r.get('hostname'))
    for hostname in unique_hostnames:
        machine_records_at_time = [r for r in group if r.get('hostname') == hostname]
        if machine_records_at_time:
            cpu_idle_for_machine = [r.get('cpu_idle', 0) for r in machine_records_at_time if isinstance(r.get('cpu_idle'), (int, float))]
            if cpu_idle_for_machine:
                machine_cpu_data[hostname] = 100 - (sum(cpu_idle_for_machine) / len(cpu_idle_for_machine))
            else:
                machine_cpu_data[hostname] = 0
        else:
            machine_cpu_data[hostname] = 0
    
    # Get top 3 machines with highest load_short for this time period (only if seen in last 2 hours)
    current_time = time.time()
    two_hours_ago = current_time - (2 * 3600)
    
    # Filter machines seen in last 2 hours
    recent_machines = []
    for r in group:
        try:
            ts = int(r.get('timestamp', 0))
            if ts > 0 and ts >= two_hours_ago:
                recent_machines.append(r)
        except (ValueError, TypeError):
            pass
    
    # Get top 3 from recently seen machines
    sorted_by_load = sorted(recent_machines, key=lambda r: r.get('load_short', 0), reverse=True)
    top3_machines = [
        {
            'hostname': sorted_by_load[0].get('hostname', 'Unknown') if len(sorted_by_load) > 0 else None,
            'load_short': sorted_by_load[0].get('load_short', 0) if len(sorted_by_load) > 0 else 0,
            'load_middle': sorted_by_load[0].get('load_middle', 0) if len(sorted_by_load) > 0 else 0,
            'load_long': sorted_by_load[0].get('load_long', 0) if len(sorted_by_load) > 0 else 0,
        },
        {
            'hostname': sorted_by_load[1].get('hostname', 'Unknown') if len(sorted_by_load) > 1 else None,
            'load_short': sorted_by_load[1].get('load_short', 0) if len(sorted_by_load) > 1 else 0,
            'load_middle': sorted_by_load[1].get('load_middle', 0) if len(sorted_by_load) > 1 else 0,
            'load_long': sorted_by_load[1].get('load_long', 0) if len(sorted_by_load) > 1 else 0,
        },
        {
            'hostname': sorted_by_load[2].get('hostname', 'Unknown') if len(sorted_by_load) > 2 else None,
            'load_short': sorted_by_load[2].get('load_short', 0) if len(sorted_by_load) > 2 else 0,
            'load_middle': sorted_by_load[2].get('load_middle', 0) if len(sorted_by_load) > 2 else 0,
            'load_long': sorted_by_load[2].get('load_long', 0) if len(sorted_by_load) > 2 else 0,
        }
    ]
    
    time_series_data.append({
        'time': time_key,
        'avg_watts': avg_watts,
        'avg_gpu': avg_gpu,
        'avg_load_short': avg_load_short,
        'avg_load_middle': avg_load_middle,
        'avg_load_long': avg_load_long,
        'avg_cpu_usage': avg_cpu_usage,
        'machine_cpu_usage': machine_cpu_data,
        'thermal_issues': thermal_issues,
        'count': len(group),
        'top3_machines': top3_machines,
        'top3_labels_1min': [
            (top3_machines[0]['hostname'] or 'Unknown') + ' (1-min)',
            (top3_machines[1]['hostname'] or 'Unknown') + ' (1-min)',
            (top3_machines[2]['hostname'] or 'Unknown') + ' (1-min)'
        ],
        'top3_labels_5min': [
            (top3_machines[0]['hostname'] or 'Unknown') + ' (5-min)',
            (top3_machines[1]['hostname'] or 'Unknown') + ' (5-min)',
            (top3_machines[2]['hostname'] or 'Unknown') + ' (5-min)'
        ],
        'top3_labels_15min': [
            (top3_machines[0]['hostname'] or 'Unknown') + ' (15-min)',
            (top3_machines[1]['hostname'] or 'Unknown') + ' (15-min)',
            (top3_machines[2]['hostname'] or 'Unknown') + ' (15-min)'
        ]
    })

html += f"""
        <div class="charts-section">
            <h2 class="section-title">Performance Trends Over Time</h2>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">🌡️ Thermal Pressure Timeline</div>
                    <div class="chart-canvas">
                        <canvas id="thermalTrendChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">⚡ Power Consumption Trends</div>
                    <div class="chart-canvas">
                        <canvas id="powerTrendChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">🎮 GPU Utilization Over Time</div>
                    <div class="chart-canvas">
                        <canvas id="gpuTrendChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <div class="chart-title">⚙️ Load Average</div>
                    <div class="chart-canvas">
                        <canvas id="cpuLoadChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <div class="chart-title">⚡ Power Consumption per Machine</div>
                    <div class="chart-canvas">
                        <canvas id="powerPerMachineChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <div class="chart-title">💻 CPU Usage per Machine</div>
                    <div class="chart-canvas">
                        <canvas id="cpuPerMachineChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="machines-table">
            <h2 class="section-title">🔝 Top 3 by Load Average (1-min)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Machine</th>
                        <th>Load (1-min)</th>
                        <th>Load (5-min)</th>
                        <th>Load (15-min)</th>
                        <th>CPU Usage (%)</th>
                        <th>Thermal</th>
                        <th>Last Seen</th>
                    </tr>
                </thead>
                <tbody>
"""

# Get top 3 machines by load average (1-min)
top3_load = sorted([(h, machines[h][-1]) for h in machines if machines[h]], 
                   key=lambda x: x[1].get('load_short', 0) if isinstance(x[1].get('load_short'), (int, float)) else 0, 
                   reverse=True)[:3]

for hostname, latest in top3_load:
    load_short = latest.get('load_short', 0) if isinstance(latest.get('load_short'), (int, float)) else 0
    load_middle = latest.get('load_middle', 0) if isinstance(latest.get('load_middle'), (int, float)) else 0
    load_long = latest.get('load_long', 0) if isinstance(latest.get('load_long'), (int, float)) else 0
    cpu_idle = latest.get('cpu_idle', 0) if isinstance(latest.get('cpu_idle'), (int, float)) else 0
    cpu_usage = 100 - cpu_idle
    thermal = latest.get('thermal_pressure', 'Unknown')
    
    # Convert Unix timestamp to readable format
    try:
        ts = int(latest.get('timestamp', 0))
        if ts > 0:
            last_seen = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        else:
            last_seen = latest.get('collected_at', 'Unknown')[:16]
    except (ValueError, TypeError):
        last_seen = latest.get('collected_at', 'Unknown')[:16]
    
    thermal_class = 'status-nominal'
    if thermal in ['Critical']:
        thermal_class = 'status-critical'
    elif thermal in ['Warning', 'High']:
        thermal_class = 'status-warning'
    
    html += f"""                <tr>
                    <td><div class="hostname-cell"><strong>{hostname}</strong><button class="copy-btn" onclick="copyToClipboard(\"{hostname}\", this)">Copy</button></div></td>
                    <td>{load_short:.2f}</td>
                    <td>{load_middle:.2f}</td>
                    <td>{load_long:.2f}</td>
                    <td>{cpu_usage:.1f}%</td>
                    <td class="{thermal_class}">{thermal}</td>
                    <td>{last_seen}</td>
                </tr>
"""

html += """                </tbody>
            </table>
        </div>
        
        <div class="charts-section">
            <h2 class="section-title">📊 Thermal & CPU Metrics</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">🌡️ Non-Nominal Thermal States</div>
                    <div class="chart-canvas">
                        <canvas id="thermalChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">📊 Average CPU Usage Over Time</div>
                    <div class="chart-canvas">
                        <canvas id="cpuChart"></canvas>
                    </div>
                </div>
            </div>
        </div>"""

# Alerts section
html += f"""
        <div class="alerts-section">
            <h2 class="section-title">🚨 System Alerts</h2>"""

if thermal_critical > 0:
    html += f"""
            <div class="alert alert-critical">
                <span class="alert-icon">🔥</span>
                <div>
                    <strong>Critical Thermal Alert:</strong> {thermal_critical} machine(s) reporting critical thermal pressure.
                    Immediate attention required to prevent hardware damage.
                </div>
            </div>"""

if thermal_heavy > 0:
    html += f"""
            <div class="alert alert-warning">
                <span class="alert-icon">🌡️</span>
                <div>
                    <strong>Heavy Thermal Pressure:</strong> {thermal_heavy} machine(s) reporting heavy thermal pressure.
                    Monitor closely and consider reducing workload or improving ventilation.
                </div>
            </div>"""

if high_gpu_usage > 10:
    html += f"""
            <div class="alert alert-warning">
                <span class="alert-icon">⚡</span>
                <div>
                    <strong>High GPU Usage:</strong> {high_gpu_usage} instances of >80% GPU utilization detected.
                    Monitor for sustained high performance workloads.
                </div>
            </div>"""

if max_watts > 15:
    html += f"""
            <div class="alert alert-warning">
                <span class="alert-icon">🔋</span>
                <div>
                    <strong>High Power Consumption:</strong> Peak power usage of {max_watts:.1f}W detected.
                    Review power-intensive applications and thermal management.
                </div>
            </div>"""

if thermal_critical == 0 and high_gpu_usage < 5:
    html += f"""
            <div class="alert" style="background: rgba(63, 185, 80, 0.1); border: 1px solid #3fb950;">
                <span class="alert-icon">✅</span>
                <div>
                    <strong>Fleet Status: Healthy</strong> All systems operating within normal parameters.
                    No immediate action required.
                </div>
            </div>"""

html += """
        </div>
        
        <div class="machines-table">
            <h2 class="section-title">💻 Machine Performance Overview</h2>
            <table id="machinesTable">
                <thead>
                    <tr>
                        <th class="sortable" data-sort="hostname">Machine</th>
                        <th class="sortable" data-sort="thermal">Thermal Status</th>
                        <th class="sortable" data-sort="power">Avg Power (W)</th>
                        <th class="sortable" data-sort="gpu">Avg GPU Usage (%)</th>
                        <th class="sortable" data-sort="cpu">CPU Usage (%)</th>
                        <th class="sortable" data-sort="load">Load Avg</th>
                        <th class="sortable" data-sort="diskused">Disk Used (%)</th>
                        <th class="sortable" data-sort="diskfree">Disk Free (GB)</th>
                        <th class="sortable" data-sort="diskio">Avg Disk IOPS</th>
                        <th class="sortable" data-sort="records">Data Points</th>
                        <th class="sortable" data-sort="lastseen">Last Seen</th>
                    </tr>
                </thead>
                <tbody id="machinesTableBody">
"""

# Create machine data for sorting
machine_data = []
for hostname in machine_list:
    machine_records = machines[hostname]
    watts = [r.get('package_watts', 0) for r in machine_records if isinstance(r.get('package_watts'), (int, float))]
    gpu_busy = [r.get('gpu_busy', 0) for r in machine_records if isinstance(r.get('gpu_busy'), (int, float))]
    # Disk IOPS calculation (operations per second)
    read_ops = [r.get('rops_per_s', 0) for r in machine_records if isinstance(r.get('rops_per_s'), (int, float))]
    write_ops = [r.get('wops_per_s', 0) for r in machine_records if isinstance(r.get('wops_per_s'), (int, float))]
    # CPU metrics
    cpu_idle = [r.get('cpu_idle', 0) for r in machine_records if isinstance(r.get('cpu_idle'), (int, float))]
    cpu_user = [r.get('cpu_user', 0) for r in machine_records if isinstance(r.get('cpu_user'), (int, float))]
    cpu_sys = [r.get('cpu_sys', 0) for r in machine_records if isinstance(r.get('cpu_sys'), (int, float))]
    load_avg = [r.get('load_avg', 0) for r in machine_records if isinstance(r.get('load_avg'), (int, float))]
    # Disk metrics - diskreport.percentage is already calculated
    disk_used_pct = [r.get('disk_used_pct', 0) for r in machine_records if r.get('disk_used_pct') is not None]
    disk_free = [r.get('disk_free', 0) for r in machine_records if r.get('disk_free') is not None]
    
    avg_watts = sum(watts) / len(watts) if watts else 0
    avg_gpu = sum(gpu_busy) / len(gpu_busy) if gpu_busy else 0
    avg_diskio = (sum(read_ops) + sum(write_ops)) / max(len(read_ops), len(write_ops)) if read_ops or write_ops else 0
    avg_cpu_idle = sum(cpu_idle) / len(cpu_idle) if cpu_idle else 0
    avg_cpu_user = sum(cpu_user) / len(cpu_user) if cpu_user else 0
    avg_cpu_sys = sum(cpu_sys) / len(cpu_sys) if cpu_sys else 0
    avg_load = sum(load_avg) / len(load_avg) if load_avg else 0
    cpu_usage = 100 - avg_cpu_idle  # Total CPU usage is inverse of idle
    avg_disk_used_pct = sum(disk_used_pct) / len(disk_used_pct) if disk_used_pct else 0
    avg_disk_free = sum(disk_free) / len(disk_free) if disk_free else 0
    
    # Get most common thermal status
    thermal_states = [r.get('thermal_pressure', 'Unknown') for r in machine_records]
    thermal_status = max(set(thermal_states), key=thermal_states.count)
    
    status_class = 'status-nominal'
    thermal_priority = 0
    if thermal_status in ['Critical']:
        status_class = 'status-critical'
        thermal_priority = 3
    elif thermal_status in ['Warning', 'High']:
        status_class = 'status-warning'
        thermal_priority = 2
    else:
        thermal_priority = 1
    
    # Convert disk_free from bytes to GB
    disk_free_gb = avg_disk_free / (1024 ** 3) if avg_disk_free else 0
    
    # Parse last_seen timestamp to show actual date/time from API (reportdata.timestamp)
    last_record = machine_records[-1] if machine_records else None
    last_seen = 'Unknown'
    
    if last_record:
        try:
            # Try to get Unix timestamp from API (reportdata.timestamp)
            ts = int(last_record.get('timestamp', 0))
            if ts > 0:
                from datetime import datetime
                last_seen = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
            else:
                # Fallback to collected_at if timestamp is missing/invalid
                last_seen_raw = last_record.get('collected_at', 'Unknown')
                if last_seen_raw != 'Unknown':
                    from datetime import datetime
                    dt = datetime.fromisoformat(last_seen_raw)
                    last_seen = dt.strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError, AttributeError):
            last_seen = 'Unknown'
    
    machine_data.append({
        'hostname': hostname,
        'thermal_status': thermal_status,
        'disk_used_pct': avg_disk_used_pct,
        'disk_free': disk_free_gb,
        'thermal_priority': thermal_priority,
        'status_class': status_class,
        'avg_watts': avg_watts,
        'avg_gpu': avg_gpu,
        'avg_diskio': avg_diskio,
        'avg_load': avg_load,
        'cpu_usage': cpu_usage,
        'record_count': len(machine_records),
        'last_seen': last_seen
    })

# Sort by: 1) Thermal priority (critical first), 2) Power consumption (highest first), 3) GPU usage
machine_data.sort(key=lambda x: (-x['thermal_priority'], -x['avg_watts'], -x['avg_gpu']))

# Build machine details data for modal
import json as json_module
machine_details = {}
for hostname in machine_list:
    machine_records = machines[hostname]
    last_record = machine_records[-1] if machine_records else None
    
    if not last_record:
        continue
    
    # Calculate averages
    cpu_idle_list = [r.get('cpu_idle', 0) for r in machine_records if isinstance(r.get('cpu_idle'), (int, float))]
    cpu_user_list = [r.get('cpu_user', 0) for r in machine_records if isinstance(r.get('cpu_user'), (int, float))]
    cpu_sys_list = [r.get('cpu_sys', 0) for r in machine_records if isinstance(r.get('cpu_sys'), (int, float))]
    load_avg_list = [r.get('load_avg', 0) for r in machine_records if isinstance(r.get('load_avg'), (int, float))]
    watts_list = [r.get('package_watts', 0) for r in machine_records if isinstance(r.get('package_watts'), (int, float))]
    gpu_list = [r.get('gpu_busy', 0) for r in machine_records if isinstance(r.get('gpu_busy'), (int, float))]
    
    machine_details[hostname] = {
        'hostname': hostname,
        'model': last_record.get('model', 'N/A'),
        'memory': last_record.get('memory', 0),
        'thermal_pressure': last_record.get('thermal_pressure', 'Unknown'),
        'cpu_idle': sum(cpu_idle_list) / len(cpu_idle_list) if cpu_idle_list else 0,
        'cpu_user': sum(cpu_user_list) / len(cpu_user_list) if cpu_user_list else 0,
        'cpu_sys': sum(cpu_sys_list) / len(cpu_sys_list) if cpu_sys_list else 0,
        'load_avg': sum(load_avg_list) / len(load_avg_list) if load_avg_list else 0,
        'package_watts': sum(watts_list) / len(watts_list) if watts_list else 0,
        'gpu_busy': sum(gpu_list) / len(gpu_list) if gpu_list else 0,
        'disk_total': last_record.get('disk_total', 0),
        'disk_free': last_record.get('disk_free', 0),
    }

machine_details_json = json_module.dumps(machine_details)

for machine in machine_data:
    row_class = ''
    if machine['avg_watts'] > 8:
        row_class += ' high-power'
    if machine['avg_gpu'] > 50:
        row_class += ' high-gpu'
    
    html += f"""                <tr{' class="' + row_class.strip() + '"' if row_class else ''}>
                    <td><div class="hostname-cell"><span class="hostname-link" onclick="showMachineDetails('{machine['hostname']}')">{machine['hostname']}</span><button class="copy-btn" onclick="copyToClipboard(\"{machine['hostname']}\", this)">Copy</button></div></td>
                    <td class="{machine['status_class']}">{machine['thermal_status']}</td>
                    <td>{machine['avg_watts']:.2f}</td>
                    <td>{machine['avg_gpu']:.1f}%</td>
                    <td>{machine['cpu_usage']:.1f}%</td>
                    <td>{machine['avg_load']:.2f}</td>
                    <td>{machine['disk_used_pct']:.1f}%</td>
                    <td>{machine['disk_free']:.1f}</td>
                    <td>{int(machine['avg_diskio'])}</td>
                    <td>{machine['record_count']}</td>
                    <td>{machine['last_seen']}</td>
                </tr>
"""

# Add top-10 sections
load_records = [(h, machines[h][-1]) for h in machines if machines[h]]
load_records.sort(key=lambda x: x[1].get('load_short', 0) if isinstance(x[1].get('load_short'), (int, float)) else 0, reverse=True)

disk_records = [(h, machines[h][-1]) for h in machines if machines[h]]
disk_records.sort(key=lambda x: x[1].get('disk_free', float('inf')) if isinstance(x[1].get('disk_free'), (int, float)) else float('inf'))

html += """    </div>
    
    <div class="machines-table">
        <h2 class="section-title">🔥 Top 10 - Highest Load Average (1-min)</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Machine</th>
                    <th>Load (1-min)</th>
                    <th>Load (5-min)</th>
                    <th>Load (15-min)</th>
                    <th>CPU Usage (%)</th>
                    <th>Last Seen</th>
                </tr>
            </thead>
            <tbody>
"""

for rank, (hostname, latest) in enumerate(load_records[:10], 1):
    load_short = latest.get('load_short', 0) if isinstance(latest.get('load_short'), (int, float)) else 0
    load_middle = latest.get('load_middle', 0) if isinstance(latest.get('load_middle'), (int, float)) else 0
    load_long = latest.get('load_long', 0) if isinstance(latest.get('load_long'), (int, float)) else 0
    cpu_idle = latest.get('cpu_idle', 0) if isinstance(latest.get('cpu_idle'), (int, float)) else 0
    cpu_usage = 100 - cpu_idle
    last_seen = latest.get('collected_at', 'Unknown')[:16]
    
    html += f"""                <tr>
                    <td>{rank}</td>
                    <td><div class="hostname-cell"><strong>{hostname}</strong><button class="copy-btn" onclick="copyToClipboard('{hostname}', this)">Copy</button></div></td>
                    <td>{load_short:.2f}</td>
                    <td>{load_middle:.2f}</td>
                    <td>{load_long:.2f}</td>
                    <td>{cpu_usage:.1f}%</td>
                    <td>{last_seen}</td>
                </tr>
"""

html += """            </tbody>
        </table>
    </div>
    
    <div class="machines-table">
        <h2 class="section-title">💾 Top 10 - Least Disk Space Available</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Machine</th>
                    <th>Disk Used (%)</th>
                    <th>Disk Free (GB)</th>
                    <th>Disk Total (GB)</th>
                    <th>Thermal Status</th>
                    <th>Last Seen</th>
                </tr>
            </thead>
            <tbody>
"""

for rank, (hostname, latest) in enumerate(disk_records[:10], 1):
    disk_free = latest.get('disk_free', 0) if isinstance(latest.get('disk_free'), (int, float)) else 0
    disk_total = latest.get('disk_total', 0) if isinstance(latest.get('disk_total'), (int, float)) else 0
    disk_used_pct = latest.get('disk_used_pct', 0) if isinstance(latest.get('disk_used_pct'), (int, float)) else 0
    thermal = latest.get('thermal_pressure', 'Unknown')
    last_seen = latest.get('collected_at', 'Unknown')[:16]
    
    disk_free_gb = disk_free / (1024 ** 3)
    disk_total_gb = disk_total / (1024 ** 3)
    
    thermal_class = 'status-nominal'
    if thermal in ['Critical']:
        thermal_class = 'status-critical'
    elif thermal in ['Warning', 'High']:
        thermal_class = 'status-warning'
    
    html += f"""                <tr>
                    <td>{rank}</td>
                    <td><div class="hostname-cell"><strong>{hostname}</strong><button class="copy-btn" onclick="copyToClipboard(\"{hostname}\", this)">Copy</button></div></td>
                    <td>{disk_used_pct:.1f}%</td>
                    <td>{disk_free_gb:.1f}</td>
                    <td>{disk_total_gb:.1f}</td>
                    <td class="{thermal_class}">{thermal}</td>
                    <td>{last_seen}</td>
                </tr>
"""

html += """            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>🔄 Data collected every <span class="update-frequency">hour</span> via GitHub Actions</p>
        <p>📈 Historical trends available • 🚨 Real-time monitoring • ⚡ Performance analytics</p>
    </div>
</div>

<script>
// Chart.js configuration
Chart.defaults.color = '#8b949e';

Chart.defaults.borderColor = '#30363d';
Chart.defaults.backgroundColor = 'rgba(88, 166, 255, 0.1)';

// Table sorting functionality
let currentSort = { column: 'thermal', direction: 'desc' };

function sortTable(column) {
    const table = document.getElementById('machinesTable');
    const tbody = document.getElementById('machinesTableBody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle direction if clicking same column
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.direction = 'desc';
        currentSort.column = column;
    }
    
    // Update header indicators
    document.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    document.querySelector(`th[data-sort="${column}"]`).classList.add(
        currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc'
    );
    
    rows.sort((a, b) => {
        const aVal = getCellValue(a, column);
        const bVal = getCellValue(b, column);
        
        if (column === 'power' || column === 'gpu' || column === 'cpu' || column === 'load' || column === 'diskused' || column === 'diskfree' || column === 'diskio' || column === 'records') {
            return currentSort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        } else if (column === 'thermal') {
            const thermalOrder = {'Critical': 3, 'Warning': 2, 'High': 2, 'Nominal': 1, 'Unknown': 0};
            return currentSort.direction === 'asc' ? 
                (thermalOrder[aVal] || 0) - (thermalOrder[bVal] || 0) :
                (thermalOrder[bVal] || 0) - (thermalOrder[aVal] || 0);
        } else {
            return currentSort.direction === 'asc' ? 
                aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
    });
    
    // Rebuild table
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

function getCellValue(row, column) {
    const columnMap = {
        'hostname': 0, 'thermal': 1, 'power': 2, 
        'gpu': 3, 'cpu': 4, 'load': 5, 'diskused': 6, 'diskfree': 7, 'diskio': 8, 'records': 9, 'lastseen': 10
    };
    const cell = row.cells[columnMap[column]];
    
    if (column === 'power' || column === 'gpu' || column === 'cpu' || column === 'load' || column === 'diskused' || column === 'diskfree' || column === 'diskio') {
        return parseFloat(cell.textContent);
    } else if (column === 'records') {
        return parseInt(cell.textContent);
    }
    return cell.textContent.trim();
}

// Add click listeners to headers
document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => sortTable(th.dataset.sort));
});

// Time series data
const timeSeriesData = """ + json.dumps(time_series_data) + """;

// Thermal trend chart
const thermalCtx = document.getElementById('thermalTrendChart').getContext('2d');
new Chart(thermalCtx, {
    type: 'line',
    data: {
        labels: timeSeriesData.map(d => d.time),
        datasets: [{
            label: 'Thermal Issues',
            data: timeSeriesData.map(d => d.thermal_issues),
            borderColor: '#f85149',
            backgroundColor: 'rgba(248, 81, 73, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                beginAtZero: true,
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 10
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { labels: { color: '#8b949e' } }
        }
    }
});

// Power trend chart
const powerCtx = document.getElementById('powerTrendChart').getContext('2d');
new Chart(powerCtx, {
    type: 'line',
    data: {
        labels: timeSeriesData.map(d => d.time),
        datasets: [{
            label: 'Average Power (W)',
            data: timeSeriesData.map(d => d.avg_watts),
            borderColor: '#58a6ff',
            backgroundColor: 'rgba(88, 166, 255, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                beginAtZero: true,
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 10
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { labels: { color: '#8b949e' } }
        }
    }
});

// GPU trend chart
const gpuCtx = document.getElementById('gpuTrendChart').getContext('2d');
new Chart(gpuCtx, {
    type: 'line',
    data: {
        labels: timeSeriesData.map(d => d.time),
        datasets: [{
            label: 'Average GPU Usage (%)',
            data: timeSeriesData.map(d => d.avg_gpu),
            borderColor: '#7c3aed',
            backgroundColor: 'rgba(124, 58, 237, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                beginAtZero: true,
                max: 100,
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 10
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { labels: { color: '#8b949e' } }
        }
    }
});

// Power consumption per machine - all machines with random colors
const powerPerMachineCtx = document.getElementById('powerPerMachineChart').getContext('2d');
const machines = """ + json.dumps(machines) + """;

// Helper function to generate random color
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Prepare datasets for all machines
const powerDatasets = [];
const machineNames = Object.keys(machines).sort();
const maxDataPoints = Math.max(...machineNames.map(m => machines[m].length || 0));

// Create a consistent color map for each machine
const colorMap = {};
for (let hostname of machineNames) {
    colorMap[hostname] = getRandomColor();
}

for (let hostname of machineNames) {
    const machineRecords = machines[hostname] || [];
    const powerValues = machineRecords.map(r => r.package_watts || 0);
    
    const color = colorMap[hostname];
    powerDatasets.push({
        label: hostname,
        data: powerValues,
        borderColor: color,
        backgroundColor: color.replace(')', ', 0.1)').replace('#', 'rgba('),
        tension: 0.2,
        fill: false,
        borderWidth: 1,
        pointRadius: 0,
        pointHoverRadius: 4
    });
}

// Generate time labels (reuse from power trend if available, or create generic ones)
const timeLabels = machineNames.length > 0 && machines[machineNames[0]] 
    ? machines[machineNames[0]].map((r, idx) => r.collected_at ? r.collected_at.substring(11, 16) : `${idx}`)
    : Array.from({length: maxDataPoints}, (_, i) => i.toString());

new Chart(powerPerMachineCtx, {
    type: 'line',
    data: {
        labels: timeLabels,
        datasets: powerDatasets
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                beginAtZero: true,
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 12
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { 
                display: false
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                titleColor: '#58a6ff',
                bodyColor: '#c9d1d9',
                borderColor: '#30363d',
                borderWidth: 1,
                callbacks: {
                    title: function(context) {
                        return context[0].dataset.label || context[0].label;
                    },
                    label: function(context) {
                        return 'Power: ' + context.parsed.y.toFixed(1) + 'W';
                    }
                }
            }
        }
    }
});

// CPU usage per machine - all machines over time with trend
const cpuPerMachineCtx = document.getElementById('cpuPerMachineChart').getContext('2d');

const cpuTrendDatasets = [];

for (let hostname of machineNames) {
    const color = colorMap[hostname];
    cpuTrendDatasets.push({
        label: hostname,
        data: timeSeriesData.map(d => d.machine_cpu_usage && d.machine_cpu_usage[hostname] !== undefined ? d.machine_cpu_usage[hostname] : 0),
        borderColor: color,
        backgroundColor: color.replace(')', ', 0.05)').replace('#', 'rgba('),
        tension: 0.3,
        fill: false,
        borderWidth: 1.5,
        pointRadius: 0,
        pointHoverRadius: 4
    });
}

new Chart(cpuPerMachineCtx, {
    type: 'line',
    data: {
        labels: timeSeriesData.map(d => d.time),
        datasets: cpuTrendDatasets
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                beginAtZero: true,
                max: 100,
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 12
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { 
                display: false
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                titleColor: '#58a6ff',
                bodyColor: '#c9d1d9',
                borderColor: '#30363d',
                borderWidth: 1,
                callbacks: {
                    title: function(context) {
                        return context[0].dataset.label || context[0].label;
                    },
                    label: function(context) {
                        return 'CPU: ' + context.parsed.y.toFixed(1) + '%';
                    }
                }
            }
        }
    }
});

// CPU Load chart with fleet average + top 3 machines
const cpuLoadCtx = document.getElementById('cpuLoadChart').getContext('2d');

// Helper to safely get hostname from top3 data
function getTopMachineLabel(index, interval) {
    return (data) => {
        const machine = data.top3_machines && data.top3_machines[index];
        const hostname = machine && machine.hostname ? machine.hostname : `Top${index + 1}`;
        return hostname + ` (${interval})`;
    };
}

new Chart(cpuLoadCtx, {
    type: 'line',
    data: {
        labels: timeSeriesData.map(d => d.time),
        datasets: [
            // Fleet averages (solid lines)
            {
                label: 'avg 1 min',
                data: timeSeriesData.map(d => d.avg_load_short),
                borderColor: '#3fb950',
                backgroundColor: 'rgba(63, 185, 80, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 1.5,
                pointRadius: 0,
                yAxisID: 'y'
            },
            {
                label: 'avg 5 min',
                data: timeSeriesData.map(d => d.avg_load_middle),
                borderColor: '#d29922',
                backgroundColor: 'rgba(210, 153, 34, 0.05)',
                tension: 0.4,
                fill: false,
                borderWidth: 1.5,
                pointRadius: 0,
                yAxisID: 'y'
            },
            {
                label: 'avg 15 min',
                data: timeSeriesData.map(d => d.avg_load_long),
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.05)',
                tension: 0.4,
                fill: false,
                borderWidth: 1.5,
                pointRadius: 0,
                yAxisID: 'y'
            },
            // Top 3 machines - 1-min load (dashed, thin)
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_1min[0] : 'Top1 (1-min)',
                data: timeSeriesData.map(d => d.top3_machines[0].load_short),
                borderColor: 'rgba(63, 185, 80, 0.5)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_1min[1] : 'Top2 (1-min)',
                data: timeSeriesData.map(d => d.top3_machines[1].load_short),
                borderColor: 'rgba(63, 185, 80, 0.35)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_1min[2] : 'Top3 (1-min)',
                data: timeSeriesData.map(d => d.top3_machines[2].load_short),
                borderColor: 'rgba(63, 185, 80, 0.2)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            // Top 3 machines - 5-min load (dashed, thin)
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_5min[0] : 'Top1 (5-min)',
                data: timeSeriesData.map(d => d.top3_machines[0].load_middle),
                borderColor: 'rgba(210, 153, 34, 0.5)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_5min[1] : 'Top2 (5-min)',
                data: timeSeriesData.map(d => d.top3_machines[1].load_middle),
                borderColor: 'rgba(210, 153, 34, 0.35)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_5min[2] : 'Top3 (5-min)',
                data: timeSeriesData.map(d => d.top3_machines[2].load_middle),
                borderColor: 'rgba(210, 153, 34, 0.2)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            // Top 3 machines - 15-min load (dashed, thin)
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_15min[0] : 'Top1 (15-min)',
                data: timeSeriesData.map(d => d.top3_machines[0].load_long),
                borderColor: 'rgba(88, 166, 255, 0.5)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_15min[1] : 'Top2 (15-min)',
                data: timeSeriesData.map(d => d.top3_machines[1].load_long),
                borderColor: 'rgba(88, 166, 255, 0.35)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            },
            {
                label: timeSeriesData.length > 0 ? timeSeriesData[0].top3_labels_15min[2] : 'Top3 (15-min)',
                data: timeSeriesData.map(d => d.top3_machines[2].load_long),
                borderColor: 'rgba(88, 166, 255, 0.2)',
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                borderWidth: 0.8,
                yAxisID: 'y'
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                type: 'linear',
                display: true,
                position: 'left',
                beginAtZero: true,
                title: { display: true, text: 'Load Average' },
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 10
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { 
                labels: { color: '#8b949e' },
                display: true,
                position: 'left',
                maxWidth: 200,
                maxHeight: 600,
                font: { size: 10 }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                titleColor: '#58a6ff',
                bodyColor: '#c9d1d9',
                borderColor: '#30363d',
                borderWidth: 1,
                callbacks: {
                    title: function(context) {
                        const label = context[0].dataset.label || '';
                        // Extract hostname - label format: "MBP-00106 (1-min)" or "Top1 (1-min)"
                        const match = label.match(/^([A-Z0-9\-]+)\s*\(/);
                        if (match && match[1]) {
                            return 'Machine: ' + match[1];
                        }
                        return label;
                    },
                    label: function(context) {
                        const label = context.dataset.label || '';
                        const interval = label.match(/\(([^)]+)\)/);
                        const intervalText = interval ? interval[1] : 'load';
                        return intervalText + ': ' + context.parsed.y.toFixed(2);
                    }
                }
            }
        }
    }
});

// Thermal status chart (non-nominal only)
const thermalStatusCtx = document.getElementById('thermalChart').getContext('2d');
new Chart(thermalStatusCtx, {
    type: 'doughnut',
    data: {
        labels: ['Warning / High', 'Critical'],
        datasets: [{
            data: [0, 0],
            backgroundColor: ['#ffd43b', '#f85149'],
            borderWidth: 2,
            borderColor: '#30363d'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { 
                labels: { color: '#8b949e' },
                position: 'bottom'
            }
        }
    }
});

// CPU usage chart
const cpuMetricsCtx = document.getElementById('cpuChart').getContext('2d');
new Chart(cpuMetricsCtx, {
    type: 'line',
    data: {
        labels: timeSeriesData.map(d => d.time),
        datasets: [{
            label: 'Average CPU Usage (%)',
            data: timeSeriesData.map(d => d.avg_cpu_usage),
            borderColor: '#58a6ff',
            backgroundColor: 'rgba(88, 166, 255, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { 
                beginAtZero: true,
                max: 100,
                ticks: { color: '#8b949e' },
                grid: { color: '#30363d' }
            },
            x: { 
                ticks: { 
                    color: '#8b949e',
                    maxTicksLimit: 10
                },
                grid: { color: '#30363d' }
            }
        },
        plugins: {
            legend: { labels: { color: '#8b949e' } }
        }
    }
});

// Copy to clipboard function
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        button.classList.add('copied');
        button.textContent = 'Copied!';
        setTimeout(() => {
            button.classList.remove('copied');
            button.textContent = 'Copy';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy: ' + text);
    });
}

// Machine Details Modal
const machineModal = document.createElement('div');
machineModal.className = 'modal';
machineModal.innerHTML = `
    <div class="modal-content">
        <div class="modal-header">
            <h2 id="modalTitle">Machine Details</h2>
            <button class="modal-close" onclick="closeMachineModal()">&times;</button>
        </div>
        <div id="modalBody"></div>
    </div>
`;
document.body.appendChild(machineModal);

const machineData = """ + machine_details_json + """;

function showMachineDetails(hostname) {
    const data = machineData[hostname];
    if (!data) return;
    
    const statusClass = data.thermal_pressure === 'Critical' ? 'critical' 
                      : data.thermal_pressure === 'Heavy' ? 'heavy'
                      : data.thermal_pressure === 'Warning' || data.thermal_pressure === 'High' ? 'warning'
                      : 'nominal';
    
    const diskFreeGb = (data.disk_free / (1024 ** 3)).toFixed(2);
    const diskUsedGb = (data.disk_total / (1024 ** 3) - diskFreeGb).toFixed(2);
    const diskTotal = (data.disk_total / (1024 ** 3)).toFixed(2);
    
    document.getElementById('modalTitle').textContent = 'Machine Details: ' + hostname;
    document.getElementById('modalBody').innerHTML = `
        <div class="detail-grid">
            <div class="detail-item">
                <div class="detail-label">Hostname</div>
                <div class="detail-value">${data.hostname}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Model</div>
                <div class="detail-value">${data.model || 'N/A'}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Memory</div>
                <div class="detail-value">${data.memory || 'N/A'} GB</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Thermal Pressure</div>
                <div class="detail-value"><span class="detail-status ${statusClass}">${data.thermal_pressure}</span></div>
            </div>
            <div class="detail-item">
                <div class="detail-label">CPU Idle</div>
                <div class="detail-value">${data.cpu_idle?.toFixed(2) || 'N/A'}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">CPU User</div>
                <div class="detail-value">${data.cpu_user?.toFixed(2) || 'N/A'}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">CPU System</div>
                <div class="detail-value">${data.cpu_sys?.toFixed(2) || 'N/A'}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Load Average</div>
                <div class="detail-value">${data.load_avg?.toFixed(2) || 'N/A'}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Avg Power</div>
                <div class="detail-value">${data.package_watts?.toFixed(2) || 'N/A'} W</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Avg GPU Usage</div>
                <div class="detail-value">${(data.gpu_busy * 100)?.toFixed(1) || 'N/A'}%</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Disk Used</div>
                <div class="detail-value">${diskUsedGb} GB / ${diskTotal} GB</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Disk Free</div>
                <div class="detail-value">${diskFreeGb} GB</div>
            </div>
        </div>
    `;
    machineModal.classList.add('active');
}

function closeMachineModal() {
    machineModal.classList.remove('active');
}

machineModal.addEventListener('click', (e) => {
    if (e.target === machineModal) closeMachineModal();
});

// Auto-refresh every 10 minutes
setTimeout(() => {
    window.location.reload();
}, 600000);
</script>
</body>
</html>
"""

with open('index.html', 'w') as f:
    f.write(html)

print("✓ Generated index.html")
