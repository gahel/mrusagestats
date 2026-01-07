#!/usr/bin/env python3
"""
Script to run automated queries against the munkireport datatables API

Results are returned in JSON format.
The actual entries are in the 'data' variable.

To make this work, set up a regular user in munkireport and adjust the 
proper values below.

Author: Arjen van Bochoven (original shell script)
Date: 2015-11-06
Modified: 2020-03-31 Added CSRF support
Python Version: 2026-01-07
"""

import requests
import json
import sys
import re

# Configuration
DEBUG = False
MR_BASE_URL = 'http://localhost:8888/index.php'
MR_DATA_QUERY = '/datatables/data'
MR_LOGIN = 'test'
MR_PASSWORD = 'test'

CLIENT_COLUMNS = [
    "machine.serial_number",
    "machine.hostname",
    "machine.machine_desc",
    "reportdata.timestamp",
    "reportdata.console_user",
    "machine.os_version",
    "reportdata.remote_ip",
    "munkireport.manifestname",
]


def columns_to_query(columns):
    """Create query parameters from column names"""
    query_params = {}
    for idx, column in enumerate(columns):
        query_params[f'columns[{idx}][name]'] = column
    return query_params


def authenticate():
    """Authenticate to munkireport and retrieve session cookie and CSRF token"""
    if DEBUG:
        print('Authenticating to munkireport..', file=sys.stderr)
    
    auth_url = f'{MR_BASE_URL}?/auth/login'
    auth_data = {
        'login': MR_LOGIN,
        'password': MR_PASSWORD
    }
    
    session = requests.Session()
    response = session.post(auth_url, data=auth_data)
    
    # Extract CSRF token from cookies or headers
    csrf_token = None
    if 'X-CSRF-TOKEN' in response.headers:
        csrf_token = response.headers['X-CSRF-TOKEN']
    elif 'CSRF-TOKEN' in response.cookies:
        csrf_token = response.cookies['CSRF-TOKEN']
    
    return session, csrf_token


def retrieve_data(session, csrf_token):
    """Retrieve data from the datatables API"""
    if DEBUG:
        print('Retrieving client data..', file=sys.stderr)
    
    # Build query parameters
    query_params = columns_to_query(CLIENT_COLUMNS)
    
    # Build the full URL
    data_url = f'{MR_BASE_URL}?{MR_DATA_QUERY}'
    
    # Set up headers
    headers = {}
    if csrf_token:
        headers['X-CSRF-TOKEN'] = csrf_token
    
    # Make the request
    response = session.get(data_url, params=query_params, headers=headers)
    
    return response.json() if response.text else {}


def main():
    """Main function"""
    try:
        # Authenticate
        session, csrf_token = authenticate()
        
        # Retrieve data
        data = retrieve_data(session, csrf_token)
        
        # Output as JSON
        print(json.dumps(data))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
