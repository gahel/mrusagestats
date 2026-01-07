# Munki Report Monitoring Agent System

## Overview

This is a complete fleet monitoring system for Munki Report v5 that identifies machines requiring attention based on:
- **Thermal Pressure** - Machines running hot (Heavy thermal pressure)
- **CPU Load** - Machines with high CPU utilization
- **Disk Space** - Machines with low free disk space

## System Architecture

### Core Components

1. **`munki_report.py`** (Main monitoring agent)
   - Fetches machine data from Munki Report API
   - Analyzes thermal pressure, CPU load, disk space status
   - Generates health status report with visual charts
   - Uses session cookie authentication for API access
   - Caches session cookie to ~/.mr_session_cookie for reuse

2. **`agent.py`** (Natural language query interface)
   - Queries cached machine data with natural language
   - Supports questions about thermal, CPU, activity status
   - Example: "Show me machines with high CPU load"

3. **`get_session_cookie.sh`** (Session management)
   - Interactive script to obtain new session cookies from browser
   - Stores PHPSESSID in ~/.mr_session_cookie

4. **`machines.json`** (Data cache)
   - Cached copy of all 107 machines with thermal/CPU/activity data
   - Used by agent.py for queries
   - Updated by munki_report.py after each run

## API Discovery Results

### Available Endpoints

#### 1. Main Datatable API
- **Endpoint**: `/index.php?/datatables/data` (POST)
- **Purpose**: Fetch machine data with specific columns
- **Available Tables**: 
  - `machine` - Serial, hostname, description
  - `reportdata` - User, timestamp
  - `usage_stats` - Thermal pressure, CPU idle %
  - `network` - Network statistics

#### 2. Disk Report Module Stats
- **Endpoint**: `/index.php?/module/disk_report/get_stats` (GET/POST)
- **Response**: JSON with disk space statistics
- **Data**:
  ```json
  {
    "thresholds": {"danger": 5, "warning": 10},
    "stats": {
      "success": 107,   // Machines with >= 10GB free
      "warning": 0,     // Machines with 5-10GB free
      "danger": 0       // Machines with < 5GB free
    }
  }
  ```

#### 3. Disk Report Module Summaries
- `/index.php?/module/disk_report/get_volume_type` - Volume types (APFS, etc.)
- `/index.php?/module/disk_report/get_disk_type` - Disk types (HDD, SSD, etc.)
- `/index.php?/module/disk_report/get_smart_stats` - S.M.A.R.T. status

### Key Finding: No Raw Disk Data via API

After extensive investigation:
- **Disk Report table does NOT exist** in database
- Individual machine disk volume data is NOT accessible via `/datatables/data`
- The Storage Report widget shows "107 machines with 10GB+" based on `get_stats` thresholds
- Actual per-machine disk volumes NOT available through standard API

### Tables That DO NOT Exist
- `disk`, `disk_report`, `storage`, `volumes`, `partition`, `diskspace`, `hdd`

## Current System Status

### Fleet Health Summary
```
Total Machines:     107
Thermal Status:     105 normal (98.1%), 2 heavy (1.9%)
CPU Load Avg:       27.0% (range: 8.5% - 98.1%)
Activity Status:    9 last hour, 29 last day, 61 last week
Disk Space:         ✓ All 107 machines with >= 10GB free
```

### Problem Machines Identified

**High Thermal Pressure (2 machines)**:
1. **XG506M5JYY** (MBP-32692) - User: arn
2. **MY7NY4PWPK** (MBP-09790) - User: live.wang.jensen

**High CPU Load (3 machines)**:
- Machines with >75% CPU utilization

**Status**: All machines have adequate disk space (>= 10GB free)

## Usage

### Run Main Monitoring Agent
```bash
cd /Users/gaute/scripts/mr_api
source .venv/bin/activate
python munki_report.py
```

**Output includes**:
- List of machines with high thermal pressure
- Comprehensive health status dashboard
- Thermal pressure distribution
- CPU load distribution  
- Activity timeline
- Disk space status
- Summary statistics

### Query with Natural Language Agent
```bash
python agent.py
# Example: "Show me machines with heavy thermal pressure"
# Example: "Which machines have >75% CPU load?"
```

### Get New Session Cookie
```bash
./get_session_cookie.sh
```
Follow prompts to extract PHPSESSID from browser cookies.

## API Query Examples

### Get all machines with selected columns
```python
import requests

session = requests.Session()
# Set PHPSESSID cookie from ~/.mr_session_cookie

data = {
    'columns[0][name]': 'machine.serial_number',
    'columns[1][name]': 'machine.hostname',
    'columns[2][name]': 'usage_stats.thermal_pressure',
    'columns[3][name]': 'usage_stats.cpu_idle',
    'draw': 1,
    'length': 107,
    'start': 0,
}

r = session.post(
    'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?/datatables/data',
    data=data,
    verify=False
)

machines = r.json()['data']  # List of 107 machines
```

### Get disk space stats
```python
# Must be authenticated with valid session
r = session.get(
    'https://app-munkireport-prod-norwayeast-001.azurewebsites.net/index.php?/module/disk_report/get_stats',
    verify=False
)

stats = r.json()
# stats['stats']['success'] = 107 (machines with >= 10GB free)
```

## Files in Project

```
mr_api/
├── munki_report.py              # Main monitoring agent
├── agent.py                     # Natural language query interface
├── get_session_cookie.sh        # Session cookie obtainer
├── machines.json                # Cached machine data (107 machines)
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── AGENT_SYSTEM.md              # This file
└── .venv/                       # Python virtual environment
```

## Technical Details

### Authentication
- Uses PHPSESSID session cookie from Munki Report web UI
- Stored in `~/.mr_session_cookie` for reuse
- No direct password authentication via API

### Data Sources
1. `/datatables/data` - Machine inventory & real-time status
2. `/module/disk_report/get_stats` - Fleet-wide disk statistics
3. `/module/disk_report/get_volume_type` - Volume format summary
4. `/module/disk_report/get_smart_stats` - Disk health summary

### Python Environment
- Python 3.14.2
- Libraries: requests, keyring, json, datetime
- Virtual environment: `.venv/`

## Limitations

1. **No Per-Machine Disk Volumes**: Cannot retrieve disk free/total per machine
2. **No SMART Details**: Cannot access detailed S.M.A.R.T. data per drive
3. **Disk Table Missing**: `disk_report` table not populated in database
4. **No Network Status**: Network table exists but not analyzed in current agent

## Future Enhancements

1. **Query individual machine disk data** - Once disk_report table is populated
2. **Automated alerting** - Email/Slack notifications for problem machines
3. **Historical trends** - Track thermal/CPU/disk trends over time
4. **Predictive maintenance** - Identify machines likely to need hardware replacement soon
5. **Performance metrics** - Add network, memory, and I/O metrics

## Troubleshooting

### "Session cookie is expired"
```bash
./get_session_cookie.sh  # Get a new session cookie
```

### "Cannot fetch disk stats"
Ensure session cookie is valid and authenticated:
```bash
cat ~/.mr_session_cookie
```

### "No data returned from API"
Verify the MunkiReport instance is accessible:
```bash
curl -k https://app-munkireport-prod-norwayeast-001.azurewebsites.net/show/dashboard
```

## API Investigation Notes

### Discovery Process
1. Tested `/datatables/data` with 50+ column names
2. Confirmed only 4 tables exist: machine, reportdata, usage_stats, network
3. Found `disk_report` table missing (despite module being installed)
4. Discovered `/module/disk_report/get_stats` via HTML page JavaScript
5. Confirmed endpoint requires authentication but returns fleet-wide stats

### Endpoint Testing Results
- ✅ `/datatables/data` - Working (machine, reportdata, usage_stats, network)
- ✅ `/module/disk_report/get_stats` - Working (fleet disk stats)
- ✅ `/module/disk_report/get_volume_type` - Working (volume format counts)
- ✅ `/module/disk_report/get_disk_type` - Working (disk type counts)
- ✅ `/module/disk_report/get_smart_stats` - Working (S.M.A.R.T. status counts)
- ❌ `/report/disk_report/storage` - Returns PHP serialized data, not JSON
- ❌ `/module/disk_report/volumes` - 404 Not Found
- ❌ `/datatables/module/disk_report` - 404 Not Found

---

**Last Updated**: December 2024
**Status**: ✅ Complete - Fleet monitoring agent operational
**Fleet Size**: 107 machines
**Data Freshness**: Real-time via Munki Report API
