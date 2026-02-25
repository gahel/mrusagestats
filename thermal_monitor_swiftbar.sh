#!/bin/bash
# thermal_monitor_swiftbar.sh - SwiftBar plugin for thermal monitoring
# Refresh every 5 minutes
# <bitbar.title>Thermal Monitor</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Gaute</bitbar.author>
# <bitbar.author.github>gahel</bitbar.author.github>
# <bitbar.desc>Monitor thermal pressure on MunkiReport machines</bitbar.desc>
# <bitbar.dependencies>jq</bitbar.dependencies>

set -e

# Configuration
DATA_FILE="/Users/gaute/scripts/mr_api2/get_data_20260113_105516.json"
ANALYZE_SCRIPT="/Users/gaute/scripts/mr_api2/analyze_thermal_issues.sh"

# Check if data file exists
if [ ! -f "$DATA_FILE" ]; then
    echo "⚠️ No data | color=red"
    echo "---"
    echo "Data file not found"
    exit 0
fi

# Parse thermal pressure data
thermal_issues=$(jq -r '
.data[] | 
select(.[17] != "Nominal" and .[17] != null) | 
[.[0], .[1], .[17]] | 
@csv
' "$DATA_FILE" 2>/dev/null)

# Count issues
issue_count=$(echo "$thermal_issues" | grep -v '^$' | wc -l | tr -d ' ')

# Main menu bar display
if [ "$issue_count" -eq 0 ]; then
    echo "🌡️ OK"
else
    echo "🔥 $issue_count | color=red"
fi

echo "---"

if [ "$issue_count" -eq 0 ]; then
    echo "✅ No thermal issues detected"
    echo "All machines reporting normal thermal pressure"
else
    echo "🚨 Machines with thermal issues:"
    echo "---"
    
    # Track machines for batch analysis
    machine_list=""
    
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            # Parse CSV line (serial, hostname, thermal_pressure)
            serial=$(echo "$line" | cut -d, -f1 | tr -d '"')
            hostname=$(echo "$line" | cut -d, -f2 | tr -d '"')
            thermal=$(echo "$line" | cut -d, -f3 | tr -d '"')
            
            # Add to machine list for batch analysis
            if [ -n "$machine_list" ]; then
                machine_list="$machine_list $hostname"
            else
                machine_list="$hostname"
            fi
            
            # Individual machine analysis
            echo "🔥 $hostname | color=red"
            echo "  Serial: $serial"
            echo "  Thermal: $thermal"
            echo "  Analyze $hostname | bash='$ANALYZE_SCRIPT' param1='$hostname' terminal=true"
            echo "---"
        fi
    done <<< "$thermal_issues"
    
    # Batch analysis option
    if [ -n "$machine_list" ]; then
        echo "🔍 Analyze ALL thermal issues | bash='$ANALYZE_SCRIPT' param1='$machine_list' terminal=true"
        echo "---"
    fi
fi

echo "---"
echo "🔄 Refresh | refresh=true"
echo "📊 Open MunkiReport | href=https://app-munkireport-prod-norwayeast-001.azurewebsites.net"