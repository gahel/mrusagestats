#!/usr/bin/env python3
"""
Brute force test - try all module names from the installed list
to see which ones have accessible data via datatables
"""

import requests
import os

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'

# All installed modules from earlier dump
modules = [
    'applications', 'appusage', 'ard', 'bluetooth', 'caching', 'certificate', 
    'crashplan', 'detectx', 'devtools', 'directory_service', 'disk_report', 
    'displays_info', 'extensions', 'fan_temps', 'filevault_escrow', 'filevault_status', 
    'findmymac', 'firewall', 'fonts', 'gpu', 'homebrew', 'homebrew_info', 'ibridge', 
    'installhistory', 'inventory', 'location', 'machine', 'managedinstalls', 'mbbr_status', 
    'mdm_status', 'munki_facts', 'munkiinfo', 'munkireport', 'munkireportinfo', 'network', 
    'network_shares', 'power', 'printer', 'profile', 'sccm_status', 'security', 'sentinelone', 
    'sentinelonequarantine', 'smart_stats', 'softwareupdate', 'sophos', 'supported_os', 
    'timemachine', 'usage_stats', 'usb', 'user_sessions', 'users', 'warranty', 'wifi'
]

print("Testing which modules have storage-related data...\n")

for module in modules:
    # Try different column name patterns for each module
    for col_suffix in ['free', 'used', 'size', 'total', 'space']:
        try:
            query_data = {
                'columns[0][name]': f'{module}.id',
                'columns[1][name]': f'{module}.{col_suffix}',
                'draw': 1,
                'length': 1,
                'start': 0,
            }
            
            r = session.post(base + '/datatables/data', data=query_data, timeout=5, verify=False)
            data = r.json()
            
            if data.get('data') and len(data['data']) > 0:
                print(f"✓✓ {module}.{col_suffix} HAS DATA!")
                print(f"   {data['data'][0]}")
        except:
            pass
