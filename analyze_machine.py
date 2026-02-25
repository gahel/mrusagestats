#!/usr/bin/env /Users/gaute/scripts/mr_api2/.venv/bin/python
"""
Analyze single machine usage stats with Copilot
Usage: ./analyze_machine.py [serial_number|hostname]
"""

import requests
import subprocess
import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class MachineAnalyzer:
    def __init__(self):
        self.base_url = "https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?"
        self.login = "localuser"
        self.password = self._get_password()
        self.session = requests.Session()
        self.session.verify = False
        self.output_dir = Path("/tmp/usage_stats")
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
    
    def get_machine_usage_stats(self, machine_identifier: str) -> Optional[Dict[str, Any]]:
        """Get complete usage stats for a specific machine by serial or hostname"""
        if not self._authenticate():
            return None
            
        query_url = f"{self.base_url}/datatables/data"
        headers = {"x-csrf-token": self.session.cookies.get("CSRF-TOKEN", "")}
        
        # Full usage stats columns
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
            
            # Find the machine with matching serial number or hostname
            for row in result.get('data', []):
                if len(row) >= 2:
                    serial = str(row[0]) if row[0] else ""
                    hostname = str(row[1]) if row[1] else ""
                    
                    if (machine_identifier.lower() == serial.lower() or 
                        machine_identifier.lower() == hostname.lower()):
                        return self._parse_usage_stats_row(row)
            
            print(f"Machine '{machine_identifier}' not found")
            return None
            
        except Exception as e:
            print(f"Error getting usage stats for {machine_identifier}: {e}")
            return None
    
    def _parse_usage_stats_row(self, row) -> Dict[str, Any]:
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
    
    def format_for_ai(self, data: Dict[str, Any]) -> str:
        """Format usage stats data for AI analysis (like your _ai.txt files)"""
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
    
    def analyze_with_copilot(self, formatted_data: str, machine_name: str) -> Optional[str]:
        """Use Copilot CLI to analyze the machine data"""
        prompt = f"Analyser følgende maskin ({machine_name}) og skriv: 1) Kort resymé, er maskinen under belastning? (maks 5 linjer) 2) Mest sannsynlig årsak (1–3 punkt) 3) Svar som ren tekst, start med SUMMARY:\\n\\n{formatted_data}"
        
        try:
            # Use Copilot CLI with echo and -s flag
            result = subprocess.run([
                'bash', '-c', f'echo "{prompt.replace('"', '\\"')}" | /opt/homebrew/bin/copilot -s'
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
    
    def save_analysis(self, machine_data: Dict[str, Any], analysis: str, formatted_data: str):
        """Save the analysis to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hostname = machine_data["machine"].get('hostname', 'unknown')
        serial = machine_data["machine"].get('serial_number', 'unknown')
        
        # Save AI-formatted data file (like your _ai.txt files)
        ai_filename = f"machine_{hostname}_{timestamp}_ai.txt"
        ai_filepath = self.output_dir / ai_filename
        
        with open(ai_filepath, 'w') as f:
            f.write(formatted_data)
        
        print(f"AI-formatted data saved to: {ai_filepath}")
        
        # Save full analysis with Copilot response
        analysis_filename = f"machine_{hostname}_{timestamp}_analysis.txt"
        analysis_filepath = self.output_dir / analysis_filename
        
        with open(analysis_filepath, 'w') as f:
            f.write(f"MACHINE ANALYSIS\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Host: {hostname}\n")
            f.write(f"Serial: {serial}\n")
            f.write("=" * 80 + "\n\n")
            f.write("COPILOT ANALYSIS:\n")
            f.write(analysis + "\n\n")
            f.write("=" * 80 + "\n")
            f.write("RAW DATA:\n")
            f.write(formatted_data)
        
        print(f"Full analysis saved to: {analysis_filepath}")
        
        # Also save JSON data for reference
        json_filename = f"machine_{hostname}_{timestamp}.json"
        json_filepath = self.output_dir / json_filename
        
        with open(json_filepath, 'w') as f:
            json.dump(machine_data, f, indent=2)
        
        print(f"JSON data saved to: {json_filepath}")
    
    def analyze_machine(self, machine_identifier: str):
        """Main function to analyze a machine"""
        print(f"Analyzing machine: {machine_identifier}")
        
        # Get usage stats
        usage_data = self.get_machine_usage_stats(machine_identifier)
        if not usage_data:
            print(f"Could not get usage stats for {machine_identifier}")
            return
        
        hostname = usage_data["machine"].get("hostname", "unknown")
        print(f"Found machine: {hostname}")
        
        # Format for AI analysis
        formatted_data = self.format_for_ai(usage_data)
        
        # Analyze with Copilot CLI
        print("Running Copilot analysis...")
        analysis = self.analyze_with_copilot(formatted_data, hostname)
        
        if analysis:
            print("\n" + "="*80)
            print("COPILOT ANALYSIS:")
            print("="*80)
            print(analysis)
            print("="*80)
            
            # Save all files
            self.save_analysis(usage_data, analysis, formatted_data)
        else:
            print("Could not get analysis from Copilot CLI")
            # Still save the formatted data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ai_filename = f"machine_{hostname}_{timestamp}_ai.txt"
            ai_filepath = self.output_dir / ai_filename
            
            with open(ai_filepath, 'w') as f:
                f.write(formatted_data)
            
            print(f"AI-formatted data saved to: {ai_filepath}")

def main():
    parser = argparse.ArgumentParser(description='Analyze machine usage stats with Copilot')
    parser.add_argument('machine', help='Machine serial number or hostname')
    args = parser.parse_args()
    
    try:
        analyzer = MachineAnalyzer()
        analyzer.analyze_machine(args.machine)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()