#!/usr/bin/env python3
"""
Try different database table names for storage data
"""

import requests
import os
from urllib.parse import urljoin

session = requests.Session()
cookie_file = os.path.expanduser('~/.mr_session_cookie')
if os.path.exists(cookie_file):
    with open(cookie_file) as f:
        phpsessid = f.read().strip().split('=', 1)[1]
        session.cookies.set('PHPSESSID', phpsessid)

base = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'

# Try different table/module names
for table_name in ['storage', 'disk_report', 'disk', 'hdd', 'volumes', 'filesystems']:
    try:
        r = session.post(
            urljoin(base, '/datatables/data'),
            data={
                'columns[0][name]': f'{table_name}.free',
                'columns[1][name]': f'{table_name}.size',
                'draw': 1, 'length': 1, 'start': 0
            },
            timeout=5, verify=False
        )
        
        if r.status_code == 200:
            j = r.json()
            if j.get('data') and len(j['data']) > 0:
                print(f'✓ {table_name}: {j["data"][0][:2]}')
            elif 'error' in j:
                if 'Base table' in j.get('error', ''):
                    print(f'✗ {table_name}: Table not found')
                else:
                    print(f'✗ {table_name}: {j["error"][:50]}')
            else:
                print(f'~ {table_name}: {list(j.keys())}')
    except Exception as e:
        print(f'! {table_name}: {str(e)[:40]}')
