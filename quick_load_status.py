#!/usr/bin/env python3
"""
Quick script to fetch current load averages for all machines
"""
import os
import subprocess
import requests
import json
from datetime import datetime

def get_load_status():
    # Get password from env or keychain
    password = os.environ.get('MR_PASSWORD')
    if not password:
        try:
            password = subprocess.check_output(
                ['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w'],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            print("Error: MR_PASSWORD not set and keychain entry not found")
            return

    base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
    login = "localuser"
    
    # Columns we need for load status
    columns = [
        "machine.serial_number",
        "machine.hostname", 
        "reportdata.long_username",
        "usage_stats.timestamp",
        "usage_stats.load_avg"
    ]

    auth_url = f"{base_url}/auth/login"
    query_url = f"{base_url}/datatables/data"
    session = requests.Session()
    session.verify = False

    auth_request = session.post(auth_url, data={"login": login, "password": password})
    
    if auth_request.status_code != 200:
        print("❌ Authentication failed")
        return

    headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}
    query_data = {f"columns[{i}][name]": c for i, c in enumerate(columns)}

    response = session.post(query_url, data=query_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ API request failed: {response.status_code}")
        return

    data = response.json()
    
    # Process and display the data
    machines = {}
    current_time = datetime.now()
    
    print(f"\n📊 Load Average Status - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Debug: Show some raw data first
    debug_count = 0
    for row in data.get('data', []):
        if debug_count < 3:  # Show first 3 entries for debugging
            print(f"DEBUG: Raw data sample {debug_count + 1}: {row}")
            debug_count += 1
    print("="*80)
    
    for row in data.get('data', []):
        if len(row) >= 5:
            serial = row[0]
            hostname = row[1] or "Unknown"
            username = row[2] or "Unknown"
            timestamp = row[3]
            load_avg = row[4]
            
            # Debug timestamp
            if timestamp:
                try:
                    ts_dt = datetime.fromtimestamp(int(timestamp))
                    age_hours = (current_time - ts_dt).total_seconds() / 3600
                    if serial in ['C3W0FX49WN', 'CF6RFYQ03F']:  # Debug specific machines
                        print(f"DEBUG {hostname}: timestamp={timestamp}, date={ts_dt}, age={age_hours:.1f}h, load_avg='{load_avg}'")
                except:
                    print(f"DEBUG {hostname}: bad timestamp={timestamp}, load_avg='{load_avg}'")
            
            # Parse load average
            load_short = load_middle = load_long = 0.0
            if load_avg:
                try:
                    # Handle comma-separated format: "122.13, 63.35, 26.33"
                    load_parts = [x.strip() for x in str(load_avg).replace(',', ' ').split()]
                    if len(load_parts) >= 1:
                        load_short = float(load_parts[0])
                    if len(load_parts) >= 2:
                        load_middle = float(load_parts[1])
                    if len(load_parts) >= 3:
                        load_long = float(load_parts[2])
                except (ValueError, TypeError):
                    if serial in ['C3W0FX49WN', 'CF6RFYQ03F']:  # Debug specific machines
                        print(f"DEBUG {hostname}: Failed to parse load_avg='{load_avg}'")
                    pass
            
            # Keep most recent entry per machine
            if serial not in machines or (timestamp and timestamp > machines[serial].get('timestamp', 0)):
                machines[serial] = {
                    'hostname': hostname,
                    'username': username,
                    'timestamp': timestamp,
                    'load_short': load_short,
                    'load_middle': load_middle,
                    'load_long': load_long
                }
    
    # Sort by load_short (descending)
    sorted_machines = sorted(machines.items(), key=lambda x: x[1]['load_short'], reverse=True)
    
    print(f"{'Hostname':<20} {'User':<15} {'Load (1m/5m/15m)':<20} {'Serial':<12}")
    print("-"*80)
    
    for serial, machine in sorted_machines:
        hostname = machine['hostname'][:19] if machine['hostname'] else "Unknown"
        username = machine['username'][:14] if machine['username'] else "Unknown"
        load_str = f"{machine['load_short']:.2f}/{machine['load_middle']:.2f}/{machine['load_long']:.2f}"
        
        # Color coding based on load
        if machine['load_short'] > 8.0:
            color = "🔴"  # High load
        elif machine['load_short'] > 4.0:
            color = "🟡"  # Medium load
        else:
            color = "🟢"  # Low load
            
        print(f"{hostname:<20} {username:<15} {load_str:<20} {serial:<12} {color}")
    
    print(f"\nTotal machines: {len(machines)}")
    if sorted_machines:
        print(f"Highest load: {sorted_machines[0][1]['hostname']} ({sorted_machines[0][1]['load_short']:.2f})")
        print(f"Lowest load: {sorted_machines[-1][1]['hostname']} ({sorted_machines[-1][1]['load_short']:.2f})")

if __name__ == "__main__":
    get_load_status()