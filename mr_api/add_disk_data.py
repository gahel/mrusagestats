#!/usr/bin/env python3
"""
Manual disk space database from Storage Report
Maps serial numbers to disk free/total in GB
"""

import json
import os

# Data extracted from Storage Report
# Format: serial_number -> {free_gb, total_gb}
DISK_DATA = {
    "CWMJW4O34C": {"free_gb": 13, "total_gb": 245},      # MBP-23810
    "YJC79LX6FJ": {"free_gb": 19, "total_gb": 245},      # MBP-09414
    "Q69GDC9DDF": {"free_gb": 92, "total_gb": 245},      # MBP-26032
    "MTPQRC2XYQ": {"free_gb": 97, "total_gb": 245},      # MBP-11309
    "WLYX6QW77T": {"free_gb": 99, "total_gb": 245},      # MBP-20022
    "H5C2D6HKQQ": {"free_gb": 105, "total_gb": 245},     # MBP-02974
    "QQW6150XCX": {"free_gb": 110, "total_gb": 494},     # MBP-28208
    "CR9XND636L": {"free_gb": 114, "total_gb": 245},     # MBP-11403
    "JYX4DW1712": {"free_gb": 114, "total_gb": 494},     # MBP-27687
    "GGQF3902FN": {"free_gb": 128, "total_gb": 494},     # MBP-15799
}

def get_disk_data(serial_number):
    """Get disk data for a machine, return None if not found"""
    return DISK_DATA.get(serial_number)

def add_disk_data_to_machines():
    """Add disk data to machines.json"""
    machines_file = 'machines.json'
    
    if not os.path.exists(machines_file):
        print("❌ machines.json not found")
        return
    
    with open(machines_file, 'r') as f:
        machines = json.load(f)
    
    updated_count = 0
    missing_count = 0
    
    for machine in machines:
        serial = machine.get('serial_number')
        disk = get_disk_data(serial)
        
        if disk:
            machine['disk_free_gb'] = disk['free_gb']
            machine['disk_total_gb'] = disk['total_gb']
            machine['disk_free_percent'] = round((disk['free_gb'] / disk['total_gb']) * 100, 1)
            updated_count += 1
        else:
            # Mark as unknown if not in our database
            machine['disk_free_gb'] = None
            machine['disk_total_gb'] = None
            machine['disk_free_percent'] = None
            missing_count += 1
    
    # Save updated machines
    with open(machines_file, 'w') as f:
        json.dump(machines, f, indent=2)
    
    print(f"✓ Updated {updated_count} machines with disk data")
    print(f"⚠️  {missing_count} machines missing disk data (need to be added manually)")
    print(f"\nTo add more disk data, edit DISK_DATA in add_disk_data.py")

if __name__ == "__main__":
    add_disk_data_to_machines()
