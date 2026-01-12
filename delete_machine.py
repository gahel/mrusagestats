#!/usr/bin/env python3
"""
Script to delete machines from MunkiReport by serial number
"""

import os
import subprocess
import requests
import sys

def munkireport_delete_machine(serial_number, login, password, base_url):
    """Delete a machine from MunkiReport"""
    auth_url = f"{base_url}/auth/login"
    delete_url = f"{base_url}/manager/delete_machine/{serial_number}"

    ses = requests.session()
    ses.verify = False
    
    # Authenticate
    response = ses.post(auth_url, data={'login': login, 'password': password})
    
    if response.status_code != 200:
        print(f"    Authentication failed")
        return False
    
    headers = {"x-csrf-token": ses.cookies.get("CSRF-TOKEN", "")}
    
    # Delete machine
    delete_result = ses.delete(delete_url, headers=headers)
    
    if delete_result.status_code != 200:
        print(f"    ❌ Error deleting {serial_number}: {delete_result.status_code}")
        return False
    else:
        print(f"    ✅ {serial_number} deleted from MunkiReport")
        return True

def main():
    # Get credentials from environment or keychain
    password = os.environ.get('MR_PASSWORD')
    if not password:
        try:
            password = subprocess.check_output(
                ['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w'],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            print("Error: MR_PASSWORD not set and keychain entry not found")
            sys.exit(1)
    
    login = "localuser"
    base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
    
    # List of serial numbers to delete
    serial_numbers = []
    
    if len(sys.argv) > 1:
        serial_numbers = sys.argv[1:]
    else:
        print("Usage: python3 delete_machine.py <serial_number> [serial_number2] ...")
        print("Example: python3 delete_machine.py C3W0FX49WN CF6RFYQ03F")
        sys.exit(1)

    deleted_count = 0
    failed_count = 0
    
    for serial_number in serial_numbers:
        print('='*50)
        print(f'Deleting {serial_number}...')
        
        if serial_number.strip():
            if munkireport_delete_machine(serial_number, login, password, base_url):
                deleted_count += 1
            else:
                failed_count += 1
        else:
            print(f'    ⚠️  Invalid serial number')
            failed_count += 1
        
        print('='*50)
    
    print(f"\nSummary: {deleted_count} deleted, {failed_count} failed")

if __name__ == "__main__":
    main()
