#!/usr/bin/env python3
"""
Find the 5 machines with highest load average
"""
import json
import os
from datetime import datetime

def is_checked_in_recently(timestamp, days=3):
    """Check if the timestamp is from the last 'days' days"""
    if not timestamp:
        return False
    
    try:
        machine_date = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        days_diff = (now - machine_date).days
        return days_diff <= days
    except (ValueError, TypeError, OSError):
        return False

def parse_load_avg(load_avg_val):
    """Parse load average value and return the 1-minute average (first value)"""
    if load_avg_val is None or load_avg_val == 'null':
        return 0.0
    
    # If it's already a number, return it directly
    if isinstance(load_avg_val, (int, float)):
        return float(load_avg_val)
    
    # If it's a string, try to parse it
    if isinstance(load_avg_val, str):
        try:
            # Load average is typically "1.23, 4.56, 7.89" - we want the first value (1-minute avg)
            first_value = load_avg_val.split(',')[0].strip()
            return float(first_value)
        except (ValueError, IndexError):
            return 0.0
    
    return 0.0

def find_latest_data_file():
    """Find the most recent JSON data file"""
    data_files = []
    for file in os.listdir('.'):
        if file.startswith('get_data_') and file.endswith('.json'):
            data_files.append(file)
    
    if not data_files:
        raise FileNotFoundError("No data files found")
    
    # Sort by filename (which includes timestamp)
    data_files.sort(reverse=True)
    return data_files[0]

def main():
    try:
        # Find latest data file
        latest_file = find_latest_data_file()
        print(f"📊 Analyzing data from: {latest_file}")
        print("=" * 60)
        
        # Load data
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        machines_data = data.get('data', [])
        
        if not machines_data:
            print("No machine data found in file")
            return
        
        # Process each machine
        machines_with_load = []
        machines_checked_in_today = 0
        for machine_row in machines_data:
            try:
                # Extract relevant fields
                serial_number = machine_row[0] if len(machine_row) > 0 else "Unknown"
                hostname = machine_row[1] if len(machine_row) > 1 else "Unknown"
                machine_desc = machine_row[2] if len(machine_row) > 2 else "Unknown"
                timestamp = machine_row[3] if len(machine_row) > 3 else None
                console_user = machine_row[8] if len(machine_row) > 8 else "Unknown"
                long_username = machine_row[9] if len(machine_row) > 9 else "Unknown"
                load_avg_raw = machine_row[21] if len(machine_row) > 21 else None
                thermal_pressure = machine_row[17] if len(machine_row) > 17 else "Unknown"
                cpu_idle = machine_row[18] if len(machine_row) > 18 else "Unknown"
                cpu_sys = machine_row[19] if len(machine_row) > 19 else "Unknown" 
                cpu_user = machine_row[20] if len(machine_row) > 20 else "Unknown"
                
                # Check if machine checked in recently (last 3 days)
                if not is_checked_in_recently(timestamp, days=3):
                    continue
                
                machines_checked_in_today += 1
                
                # Parse load average
                load_avg_1min = parse_load_avg(load_avg_raw)
                
                machines_with_load.append({
                    'serial_number': serial_number,
                    'hostname': hostname,
                    'machine_desc': machine_desc,
                    'console_user': console_user,
                    'long_username': long_username,
                    'load_avg_raw': load_avg_raw,
                    'load_avg_1min': load_avg_1min,
                    'thermal_pressure': thermal_pressure,
                    'cpu_idle': cpu_idle,
                    'cpu_sys': cpu_sys,
                    'cpu_user': cpu_user,
                    'timestamp': timestamp,
                    'check_in_time': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "Unknown"
                })
            except (IndexError, ValueError) as e:
                print(f"Error processing machine: {e}")
                continue
        
        # Sort by load average (descending)
        machines_with_load.sort(key=lambda x: x['load_avg_1min'], reverse=True)
        
        # Display top 5
        print(f"🔥 TOP 5 MACHINES BY LOAD AVERAGE (1-min) - CHECKED IN RECENTLY (last 3 days)")
        print(f"Machines checked in recently: {machines_checked_in_today}")
        print(f"Total machines in dataset: {len(machines_data)}")
        print("=" * 80)
        
        for i, machine in enumerate(machines_with_load[:5], 1):
            print(f"\n#{i} - {machine['hostname']} ({machine['serial_number']})")
            print(f"    Model: {machine['machine_desc']}")
            print(f"    User: {machine['long_username']} ({machine['console_user']})")
            print(f"    Check-in time: {machine['check_in_time']}")
            print(f"    Load Avg: {machine['load_avg_raw']}")
            print(f"    1-min Load: {machine['load_avg_1min']:.2f}")
            print(f"    Thermal: {machine['thermal_pressure']}")
            print(f"    CPU Usage: User={machine['cpu_user']}, Sys={machine['cpu_sys']}, Idle={machine['cpu_idle']}")
            print("-" * 50)
        
        # Show some stats
        print(f"\n📈 STATISTICS")
        print("=" * 30)
        print(f"Total machines in dataset: {len(machines_data)}")
        print(f"Machines checked in recently: {machines_checked_in_today}")
        print(f"Machines with load data (recent): {len(machines_with_load)}")
        avg_load = sum(m['load_avg_1min'] for m in machines_with_load) / len(machines_with_load) if machines_with_load else 0
        max_load = max((m['load_avg_1min'] for m in machines_with_load), default=0)
        
        print(f"Average load (recent): {avg_load:.2f}")
        print(f"Highest load (recent): {max_load:.2f}")
        
        # Show machines with high thermal pressure (recent only)
        high_thermal = [m for m in machines_with_load if m['thermal_pressure'] not in ['Nominal', 'Unknown', None]]
        if high_thermal:
            print(f"\n🌡️  MACHINES WITH HIGH THERMAL PRESSURE (RECENT):")
            print("=" * 50)
            for machine in high_thermal:
                print(f"  {machine['hostname']} ({machine['check_in_time']}): {machine['thermal_pressure']}")
        
        if not machines_with_load:
            print("\n⚠️  No machines found that checked in recently!")
            print("Try checking with a different date range or verify the data.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()