#!/usr/bin/env python3
"""
Samler client activity data fra MunkiReport.
Kjør dette scriptet hver time (f.eks. via cron) for å bygge opp historisk data.

Lagrer data i client_activity_history.json
"""
import requests
import subprocess
import json
from datetime import datetime
import os
import warnings

warnings.filterwarnings('ignore')

base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
login = "localuser"
password = subprocess.check_output(['security', 'find-generic-password', '-a', 'localuser', '-s', 'munkireport-api', '-w']).decode().strip()

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_activity_history.json")

# Kolonner for å hente timestamp data
columns = [
    "machine.serial_number",
    "reportdata.timestamp",
]

def authenticate():
    """Autentiser mot MunkiReport API"""
    auth_url = f"{base_url}/auth/login"
    session = requests.Session()
    session.verify = False
    auth_request = session.post(auth_url, data={"login": login, "password": password})
    
    if auth_request.status_code != 200:
        raise Exception("Authentication failed")
    
    return session

def get_client_activity(session):
    """Hent client activity data"""
    query_url = f"{base_url}/datatables/data"
    headers = {"x-csrf-token": session.cookies["CSRF-TOKEN"]}
    
    query_data = {f"columns[{i}][name]": c for i, c in enumerate(columns)}
    response = session.post(query_url, data=query_data, headers=headers)
    result = response.json()
    
    if "error" in result:
        raise Exception(f"API error: {result['error']}")
    
    return result

def calculate_clients_per_hour(data, current_time):
    """Beregn antall klienter som har rapportert inn siste time"""
    one_hour_ago = current_time - 3600
    clients_last_hour = 0
    total_clients = 0
    active_clients = 0
    
    for machine in data.get('data', []):
        total_clients += 1
        # timestamp er i indeks 1 (reportdata.timestamp)
        timestamp = machine[1] if len(machine) > 1 else None
        
        if timestamp:
            try:
                ts = int(timestamp)
                # Aktiv = rapportert siste 24 timer
                if ts > (current_time - 86400):
                    active_clients += 1
                # Clients per hour = rapportert siste time
                if ts > one_hour_ago:
                    clients_last_hour += 1
            except (ValueError, TypeError):
                pass
    
    return {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "clients_per_hour": clients_last_hour
    }

def load_history():
    """Last historisk data fra fil"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"measurements": []}

def save_history(history):
    """Lagre historisk data til fil"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def cleanup_old_data(history, days=7):
    """Fjern data eldre enn angitt antall dager"""
    cutoff = datetime.now().timestamp() - (days * 24 * 3600)
    history["measurements"] = [
        m for m in history["measurements"]
        if m.get("timestamp", 0) > cutoff
    ]
    return history

def main():
    try:
        session = authenticate()
        data = get_client_activity(session)
        current_time = datetime.now().timestamp()
        
        stats = calculate_clients_per_hour(data, current_time)
        
        # Last og oppdater historikk
        history = load_history()
        
        measurement = {
            "timestamp": int(current_time),
            "datetime": datetime.now().isoformat(),
            "total_clients": stats["total_clients"],
            "active_clients": stats["active_clients"],
            "clients_per_hour": stats["clients_per_hour"]
        }
        
        history["measurements"].append(measurement)
        
        # Fjern data eldre enn 7 dager
        history = cleanup_old_data(history, days=7)
        
        save_history(history)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
              f"Total: {stats['total_clients']}, "
              f"Active: {stats['active_clients']}, "
              f"Per hour: {stats['clients_per_hour']}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
