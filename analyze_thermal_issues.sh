#!/bin/bash
# analyze_thermal_issues.sh - Opens Terminal and runs analyze_machine.sh for thermal issues
# Usage: ./analyze_thermal_issues.sh "MBP-28552" "MBP-15822"

set -e

# Configuration
SCRIPT_DIR="/Users/gaute/scripts/mr_api2"
SCRIPT_NAME="analyze_machine.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if machines are provided
if [ $# -eq 0 ]; then
    log_error "No machines specified"
    echo "Usage: $0 \"MBP-machine1\" [\"MBP-machine2\" ...]"
    exit 1
fi

# Build the command to run
MACHINES=("$@")
COMMAND="cd '$SCRIPT_DIR' && ./$SCRIPT_NAME"

# Add each machine to the command
for machine in "${MACHINES[@]}"; do
    COMMAND="$COMMAND '$machine'"
done

log_info "Opening Terminal to analyze: ${MACHINES[*]}"

# Create AppleScript to open Terminal and run the command
osascript << EOF
tell application "Terminal"
    activate
    do script "$COMMAND"
end tell
EOF

log_info "Terminal opened with analysis command"