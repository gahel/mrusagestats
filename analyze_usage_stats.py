#!/usr/bin/env python3
"""
Analyze usage_stats history and generate interactive HTML dashboard
"""
import json
import os
from datetime import datetime
from collections import defaultdict

def read_jsonl(filename):
    """Read JSONL file and return list of records"""
    records = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    return records

def generate_dashboard(records):
    """Generate interactive HTML dashboard with charts"""
    
    # Aggregate data by machine
    machines = defaultdict(list)
    for record in records:
        hostname = record.get('hostname', 'Unknown')
        machines[hostname].append(record)
    
    # Generate chart data
    machine_list = sorted(machines.keys())
    
    # Stats
    total_records = len(records)
    unique_machines = len(machine_list)
    
    # Find extremes
    max_thermal = max((r.get('thermal_pressure', 'Nominal') for r in records if isinstance(r.get('thermal_pressure'), (int, float))), default=0)
    max_watts = max((r.get('package_watts', 0) for r in records), default=0)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Usage Stats Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ background: #161b22; padding: 30px 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #30363d; }}
        h1 {{ color: #58a6ff; margin-bottom: 10px; }}
        .timestamp {{ color: #8b949e; font-size: 14px; }}
        
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; }}
        .stat-label {{ color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }}
        .stat-value {{ color: #58a6ff; font-size: 28px; font-weight: bold; }}
        
        .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart-container {{ background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; position: relative; height: 300px; }}
        .chart-title {{ color: #58a6ff; font-size: 14px; font-weight: 600; margin-bottom: 15px; }}
        
        table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; }}
        th {{ background: #0d1117; color: #58a6ff; padding: 12px; text-align: left; border-bottom: 1px solid #30363d; }}
        td {{ padding: 12px; border-bottom: 1px solid #30363d; }}
        tr:hover {{ background: #0d1117; }}
        
        .nominal {{ color: #3fb950; }}
        .warning {{ color: #f0883e; }}
        .critical {{ color: #f85149; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 MacBook Usage Statistics Dashboard</h1>
            <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Records</div>
                <div class="stat-value">{total_records:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Unique Machines</div>
                <div class="stat-value">{unique_machines}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Max Thermal</div>
                <div class="stat-value">{max_thermal}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Max Power (W)</div>
                <div class="stat-value">{max_watts:.2f}</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">Thermal Pressure Distribution</div>
                <canvas id="thermalChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Power Consumption Trend</div>
                <canvas id="wattChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">GPU Busy Distribution</div>
                <canvas id="gpuChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Records Over Time</div>
                <canvas id="timeChart"></canvas>
            </div>
        </div>
        
        <h2 style="color: #58a6ff; margin: 30px 0 20px 0;">Machine Overview</h2>
        <table>
            <thead>
                <tr>
                    <th>Hostname</th>
                    <th>Avg Power (W)</th>
                    <th>Avg GPU %</th>
                    <th>Avg CPU Freq (GHz)</th>
                    <th>Records</th>
                    <th>Last Seen</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Machine stats
    for hostname in machine_list:
        machine_records = machines[hostname]
        
        watts = [r.get('package_watts', 0) for r in machine_records if isinstance(r.get('package_watts'), (int, float))]
        gpu_busy = [r.get('gpu_busy', 0) for r in machine_records if isinstance(r.get('gpu_busy'), (int, float))]
        cpu_freq = [r.get('freq_hz', 0) / 1e9 for r in machine_records if isinstance(r.get('freq_hz'), (int, float))]
        
        avg_watts = sum(watts) / len(watts) if watts else 0
        avg_gpu = sum(gpu_busy) / len(gpu_busy) if gpu_busy else 0
        avg_cpu_freq = sum(cpu_freq) / len(cpu_freq) if cpu_freq else 0
        
        last_record = machine_records[-1].get('collected_at', 'Unknown')
        
        html += f"""                <tr>
                    <td><strong>{hostname}</strong></td>
                    <td>{avg_watts:.2f}</td>
                    <td>{avg_gpu:.1f}%</td>
                    <td>{avg_cpu_freq:.2f}</td>
                    <td>{len(machine_records)}</td>
                    <td>{last_record}</td>
                </tr>
"""
    
    html += """            </tbody>
        </table>
    </div>
    
    <script>
        // Thermal distribution
        const thermalChart = new Chart(document.getElementById('thermalChart'), {
            type: 'doughnut',
            data: {
                labels: ['Nominal', 'Warning', 'Critical'],
                datasets: [{
                    data: [""" + str(sum(1 for r in records if r.get('thermal_pressure') == 'Nominal')) + """, """ + str(sum(1 for r in records if r.get('thermal_pressure') == 'Warning')) + """, """ + str(sum(1 for r in records if r.get('thermal_pressure') == 'Critical')) + """],
                    backgroundColor: ['#3fb950', '#f0883e', '#f85149']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8b949e' } } }
            }
        });
        
        // Watts trend (last 30 records)
        const wattRecords = """ + json.dumps([r.get('package_watts', 0) for r in records[-30:]]) + """;
        const wattChart = new Chart(document.getElementById('wattChart'), {
            type: 'line',
            data: {
                labels: Array.from({length: wattRecords.length}, (_, i) => i),
                datasets: [{
                    label: 'Power (W)',
                    data: wattRecords,
                    borderColor: '#58a6ff',
                    backgroundColor: 'rgba(88, 166, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8b949e' } } },
                scales: {
                    y: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } },
                    x: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } }
                }
            }
        });
        
        // GPU busy distribution
        const gpuBusy = """ + json.dumps([r.get('gpu_busy', 0) for r in records if isinstance(r.get('gpu_busy'), (int, float))]) + """;
        const gpuChart = new Chart(document.getElementById('gpuChart'), {
            type: 'bar',
            data: {
                labels: ['0-10%', '10-25%', '25-50%', '50-75%', '75-100%'],
                datasets: [{
                    label: 'Count',
                    data: [
                        gpuBusy.filter(x => x < 10).length,
                        gpuBusy.filter(x => x >= 10 && x < 25).length,
                        gpuBusy.filter(x => x >= 25 && x < 50).length,
                        gpuBusy.filter(x => x >= 50 && x < 75).length,
                        gpuBusy.filter(x => x >= 75).length
                    ],
                    backgroundColor: '#58a6ff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8b949e' } } },
                scales: {
                    y: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } },
                    x: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } }
                }
            }
        });
        
        // Time chart (records per hour/day)
        const timeChart = new Chart(document.getElementById('timeChart'), {
            type: 'line',
            data: {
                labels: ['Last collection'],
                datasets: [{
                    label: 'Records collected',
                    data: [""" + str(total_records) + """],
                    borderColor: '#3fb950',
                    backgroundColor: 'rgba(63, 185, 80, 0.1)',
                    tension: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8b949e' } } },
                scales: {
                    y: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } },
                    x: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } }
                }
            }
        });
    </script>
</body>
</html>
"""
    
    return html

def main():
    records = read_jsonl('usage_stats_history.jsonl')
    
    if not records:
        print("No data found in usage_stats_history.jsonl")
        return
    
    print(f"Read {len(records)} records")
    
    html = generate_dashboard(records)
    
    with open('index.html', 'w') as f:
        f.write(html)
    
    print("✓ Generated index.html")

if __name__ == '__main__':
    main()
