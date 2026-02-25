#!/usr/bin/env python3
"""
Get detailed usage stats for a specific machine
"""
import os
import subprocess
import requests
import json
from datetime import datetime

def get_machine_usage_stats(target_serial):
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
    
    # All usage stats columns
    columns = [
        "machine.serial_number",
        "machine.hostname", 
        "reportdata.long_username",
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
        "diskreport.percentage"
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
    data = response.json()
    
    # Filter for target machine and collect all records
    machine_records = []
    machine_info = None
    
    for row in data.get('data', []):
        if len(row) >= len(columns) and row[0] == target_serial:
            record = {
                'serial_number': row[0],
                'hostname': row[1],
                'username': row[2],
                'timestamp': row[3],
                'thermal_pressure': row[4],
                'package_watts': row[5],
                'gpu_busy': row[6],
                'freq_hz': row[7],
                'freq_ratio': row[8],
                'gpu_freq_mhz': row[9],
                'backlight': row[10],
                'keyboard_backlight': row[11],
                'ibyte_rate': row[12],
                'obyte_rate': row[13],
                'rbytes_per_s': row[14],
                'wbytes_per_s': row[15],
                'cpu_idle': row[16],
                'cpu_sys': row[17],
                'cpu_user': row[18],
                'load_avg': row[19],
                'disk_total': row[20],
                'disk_free': row[21],
                'disk_percentage': row[22]
            }
            
            machine_records.append(record)
            if not machine_info:
                machine_info = {
                    'hostname': row[1],
                    'username': row[2],
                    'serial': row[0]
                }
    
    if not machine_records:
        print(f"❌ No data found for machine {target_serial}")
        return
    
    # Sort by timestamp (most recent first)
    machine_records.sort(key=lambda x: x['timestamp'] if x['timestamp'] else 0, reverse=True)
    
    print(f"\n📊 Usage Stats for {machine_info['hostname']} ({machine_info['username']})")
    print(f"Serial: {target_serial}")
    print(f"Total records: {len(machine_records)}")
    print("="*80)
    
    # Show recent records with timestamps
    current_time = datetime.now()
    for i, record in enumerate(machine_records[:10]):  # Show last 10 records
        if record['timestamp']:
            try:
                ts_dt = datetime.fromtimestamp(int(record['timestamp']))
                age_hours = (current_time - ts_dt).total_seconds() / 3600
                
                # Parse load average
                load_avg_str = "N/A"
                if record['load_avg']:
                    try:
                        load_parts = [x.strip() for x in str(record['load_avg']).replace(',', ' ').split()]
                        if len(load_parts) >= 3:
                            load_avg_str = f"{load_parts[0]}/{load_parts[1]}/{load_parts[2]}"
                        elif len(load_parts) >= 1:
                            load_avg_str = load_parts[0]
                    except:
                        load_avg_str = str(record['load_avg'])
                
                print(f"Record {i+1:2d}: {ts_dt.strftime('%Y-%m-%d %H:%M:%S')} ({age_hours:5.1f}h ago)")
                print(f"           Load: {load_avg_str:<20} CPU: {record['cpu_user']}/{record['cpu_sys']}/{record['cpu_idle']}")
                print(f"           Thermal: {record['thermal_pressure']:<12} Watts: {record['package_watts']}")
                print(f"           GPU: {record['gpu_busy']:<12} Freq: {record['freq_hz']}")
                print()
            except:
                print(f"Record {i+1:2d}: Invalid timestamp {record['timestamp']}")
    
    # Save detailed data to file
    filename = f"machine_{machine_info['hostname']}_{target_serial}_detailed.json"
    with open(filename, 'w') as f:
        json.dump({
            'machine_info': machine_info,
            'records': machine_records,
            'summary': {
                'total_records': len(machine_records),
                'date_range': {
                    'oldest': machine_records[-1]['timestamp'] if machine_records else None,
                    'newest': machine_records[0]['timestamp'] if machine_records else None
                }
            }
        }, f, indent=2)
    
    print(f"💾 Detailed data saved to: {filename}")
    return filename

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        serial = sys.argv[1]
    else:
        serial = "V26XYWP739"  # MBP-15658 (Rune Ryen)
    
    get_machine_usage_stats(serial)