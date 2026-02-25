#!/usr/bin/env /Users/gaute/scripts/mr_api2/.venv/bin/python
"""
Thermal Pressure Monitor
Runs every 15 minutes to check for machines with non-nominal thermal pressure
and analyzes their usage stats with Copilot CLI
"""

import requests
import subprocess
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class ThermalMonitor:
    def __init__(self):
        # Load configuration
        config_file = "/Users/gaute/scripts/mr_api2/thermal_config.json"
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.base_url = config["base_url"]
            self.login = config["login"] 
            self.password = config["password"]
            self.output_dir = Path(config["output_dir"])
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            # Fallback to keychain method
            print(f"Config file error: {e}, falling back to keychain")
            self.base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
            self.login = "localuser"
            self.password = self._get_password()
            self.output_dir = Path("/tmp/usage_stats")
            
        self.session = requests.Session()
        self.session.verify = False
        self.output_dir.mkdir(exist_ok=True)
        
    def _get_password(self) -> str:
        """Get password from keychain"""
        try:
            return subprocess.check_output([
                'security', 'find-generic-password', 
                '-a', 'localuser', 
                '-s', 'munkireport-api', 
                '-w'
            ]).decode().strip()
        except subprocess.CalledProcessError:
            raise Exception("Could not retrieve password from keychain")
    
    def _authenticate(self) -> bool:
        """Authenticate with MunkiReport API"""
        auth_url = f"{self.base_url}/auth/login"
        try:
            auth_request = self.session.post(auth_url, data={
                "login": self.login, 
                "password": self.password
            })
            return auth_request.status_code == 200
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def check_thermal_pressure(self) -> List[Dict[str, Any]]:
        """Check for machines with non-nominal thermal pressure"""
        if not self._authenticate():
            return []
        
        query_url = f"{self.base_url}/datatables/data"
        headers = {"x-csrf-token": self.session.cookies.get("CSRF-TOKEN", "")}
        
        # Query for thermal pressure and basic machine info
        thermal_columns = [
            "machine.serial_number",
            "machine.hostname", 
            "usage_stats.thermal_pressure",
            "usage_stats.timestamp"
        ]
        
        query_data = {f"columns[{i}][name]": c for i, c in enumerate(thermal_columns)}
        
        try:
            response = self.session.post(query_url, data=query_data, headers=headers)
            result = response.json()
            
            if "error" in result:
                print(f"Query error: {result['error']}")
                return []
            
            # Filter for non-nominal thermal pressure
            non_nominal_machines = []
            for row in result.get('data', []):
                if len(row) >= 3 and row[2] and str(row[2]).strip().lower() != 'nominal':
                    non_nominal_machines.append({
                        'serial_number': row[0],
                        'hostname': row[1], 
                        'thermal_pressure': row[2],
                        'timestamp': row[3]
                    })
            
            return non_nominal_machines
            
        except Exception as e:
            print(f"Error checking thermal pressure: {e}")
            return []
    
    def get_full_usage_stats(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """Get complete usage stats for a specific machine"""
        if not self._authenticate():
            return None
            
        query_url = f"{self.base_url}/datatables/data"
        headers = {"x-csrf-token": self.session.cookies.get("CSRF-TOKEN", "")}
        
        # Full usage stats columns (based on your existing script)
        columns = [
            "machine.serial_number",
            "machine.hostname",
            "usage_stats.timestamp",
            "usage_stats.thermal_pressure",
            "usage_stats.package_watts",
            "usage_stats.gpu_busy",
            "usage_stats.gpu_freq_mhz",
            "usage_stats.backlight",
            "usage_stats.keyboard_backlight",
            "usage_stats.ibyte_rate",
            "usage_stats.obyte_rate",
            "usage_stats.rbytes_per_s",
            "usage_stats.wbytes_per_s",
            "usage_stats.rops_per_s",
            "usage_stats.wops_per_s",
            "usage_stats.freq_hz",
            "usage_stats.freq_ratio",
            "usage_stats.cpu_idle",
            "usage_stats.cpu_sys",
            "usage_stats.cpu_user",
            "usage_stats.load_avg",
        ]
        
        query_data = {f"columns[{i}][name]": c for i, c in enumerate(columns)}
        
        try:
            response = self.session.post(query_url, data=query_data, headers=headers)
            result = response.json()
            
            if "error" in result:
                print(f"Query error: {result['error']}")
                return None
            
            # Find the machine with matching serial number
            for row in result.get('data', []):
                if len(row) >= 1 and row[0] == serial_number:
                    return self._parse_usage_stats_row(row)
            
            return None
            
        except Exception as e:
            print(f"Error getting usage stats for {serial_number}: {e}")
            return None
    
    def _parse_usage_stats_row(self, row: List[Any]) -> Dict[str, Any]:
        """Parse a usage stats row into structured data"""
        try:
            # Parse load average
            load_avg = None
            if len(row) > 20 and row[20]:
                load_parts = str(row[20]).split(',')
                if len(load_parts) >= 3:
                    load_avg = {
                        "1min": float(load_parts[0].strip()),
                        "5min": float(load_parts[1].strip()),
                        "15min": float(load_parts[2].strip()),
                        "raw": row[20]
                    }
            
            # Parse CPU percentages
            def parse_cpu_percent(val):
                if val is None:
                    return None
                try:
                    return float(str(val).replace('%', '').strip())
                except (ValueError, AttributeError):
                    return None
            
            return {
                "machine": {
                    "serial_number": row[0],
                    "hostname": row[1] if len(row) > 1 else None
                },
                "usage_stats": {
                    "timestamp": row[2] if len(row) > 2 else None,
                    "thermal_pressure": row[3] if len(row) > 3 else None,
                    "package_watts": row[4] if len(row) > 4 else None,
                    "gpu_busy": row[5] if len(row) > 5 else None,
                    "gpu_freq_mhz": row[6] if len(row) > 6 else None,
                    "backlight": row[7] if len(row) > 7 else None,
                    "keyboard_backlight": row[8] if len(row) > 8 else None,
                    "ibyte_rate": row[9] if len(row) > 9 else None,
                    "obyte_rate": row[10] if len(row) > 10 else None,
                    "rbytes_per_s": row[11] if len(row) > 11 else None,
                    "wbytes_per_s": row[12] if len(row) > 12 else None,
                    "rops_per_s": row[13] if len(row) > 13 else None,
                    "wops_per_s": row[14] if len(row) > 14 else None,
                    "freq_hz": row[15] if len(row) > 15 else None,
                    "freq_ratio": row[16] if len(row) > 16 else None,
                    "cpu_idle": parse_cpu_percent(row[17]) if len(row) > 17 else None,
                    "cpu_sys": parse_cpu_percent(row[18]) if len(row) > 18 else None,
                    "cpu_user": parse_cpu_percent(row[19]) if len(row) > 19 else None,
                    "load_avg": load_avg,
                },
                "collected_at": datetime.now().isoformat(),
                "raw_data": row
            }
        except Exception as e:
            print(f"Error parsing usage stats row: {e}")
            return None
    
    def format_for_copilot(self, data: Dict[str, Any]) -> str:
        """Format usage stats data for Copilot analysis (similar to your existing format)"""
        machine = data.get("machine", {})
        stats = data.get("usage_stats", {})
        
        # Calculate timestamp from epoch if available
        timestamp_str = "Unknown"
        if stats.get("timestamp"):
            try:
                timestamp_str = datetime.fromtimestamp(int(stats["timestamp"])).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                timestamp_str = str(stats["timestamp"])
        
        # Calculate CPU total usage
        cpu_idle = stats.get("cpu_idle", 0) or 0
        cpu_total_usage = 100 - cpu_idle if cpu_idle else None
        
        formatted = f"""MACHINE_ANALYSIS_DATA
host={machine.get('hostname', 'Unknown')}
serial={machine.get('serial_number', 'Unknown')}
collected_at={data.get('collected_at', 'Unknown')}
data_timestamp={timestamp_str}

PERFORMANCE_STATUS
thermal_pressure={stats.get('thermal_pressure', 'Unknown')}"""

        # Add load average if available
        load_avg = stats.get("load_avg")
        if load_avg:
            formatted += f"""
load_avg_1min={load_avg.get('1min', 'N/A')}
load_avg_5min={load_avg.get('5min', 'N/A')} 
load_avg_15min={load_avg.get('15min', 'N/A')}"""

        # CPU utilization
        formatted += f"""

CPU_UTILIZATION
cpu_idle_percent={stats.get('cpu_idle', 'N/A')}
cpu_system_percent={stats.get('cpu_sys', 'N/A')}
cpu_user_percent={stats.get('cpu_user', 'N/A')}"""
        
        if cpu_total_usage is not None:
            formatted += f"""
cpu_total_usage_percent={cpu_total_usage:.2f}"""

        # Disk I/O
        formatted += f"""

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
    
    def analyze_with_copilot(self, formatted_data: str, machine_info: Dict[str, str]) -> Optional[str]:
        """Use Copilot CLI to analyze the machine data"""
        hostname = machine_info.get('hostname', 'Unknown')
        thermal_pressure = machine_info.get('thermal_pressure', 'Unknown')
        
        try:
            # Create the full prompt
            full_prompt = f"Analyser følgende maskin som har thermal_pressure='{thermal_pressure}' (ikke Nominal) og skriv: 1) Kort resymé, er maskinen under belastning? (maks 5 linjer) 2) Mest sannsynlig årsak (1–3 punkt) 3) Svar som ren tekst, start med SUMMARY:\n\n{formatted_data}"
            
            # Use Copilot CLI with echo and -s flag
            result = subprocess.run([
                'bash', '-c', f'echo "{full_prompt.replace('"', '\"')}" | /opt/homebrew/bin/copilot -s'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Copilot CLI error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Copilot CLI timed out")
            return None
        except FileNotFoundError:
            print("Copilot CLI not found at /opt/homebrew/bin/copilot")
            return None
        except Exception as e:
            print(f"Error running Copilot CLI: {e}")
            return None
    
    def save_analysis(self, machine_info: Dict[str, str], analysis: str, formatted_data: str):
        """Save the analysis to a file in /tmp/usage_stats/"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hostname = machine_info.get('hostname', 'unknown')
        serial = machine_info.get('serial_number', 'unknown')
        
        filename = f"thermal_analysis_{hostname}_{serial}_{timestamp}.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(f"THERMAL PRESSURE ANALYSIS\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Host: {hostname}\n")
            f.write(f"Serial: {serial}\n")
            f.write(f"Thermal Pressure: {machine_info.get('thermal_pressure', 'Unknown')}\n")
            f.write("=" * 80 + "\n\n")
            f.write("COPILOT ANALYSIS:\n")
            f.write(analysis + "\n\n")
            f.write("=" * 80 + "\n")
            f.write("RAW DATA:\n")
            f.write(formatted_data)
        
        print(f"Analysis saved to: {filepath}")
    
    def run(self):
        """Main monitoring loop"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for thermal pressure issues...")
        
        # Check for machines with non-nominal thermal pressure
        problem_machines = self.check_thermal_pressure()
        
        if not problem_machines:
            print("No machines found with thermal pressure issues.")
            return
        
        print(f"Found {len(problem_machines)} machine(s) with thermal pressure issues:")
        for machine in problem_machines:
            print(f"  - {machine['hostname']} ({machine['serial_number']}): {machine['thermal_pressure']}")
        
        # Analyze each problematic machine
        for machine_info in problem_machines:
            serial = machine_info['serial_number']
            hostname = machine_info['hostname']
            
            print(f"\nAnalyzing {hostname} ({serial})...")
            
            # Get full usage stats
            usage_data = self.get_full_usage_stats(serial)
            if not usage_data:
                print(f"Could not get usage stats for {hostname}")
                continue
            
            # Format for Copilot
            formatted_data = self.format_for_copilot(usage_data)
            
            # Analyze with Copilot CLI
            analysis = self.analyze_with_copilot(formatted_data, machine_info)
            if analysis:
                self.save_analysis(machine_info, analysis, formatted_data)
                print(f"Analysis completed for {hostname}")
            else:
                print(f"Could not analyze {hostname} with Copilot CLI")

def main():
    try:
        monitor = ThermalMonitor()
        monitor.run()
    except Exception as e:
        print(f"Error running thermal monitor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()