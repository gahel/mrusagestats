#!/usr/bin/env /Users/gaute/scripts/mr_api2/.venv/bin/python
"""
Test script for thermal monitor with simulated thermal pressure issue
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

# Simulated data from a machine with thermal pressure issues
test_data = {
    "machine": {
        "serial_number": "TEST12345",
        "hostname": "TestMBP"
    },
    "usage_stats": {
        "timestamp": 1764245707,
        "thermal_pressure": "Heavy",
        "package_watts": 28.5,
        "gpu_busy": 85.2,
        "gpu_freq_mhz": 1200,
        "backlight": 255,
        "keyboard_backlight": 255,
        "ibyte_rate": 5000000,
        "obyte_rate": 2000000,
        "rbytes_per_s": 150000000,
        "wbytes_per_s": 75000000,
        "rops_per_s": 8500,
        "wops_per_s": 3200,
        "freq_hz": 2800000000,
        "freq_ratio": 0.95,
        "cpu_idle": 5.2,
        "cpu_sys": 45.8,
        "cpu_user": 49.0,
        "load_avg": {
            "1min": 8.5,
            "5min": 7.2,
            "15min": 6.8,
            "raw": "8.5, 7.2, 6.8"
        }
    },
    "collected_at": datetime.now().isoformat(),
}

def format_for_copilot(data):
    """Format usage stats data for Copilot analysis"""
    machine = data.get("machine", {})
    stats = data.get("usage_stats", {})
    
    timestamp_str = datetime.fromtimestamp(int(stats["timestamp"])).strftime('%Y-%m-%d %H:%M:%S')
    cpu_idle = stats.get("cpu_idle", 0) or 0
    cpu_total_usage = 100 - cpu_idle
    
    formatted = f"""MACHINE_ANALYSIS_DATA
host={machine.get('hostname', 'Unknown')}
serial={machine.get('serial_number', 'Unknown')}
collected_at={data.get('collected_at', 'Unknown')}
data_timestamp={timestamp_str}

PERFORMANCE_STATUS
thermal_pressure={stats.get('thermal_pressure', 'Unknown')}
load_avg_1min={stats["load_avg"]["1min"]}
load_avg_5min={stats["load_avg"]["5min"]} 
load_avg_15min={stats["load_avg"]["15min"]}

CPU_UTILIZATION
cpu_idle_percent={stats.get('cpu_idle', 'N/A')}
cpu_system_percent={stats.get('cpu_sys', 'N/A')}
cpu_user_percent={stats.get('cpu_user', 'N/A')}
cpu_total_usage_percent={cpu_total_usage:.2f}

DISK_IO
disk_read_bytes_per_sec={stats.get('rbytes_per_s', 'N/A')}
disk_write_bytes_per_sec={stats.get('wbytes_per_s', 'N/A')}
disk_read_ops_per_sec={stats.get('rops_per_s', 'N/A')}
disk_write_ops_per_sec={stats.get('wops_per_s', 'N/A')}

NETWORK_IO
network_inbound_bytes_per_sec={stats.get('ibyte_rate', 'N/A')}
network_outbound_bytes_per_sec={stats.get('obyte_rate', 'N/A')}

GPU_PERFORMANCE
gpu_utilization_percent={stats.get('gpu_busy', 'N/A')}
gpu_frequency_mhz={stats.get('gpu_freq_mhz', 'N/A')}

POWER_MANAGEMENT
power_consumption_watts={stats.get('package_watts', 'N/A')}
cpu_frequency_hz={stats.get('freq_hz', 'None')}
cpu_frequency_ratio={stats.get('freq_ratio', 'None')}

DISPLAY
screen_backlight={stats.get('backlight', 'N/A')}
keyboard_backlight={stats.get('keyboard_backlight', 'N/A')}
"""
    return formatted

def analyze_with_copilot(formatted_data):
    """Use Copilot CLI to analyze the machine data"""
    prompt = f"""Analyser følgende maskin som har thermal_pressure='Heavy' (ikke Nominal):

{formatted_data}

Gi en kort analyse (max 200 ord) som inkluderer:
1. Mulige årsaker til thermal pressure problemet
2. Hvilke metrikker som indikerer belastning 
3. Anbefalte tiltak for å redusere termisk belastning

Fokuser på de mest kritiske funnene og praktiske løsninger."""
    
    try:
        # Create the full prompt
        full_prompt = f"Analyser følgende maskin som har thermal_pressure='Heavy' (ikke Nominal) og skriv: 1) Kort resymé, er maskinen under belastning? (maks 5 linjer) 2) Mest sannsynlig årsak (1–3 punkt) 3) Svar som ren tekst, start med SUMMARY:\n\n{formatted_data}"
        
        # Use Copilot CLI with echo and -s flag
        result = subprocess.run([
            'bash', '-c', f'echo "{full_prompt.replace('"', '\"')}" | /opt/homebrew/bin/copilot -s'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Copilot CLI error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error running Copilot CLI: {e}")
        return None

def main():
    print("🔥 Testing thermal monitor with simulated Heavy thermal pressure...")
    
    # Format data for Copilot
    formatted_data = format_for_copilot(test_data)
    print("\n📊 Formatted data:")
    print(formatted_data)
    
    # Analyze with Copilot
    print("\n🤖 Running Copilot analysis...")
    analysis = analyze_with_copilot(formatted_data)
    
    if analysis:
        print("\n✅ Copilot Analysis:")
        print("=" * 80)
        print(analysis)
        print("=" * 80)
        
        # Save to file
        output_dir = Path("/tmp/usage_stats")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_thermal_analysis_{timestamp}.txt"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(f"TEST THERMAL PRESSURE ANALYSIS\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Host: TestMBP\n")
            f.write(f"Serial: TEST12345\n")
            f.write(f"Thermal Pressure: Heavy\n")
            f.write("=" * 80 + "\n\n")
            f.write("COPILOT ANALYSIS:\n")
            f.write(analysis + "\n\n")
            f.write("=" * 80 + "\n")
            f.write("RAW DATA:\n")
            f.write(formatted_data)
        
        print(f"\n📁 Test analysis saved to: {filepath}")
    else:
        print("\n❌ Could not get analysis from Copilot CLI")

if __name__ == "__main__":
    main()