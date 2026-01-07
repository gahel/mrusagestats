#!/usr/bin/env python3
"""
Analyze machines.json for various metrics and issues
"""

import json
import sys
from datetime import datetime

def load_machines(filename="machines.json"):
    """Load machines from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ {filename} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ {filename} is not valid JSON")
        sys.exit(1)

def analyze_machines(machines):
    """Analyze machine data and print results"""
    
    now = datetime.now().timestamp()
    
    print("=" * 80)
    print("🔍 MACHINE PARK ANALYSIS")
    print("=" * 80)
    print(f"\nTotal machines: {len(machines)}\n")
    
    # ===== THERMAL PRESSURE =====
    print("🌡️  THERMAL PRESSURE STATUS")
    print("-" * 80)
    thermal_issues = [m for m in machines if m.get('thermal_pressure') == 'Heavy']
    
    if thermal_issues:
        print(f"⚠️  {len(thermal_issues)} machine(s) with HEAVY thermal pressure:\n")
        for m in thermal_issues:
            age = m['last_report']['age_human'] if m['last_report']['age_human'] else 'unknown'
            print(f"  • {m['hostname']:<20} (User: {m['console_user']:<25}) Last: {age}")
            print(f"    Model: {m['description']}")
    else:
        print("✓ All machines have normal thermal pressure\n")
    
    # ===== HIGH CPU LOAD =====
    print("\n⚙️  HIGH CPU LOAD (>75%)")
    print("-" * 80)
    high_cpu = [m for m in machines if m['cpu']['load_percent'] and m['cpu']['load_percent'] > 75]
    
    if high_cpu:
        high_cpu = sorted(high_cpu, key=lambda x: x['cpu']['load_percent'], reverse=True)
        print(f"⚠️  {len(high_cpu)} machine(s) with high CPU load:\n")
        for m in high_cpu[:10]:
            age = m['last_report']['age_human'] if m['last_report']['age_human'] else 'unknown'
            print(f"  • {m['hostname']:<20} {m['cpu']['load_percent']:>6.1f}% (User: {m['console_user']:<15}) Last: {age}")
            print(f"    Model: {m['description']}")
        if len(high_cpu) > 10:
            print(f"\n  ... and {len(high_cpu) - 10} more")
    else:
        print("✓ All machines have CPU load < 75%\n")
    
    # ===== INACTIVE MACHINES =====
    print("\n⏱️  INACTIVE MACHINES (>30 days)")
    print("-" * 80)
    inactive = [m for m in machines if m['last_report']['age_seconds'] and m['last_report']['age_seconds'] > 2592000]
    
    if inactive:
        inactive = sorted(inactive, key=lambda x: x['last_report']['age_seconds'], reverse=True)
        print(f"⚠️  {len(inactive)} inactive machine(s):\n")
        for m in inactive[:10]:
            print(f"  • {m['hostname']:<20} (User: {m['console_user']:<20}) Last: {m['last_report']['age_human']}")
            print(f"    Model: {m['description']}")
        if len(inactive) > 10:
            print(f"\n  ... and {len(inactive) - 10} more")
    else:
        print("✓ All machines have reported within last 30 days\n")
    
    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    print(f"\n✓ Total machines:           {len(machines)}")
    print(f"⚠️  Heavy thermal pressure:   {len(thermal_issues)}")
    print(f"⚠️  High CPU load (>75%):    {len(high_cpu)}")
    print(f"⚠️  Inactive (>30 days):     {len(inactive)}")
    
    if thermal_issues:
        print(f"\n→ ACTION: Contact users of machines with heavy thermal pressure")
        print(f"  Machines: {', '.join([m['hostname'] for m in thermal_issues])}")
    
    if high_cpu:
        print(f"\n→ ACTION: Investigate high CPU load on these machines:")
        for m in high_cpu[:5]:
            print(f"  • {m['hostname']} ({m['cpu']['load_percent']:.1f}%) - User: {m['console_user']}")
    
    if inactive:
        print(f"\n→ ACTION: Check status of inactive machines (may be lost or decommissioned)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    machines = load_machines()
    analyze_machines(machines)
