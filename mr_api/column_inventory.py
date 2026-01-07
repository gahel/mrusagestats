#!/usr/bin/env python3
"""
Complete inventory of available columns found in MunkiReport API
"""

available_columns = {
    "machine": [
        "machine.serial_number",
        "machine.hostname",
        "machine.machine_desc",
        "machine.os_version",
    ],
    
    "reportdata": [
        "reportdata.serial_number",
        "reportdata.timestamp",
        "reportdata.console_user",
        "reportdata.remote_ip",
        "reportdata.machine_group",
        "reportdata.archive_status",
        "reportdata.uptime",
    ],
    
    "munkireport": [
        "munkireport.manifestname",
    ],
    
    "usage_stats": [
        "usage_stats.serial_number",
        "usage_stats.timestamp",
        "usage_stats.thermal_pressure",
    ],
    
    "managedinstalls": [
        "managedinstalls.serial_number",
        "managedinstalls.size",
    ],
    
    "security": [
        "security.serial_number",
    ],
    
    "report_items_with_serial_only": [
        "applications.serial_number",
        "appusage.serial_number",
        "ard.serial_number",
        "bluetooth.serial_number",
        "certificate.serial_number",
        "detectx.serial_number",
        "extensions.serial_number",
        "fan_temps.serial_number",
        "filevault_status.serial_number",
        "findmymac.serial_number",
        "firewall.serial_number",
        "fonts.serial_number",
        "gpu.serial_number",
        "mdm_status.serial_number",
        "munki_facts.serial_number",
        "munkiinfo.serial_number",
        "network.serial_number",
        "network_shares.serial_number",
        "power.serial_number",
        "printer.serial_number",
        "profile.serial_number",
        "softwareupdate.serial_number",
        "sophos.serial_number",
        "timemachine.serial_number",
        "usb.serial_number",
        "user_sessions.serial_number",
        "warranty.serial_number",
        "wifi.serial_number",
    ]
}

# Print summary
print("=" * 80)
print("MUNKIREPORT API - AVAILABLE COLUMNS INVENTORY")
print("=" * 80)
print()

total_columns = 0
for table, cols in available_columns.items():
    if table != "report_items_with_serial_only":
        print(f"{table.upper()}:")
        for col in cols:
            print(f"  ✓ {col}")
        print()
        total_columns += len(cols)

print("REPORT ITEMS (with serial_number only):")
print(f"  {len(available_columns['report_items_with_serial_only'])} tables available")
for col in available_columns['report_items_with_serial_only']:
    print(f"    - {col}")

total_columns += len(available_columns['report_items_with_serial_only'])

print()
print("=" * 80)
print(f"TOTAL: {total_columns} columns found")
print("=" * 80)

# Show recommended queries
print()
print("RECOMMENDED QUERIES:")
print()
print("1. Basic machine info + thermal status:")
print("   machine.serial_number, machine.hostname, machine.machine_desc,")
print("   reportdata.console_user, usage_stats.thermal_pressure, usage_stats.timestamp")
print()
print("2. System health check:")
print("   machine.serial_number, machine.hostname, reportdata.timestamp,")
print("   reportdata.uptime, usage_stats.thermal_pressure")
print()
print("3. Security status:")
print("   machine.serial_number, machine.hostname, security.serial_number")
print()
print("NOTE: Disk space data (free/used/available) not found in API")
print("      Available from web UI report: 1 machine < 100GB, 107 machines > 10GB")
