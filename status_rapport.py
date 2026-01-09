#!/usr/bin/env python3
import json

# Load the latest usage stats
with open('usage_stats_20260108_205200.json', 'r') as f:
    data = json.load(f)

print("=" * 90)
print("MASKINPARK STATUS - CPU & LOAD RAPPORT")
print("=" * 90)
print()
print(f"Innsamlet: {data.get('collected_at', 'N/A')}")
print(f"Antall maskiner: {data.get('records', 0)}")
print()

# Data structure from collect_script.py:
# [0] machine.serial_number
# [1] machine.hostname
# [2] usage_stats.timestamp
# [3] usage_stats.thermal_pressure
# [4] usage_stats.package_watts
# [5] usage_stats.gpu_busy
# [6-14] various unused fields with nulls
# [15] usage_stats.cpu_idle
# [16] usage_stats.cpu_sys
# [17] usage_stats.cpu_user
# [18] usage_stats.load_avg
# [19+] disk fields

machines = {}
for row in data.get('data', []):
    if len(row) > 18:
        hostname = row[1]
        thermal = row[3]
        package_watts = float(row[4]) if row[4] else 0
        
        # CPU values are strings with % signs: "78.49%"
        try:
            cpu_idle = float(str(row[15]).rstrip('%')) if row[15] else 0
        except (ValueError, TypeError):
            cpu_idle = 0
        
        try:
            cpu_sys = float(str(row[16]).rstrip('%')) if row[16] else 0
        except (ValueError, TypeError):
            cpu_sys = 0
        
        try:
            cpu_user = float(str(row[17]).rstrip('%')) if row[17] else 0
        except (ValueError, TypeError):
            cpu_user = 0
        
        # Load avg is a string: "3.19, 2.39, 2.79" (1-min, 5-min, 15-min)
        load_avg = 0
        if row[18]:
            try:
                load_parts = str(row[18]).split(',')
                load_avg = float(load_parts[0].strip())  # Take 1-minute average
            except (ValueError, TypeError, IndexError):
                load_avg = 0
        
        # Calculate CPU usage (100% - idle%)
        cpu_used = 100 - cpu_idle if cpu_idle >= 0 else 0
        
        machines[hostname] = {
            'thermal': thermal,
            'watts': package_watts,
            'cpu_idle': cpu_idle,
            'cpu_used': cpu_used,
            'cpu_sys': cpu_sys,
            'cpu_user': cpu_user,
            'load_avg': load_avg
        }

# Sort by CPU usage
sorted_machines = sorted(machines.items(), key=lambda x: x[1]['cpu_used'], reverse=True)

print(f"{'Hostname':<20} {'Thermal':<12} {'CPU Used%':<12} {'Load Avg':<12} {'Watts':<10}")
print("-" * 90)

high_cpu = []
high_load = []

for hostname, stats in sorted_machines:
    thermal = stats['thermal']
    cpu_used = stats['cpu_used']
    load_avg = stats['load_avg']
    watts = stats['watts']
    
    # Status indicators
    cpu_status = "⚠️ " if cpu_used > 50 else "✓ "
    thermal_status = "🔴" if thermal == 'Critical' else ("🟡" if thermal == 'Warning' else "🟢")
    
    print(f"{hostname:<20} {thermal_status} {thermal:<10} {cpu_used:>10.1f}% {load_avg:>10.2f} {watts:>8.1f}W")
    
    if cpu_used > 50:
        high_cpu.append((hostname, cpu_used))
    if load_avg > 4:
        high_load.append((hostname, load_avg))

print()
print("=" * 90)
print("SAMMENDRAG")
print("=" * 90)
print(f"✓ Totalt: {len(machines)} maskiner")
if sorted_machines:
    print(f"✓ Gjennomsnittlig CPU-bruk: {sum(m[1]['cpu_used'] for m in sorted_machines) / len(sorted_machines):.1f}%")
    print(f"✓ Gjennomsnittlig Load: {sum(m[1]['load_avg'] for m in sorted_machines) / len(sorted_machines):.2f}")
print()

if high_cpu:
    print(f"⚠️ Høy CPU-belastning (>50%): {len(high_cpu)} maskiner")
    for h, cpu in high_cpu:
        print(f"   - {h}: {cpu:.1f}%")
    print()
else:
    print("✓ Alle maskiner har normal CPU-belastning")
    print()

if high_load:
    print(f"⚠️ Høyt load average (>4): {len(high_load)} maskiner")
    for h, load in high_load:
        print(f"   - {h}: {load:.2f}")
else:
    print("✓ Alle maskiner har normal load average")
