#!/bin/bash
#
# Script to show hostnames of machines less than 7 days old
# Uses get_data.sh and jq to filter by timestamp

# Run get_data.sh to get current data
echo "Fetching machine data..." >&2

bash get_data.sh > /tmp/machines_data.json 2>/dev/null

# Calculate timestamp for 7 days ago (Unix timestamp)
SEVEN_DAYS_AGO=$(date -v-7d +%s)
NOW=$(date +%s)

echo "Machines added in the last 7 days (since $(date -v-7d '+%Y-%m-%d')):" >&2
echo "================================================" >&2

# Use jq to filter machines and extract hostnames
# Index 3 is reportdata.timestamp, index 1 is hostname
jq -r ".data[] | 
  select(.[3] != null and (.[3] | tonumber) > $SEVEN_DAYS_AGO) | 
  {hostname: .[1], timestamp: .[3]}" /tmp/machines_data.json | \
jq -r -s 'sort_by(.timestamp) | reverse | .[] | 
  "\(.hostname) (\(.timestamp))"' | \
while read -r line; do
  hostname=$(echo "$line" | cut -d' ' -f1)
  timestamp=$(echo "$line" | sed 's/.*(\([0-9]*\)).*/\1/')
  
  # Parse timestamp to human readable date (macOS compatible)
  added_date=$(date -f "%s" "$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown")
  age_seconds=$((NOW - timestamp))
  age_days=$((age_seconds / 86400))
  
  printf "  %s (added %d days ago on %s)\n" "$hostname" "$age_days" "$added_date"
done

rm -f /tmp/machines_data.json
