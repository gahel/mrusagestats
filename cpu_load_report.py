#!/usr/bin/env python3
"""
Generate CPU load and performance report
"""
import json
import subprocess
from collections import defaultdict
from datetime import datetime

def get_latest_stats():
    """Get the most recent usage stats file"""
    result = subprocess.run(
        ['ls', '-t', 'usage_stats_*.json'],
        capture_output=True,
        text=True,
        shell=True
    )
    files = result.stdout.strip().split('\n')
    if files and files[0]:
        return files[0]
    return None

# Read data
stats_file = get_latest_stats()
if not stats_file:
    print("No usage stats files found")
    exit(1)

print(f"Reading data from: {stats_file}\n")

try:
    with open(stats_file, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error reading file: {e}")
    exit(1)

# Parse data - look at structure first
if not data.get('data'):
    print("No data in file")
    exit(1)

# Examine first row to understand structure
first_row = data['data'][0]
print(f"Data structure (first row has {len(first_row)} columns):\n")
cols = data.get('columns', [])
for i, col in enumerate(cols[:25]):
    print(f"  [{i:2d}] {col}")
print()

# Aggregate by machine
machines = defaultdict(lambda: {
    'cpu_user': [],
    'cpu_sys': [],
    'cpu_idle': [],
    'load_avg': [],
    'thermal': []
})

# Match columns to indices
col_map = {col: i for i, col in enumerate(cols)}
hostname_idx = col_map.get('machine.hostname', 1)
cpu_user_idx = col_map.get('usage_stats.cpu_user', None)
cpu_sys_idx = col_map.get('usage_stats.cpu_sys', None)
cpu_idle_idx = col_map.get('usage_stats.cpu_idle', None)
load_avg_idx = col_map.get('usage_stats.load_avg', None)
thermal_idx = col_map.get('usage_stats.thermal_pressure', None)

print(f"Column indices:")
print(f"  hostname: {hostname_idx}")
print(f"  cpu_user: {cpu_user_idx}")
print(f"  cpu_sys: {cpu_sys_idx}")
print(f"  cpu_idle: {cpu_idle_idx}")
print(f"  load_avg: {load_avg_idx}")
print(f"  thermal: {thermal_idx}\n")

for row in data.get('data', []):
    try:
        hostname = row[hostname_idx] if hostname_idx and hostname_idx < len(row) else 'Unknown'
        
        if cpu_idle_idx and cpu_idle_idx < len(row):
            cpu_idle = float(row[cpu_idle_idx]) if row[cpu_idle_idx] else 0
            machines[hostname]['cpu_idle'].append(cpu_idle)
        
        if cpu_sys_idx and cpu_sys_idx < len(row):
            cpu_sys = float(row[cpu_sys_idx]) if row[cpu_sys_idx] else 0
            machines[hostname]['cpu_sys'].append(cpu_sys)
        
        if cpu_user_idx and cpu_user_idx < len(row):
            cpu_user = float(row[cpu_user_idx]) if row[cpu_user_idx] else 0
            machines[hostname]['cpu_user'].append(cpu_user)
        
        if load_avg_idx and load_avg_idx < len(row):
            load_avg = row[load_avg_idx]
            if load_avg:
                try:
                    machines[hostname]['load_avg'].append(float(load_avg))
                except:
                    pass
        
        if thermal_idx and thermal_idx < len(row):
            thermal = row[thermal_idx]
            if thermal:
                machines[hostname]['thermal'].append(thermal)
    except Exception as e:
        continue

# Calculate averages
results = []
for hostname, stats in machines.items():
    if stats['cpu_idle']:
        cpu_idle_avg = sum(stats['cpu_idle']) / len(stats['cpu_idle'])
        cpu_sys_avg = sum(stats['cpu_sys']) / len(stats['cpu_sys']) if stats['cpu_sys'] else 0
        cpu_user_avg = sum(stats['cpu_user']) / len(stats['cpu_user']) if stats['cpu_user'] else 0
        
        load_avg = 0
        if stats['load_avg']:
            load_avg = sum(stats['load_avg']) / len(stats['load_avg'])
        
        thermal = stats['thermal'][0] if stats['thermal'] else 'N/A'
        
        results.append({
            'hostname': hostname,
            'cpu_idle': cpu_idle_avg,
            'cpu_sys': cpu_sys_avg,
            'cpu_user': cpu_user_avg,
            'load_avg': load_avg,
            'thermal': thermal
        })

# Sort by load average
results.sort(key=lambda x: x['load_avg'], reverse=True)

print("=" * 100)
print("CPU LOAD & PERFORMANCE REPORT")
print("=" * 100)
print()

print(f"{'Hostname':<20} {'CPU Idle':<12} {'CPU User':<12} {'CPU Sys':<12} {'Load Avg':<12} {'Thermal':<12}")
print("-" * 100)

high_load = []
for r in results:
    status = "⚠️ " if r['cpu_user'] > 50 else "✓ "
    print(f"{r['hostname']:<20} {r['cpu_idle']:>10.1f}% {r['cpu_user']:>10.1f}% {r['cpu_sys']:>10.1f}% {r['load_avg']:>10.2f} {str(r['thermal']):<12}")
    if r['cpu_user'] > 50:
        high_load.append(r['hostname'])

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Total machines: {len(results)}")
avg_cpu_user = sum(r['cpu_user'] for r in results) / len(results) if results else 0
avg_load = sum(r['load_avg'] for r in results) / len(results) if results else 0
print(f"Average CPU User: {avg_cpu_user:.1f}%")
print(f"Average Load Avg: {avg_load:.2f}")

if high_load:
    print(f"High CPU load (>50%): {len(high_load)} machines")
    for h in high_load:
        print(f"  - {h}")
else:
    print("✓ All machines have normal CPU usage")
