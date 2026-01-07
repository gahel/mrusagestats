#!/usr/bin/env python3
import requests
import subprocess

base_url = 'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?'
login = 'localuser'
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

session = requests.Session()
session.verify = False
auth_request = session.post(f'{base_url}/auth/login', data={'login': login, 'password': password})

if auth_request.status_code == 200:
    headers = {'x-csrf-token': session.cookies['CSRF-TOKEN']}
    
    test_cols = [
        'diskreport.disksize', 
        'diskreport.capacity', 
        'diskreport.used', 
        'diskreport.usedspace', 
        'diskreport.totalspace', 
        'diskreport.size', 
        'diskreport.percent', 
        'diskreport.percentfree', 
        'diskreport.percentused',
        'diskreport.total',
    ]
    
    for col in test_cols:
        data = {
            'columns[0][name]': 'machine.serial_number',
            'columns[1][name]': col,
            'draw': 1,
            'length': 1,
            'start': 0,
        }
        r = session.post(f'{base_url}/datatables/data', data=data, headers=headers)
        
        try:
            result = r.json()
            if result.get('data') and len(result['data']) > 0:
                print(f'✓ {col:<35} Sample: {result["data"][0][1]}')
        except:
            pass
