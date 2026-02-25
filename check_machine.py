#!/usr/bin/env python3
"""
Check specific machine status - MBP-28552
"""
import json
from datetime import datetime

def main():
    target_machine = "MBP-28552"
    
    try:
        # Load latest data
        with open('get_data_20260113_105516.json', 'r') as f:
            data = json.load(f)
        
        machines_data = data.get('data', [])
        
        print(f"🔍 SEARCHING FOR: {target_machine}")
        print("=" * 50)
        
        found = False
        for row in machines_data:
            hostname = row[1] if len(row) > 1 else 'Unknown'
            if target_machine in hostname:
                found = True
                serial_number = row[0]
                machine_desc = row[2] 
                timestamp = row[3]
                console_user = row[8]
                long_username = row[9]
                thermal_pressure = row[17] if len(row) > 17 else 'Unknown'
                cpu_idle = row[18] if len(row) > 18 else 'Unknown'
                cpu_sys = row[19] if len(row) > 19 else 'Unknown'
                cpu_user = row[20] if len(row) > 20 else 'Unknown'
                load_avg = row[21] if len(row) > 21 else 'Unknown'
                
                check_in_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                hours_ago = (datetime.now().timestamp() - timestamp) / 3600
                
                print(f"✅ FOUND: {hostname} ({serial_number})")
                print(f"📱 Model: {machine_desc}")
                print(f"👤 User: {long_username} ({console_user})")
                print(f"📅 Last check-in: {check_in_time} ({hours_ago:.1f} hours ago)")
                print()
                print("🌡️  THERMAL STATUS:")
                print(f"   Thermal Pressure: {thermal_pressure}")
                
                # Analyze thermal status
                if thermal_pressure == "Nominal":
                    print("   Status: ✅ Normal - No thermal issues detected")
                elif isinstance(thermal_pressure, str) and "%" in thermal_pressure:
                    try:
                        pressure_val = float(thermal_pressure.replace('%', ''))
                        if pressure_val > 90:
                            print("   Status: 🔴 CRITICAL - Very high thermal pressure!")
                        elif pressure_val > 75:
                            print("   Status: 🟡 WARNING - High thermal pressure")
                        else:
                            print("   Status: ✅ Normal thermal pressure")
                    except ValueError:
                        print(f"   Status: ❓ Unknown thermal pressure format: {thermal_pressure}")
                else:
                    print(f"   Status: ❓ Unknown thermal status: {thermal_pressure}")
                
                print()
                print("💻 CPU PERFORMANCE:")
                print(f"   CPU User: {cpu_user}")
                print(f"   CPU System: {cpu_sys}")
                print(f"   CPU Idle: {cpu_idle}")
                print()
                print("⚡ LOAD AVERAGE:")
                print(f"   Load: {load_avg}")
                
                # Parse load average for analysis
                if load_avg and load_avg != 'Unknown':
                    try:
                        load_1min = float(str(load_avg).split(',')[0].strip())
                        print(f"   1-minute load: {load_1min:.2f}")
                        
                        if load_1min > 20:
                            print("   Status: 🔴 HIGH LOAD - System under heavy stress")
                        elif load_1min > 10:
                            print("   Status: 🟡 MODERATE LOAD - System busy")
                        else:
                            print("   Status: ✅ Normal load")
                    except (ValueError, IndexError):
                        print("   Status: ❓ Unable to parse load average")
                
                # Recommendations
                print()
                print("💡 RECOMMENDATIONS:")
                if thermal_pressure != "Nominal":
                    print("   • Monitor thermal pressure - consider reducing workload")
                    print("   • Check for dust buildup in vents")
                    print("   • Ensure proper ventilation around device")
                    print("   • Consider closing resource-intensive applications")
                else:
                    print("   • Thermal status is normal - no immediate action needed")
                
                break
        
        if not found:
            print(f"❌ Machine {target_machine} not found in current dataset")
            print("   • Check if machine hostname is correct")
            print("   • Machine may not have checked in recently")
            print("   • Try searching for similar hostnames")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()