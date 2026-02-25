#!/usr/bin/env python3
"""
Visualiserer "clients per hour" over de siste 7 dagene.
Krever at client_activity_collector.py har kjørt periodisk for å samle data.
"""
import json
import os
from datetime import datetime, timedelta
import sys

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_activity_history.json")

def load_history():
    """Last historisk data fra fil"""
    if not os.path.exists(HISTORY_FILE):
        print("Ingen historisk data funnet.")
        print("Kjør først: python3 client_activity_collector.py")
        sys.exit(1)
    
    with open(HISTORY_FILE, 'r') as f:
        return json.load(f)

def format_bar(value, max_value, width=50):
    """Lag en ASCII bar"""
    if max_value == 0:
        return ""
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)

def group_by_hour(measurements):
    """Grupper målinger per time"""
    hourly_data = {}
    
    for m in measurements:
        dt = datetime.fromisoformat(m["datetime"])
        hour_key = dt.strftime("%Y-%m-%d %H:00")
        
        if hour_key not in hourly_data:
            hourly_data[hour_key] = []
        hourly_data[hour_key].append(m["clients_per_hour"])
    
    # Ta gjennomsnitt per time
    result = {}
    for hour_key, values in hourly_data.items():
        result[hour_key] = sum(values) / len(values)
    
    return result

def group_by_day(measurements):
    """Grupper målinger per dag"""
    daily_data = {}
    
    for m in measurements:
        dt = datetime.fromisoformat(m["datetime"])
        day_key = dt.strftime("%Y-%m-%d")
        
        if day_key not in daily_data:
            daily_data[day_key] = {
                "values": [],
                "max_per_hour": 0,
                "total_active": []
            }
        daily_data[day_key]["values"].append(m["clients_per_hour"])
        daily_data[day_key]["max_per_hour"] = max(daily_data[day_key]["max_per_hour"], m["clients_per_hour"])
        daily_data[day_key]["total_active"].append(m.get("active_clients", 0))
    
    return daily_data

def print_7day_graph(history):
    """Vis graf over 7 dager"""
    measurements = history.get("measurements", [])
    
    if not measurements:
        print("Ingen målinger funnet.")
        return
    
    print("\n" + "=" * 70)
    print("📊 CLIENT ACTIVITY - SISTE 7 DAGER")
    print("=" * 70)
    
    # Grupper per dag
    daily_data = group_by_day(measurements)
    
    if not daily_data:
        print("Ingen data å vise.")
        return
    
    # Finn maks for skalering
    max_per_hour = max(
        d["max_per_hour"] for d in daily_data.values()
    ) or 1
    
    # Vis daglig oppsummering
    print(f"\n{'Dag':<12} {'Snitt CPH':>10} {'Maks CPH':>10} {'Graf':<52}")
    print("-" * 70)
    
    sorted_days = sorted(daily_data.keys())
    
    for day in sorted_days:
        data = daily_data[day]
        avg_cph = sum(data["values"]) / len(data["values"]) if data["values"] else 0
        max_cph = data["max_per_hour"]
        
        # Bruk ukedag for lesbarhet
        dt = datetime.strptime(day, "%Y-%m-%d")
        weekday = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"][dt.weekday()]
        day_label = f"{weekday} {dt.strftime('%d/%m')}"
        
        bar = format_bar(max_cph, max_per_hour, 40)
        
        print(f"{day_label:<12} {avg_cph:>10.1f} {max_cph:>10} {bar}")
    
    # Vis timebasert aktivitet for i dag
    print("\n" + "-" * 70)
    print("📈 AKTIVITET I DAG (per time)")
    print("-" * 70)
    
    today = datetime.now().strftime("%Y-%m-%d")
    hourly_data = group_by_hour(measurements)
    
    today_hours = {k: v for k, v in hourly_data.items() if k.startswith(today)}
    
    if today_hours:
        max_hourly = max(today_hours.values()) or 1
        
        for hour in sorted(today_hours.keys()):
            time_label = hour.split()[1][:5]
            value = today_hours[hour]
            bar = format_bar(value, max_hourly, 40)
            print(f"  {time_label}  {value:>5.1f} {bar}")
    else:
        print("  Ingen data for i dag ennå.")
    
    # Statistikk
    print("\n" + "-" * 70)
    print("📉 STATISTIKK")
    print("-" * 70)
    
    all_cph = [m["clients_per_hour"] for m in measurements]
    all_active = [m.get("active_clients", 0) for m in measurements]
    
    print(f"  Målinger totalt:      {len(measurements)}")
    print(f"  Gjennomsnitt CPH:     {sum(all_cph)/len(all_cph):.1f}")
    print(f"  Maks CPH:             {max(all_cph)}")
    print(f"  Min CPH:              {min(all_cph)}")
    if all_active and max(all_active) > 0:
        print(f"  Aktive klienter (nå): {all_active[-1]}")
    
    print("=" * 70 + "\n")

def print_html_graph(history):
    """Generer HTML fil med interaktiv graf"""
    measurements = history.get("measurements", [])
    
    html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_activity_graph.html")
    
    # Forbered data for Chart.js
    labels = []
    cph_data = []
    active_data = []
    
    for m in measurements:
        dt = datetime.fromisoformat(m["datetime"])
        labels.append(dt.strftime("%d/%m %H:%M"))
        cph_data.append(m["clients_per_hour"])
        active_data.append(m.get("active_clients", 0))
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MunkiReport Client Activity - 7 dager</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; flex: 1; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .chart-container {{ position: relative; height: 400px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Client Activity - Siste 7 dager</h1>
        <p>Generert: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{cph_data[-1] if cph_data else 0}</div>
                <div class="stat-label">Clients per hour (nå)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{active_data[-1] if active_data else 0}</div>
                <div class="stat-label">Aktive klienter</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{max(cph_data) if cph_data else 0}</div>
                <div class="stat-label">Maks CPH (7d)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(cph_data)//len(cph_data) if cph_data else 0}</div>
                <div class="stat-label">Snitt CPH</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="activityChart"></canvas>
        </div>
    </div>
    
    <script>
        const ctx = document.getElementById('activityChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [
                    {{
                        label: 'Clients per hour',
                        data: {json.dumps(cph_data)},
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: true,
                        tension: 0.3
                    }},
                    {{
                        label: 'Aktive klienter',
                        data: {json.dumps(active_data)},
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.3,
                        hidden: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'MunkiReport Client Activity'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    with open(html_file, 'w') as f:
        f.write(html)
    
    print(f"HTML graf lagret: {html_file}")
    return html_file

def main():
    history = load_history()
    
    # Vis ASCII graf i terminal
    print_7day_graph(history)
    
    # Generer HTML graf
    html_file = print_html_graph(history)
    
    # Åpne i nettleser hvis ønskelig
    if len(sys.argv) > 1 and sys.argv[1] == "--open":
        import webbrowser
        webbrowser.open(f"file://{html_file}")

if __name__ == "__main__":
    main()
