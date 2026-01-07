# MunkiReport API Data Collection & Analytics

Automated collection and visualization of MacBook usage statistics from MunkiReport API.

## Features

- **Hourly Collection**: Automatically collects usage stats via GitHub Actions
- **Interactive Dashboard**: Real-time visualization with Chart.js
- **Historical Tracking**: JSONL format for easy trend analysis
- **GitHub Pages**: Hosted dashboard at `yourusername.github.io/mr_api2`

## Scripts

### Collection
- **`collect_usage_stats.py`** - Collects usage_stats data and saves to JSON + JSONL
- **`collect_usage_stats.sh`** - Shell wrapper for cron jobs

### Analysis
- **`analyze_usage_stats.py`** - Generates interactive HTML dashboard

### Data Retrieval
- **`get_data.py` / `get_data.sh`** - Complete machine inventory with disk data
- **`health_report.py`** - System health analysis
- **`thermal_pressure_report.py`** - Thermal performance reports

## Setup

### Local Setup

1. **Configure API credentials in macOS Keychain:**
```bash
security add-generic-password -a localuser -s munkireport-api -w "your_password_here"
```

2. **Install Python dependencies:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install requests
```

3. **Test collection:**
```bash
python collect_usage_stats.py
python analyze_usage_stats.py
```

### GitHub Actions Setup

1. **Create GitHub Repository:**
```bash
cd /Users/gaute/scripts/mr_api2
git init
git remote add origin https://github.com/yourusername/mr_api2
```

2. **Set GitHub Secret:**
   - Go to: Settings → Secrets and variables → Actions
   - Add `MR_API_PASSWORD` with your MunkiReport API password

3. **Enable GitHub Pages:**
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: `gh-pages` / `/ (root)`

4. **Push to GitHub:**
```bash
git add .
git commit -m "Initial commit"
git push -u origin main
```

The workflow will:
- Run automatically every hour
- Collect usage stats
- Generate dashboard
- Commit data to main branch
- Deploy to GitHub Pages

## Data Structure

### usage_stats_history.jsonl
Each line is a JSON record:
```json
{
  "collected_at": "2026-01-07T21:50:46.123456",
  "serial_number": "C3W0FX49WN",
  "hostname": "MBP-12418",
  "thermal_pressure": "Nominal",
  "package_watts": 0.182886,
  "gpu_busy": 0.5,
  "freq_hz": 3500000000,
  "gpu_freq_mhz": 1300,
  "backlight": 60,
  "keyboard_backlight": 0,
  "ibyte_rate": 1024000,
  "obyte_rate": 512000,
  "rbytes_per_s": 2048000,
  "wbytes_per_s": 1024000
}
```

## Metrics Collected

- **Thermal**: thermal_pressure (Nominal/Warning/Critical)
- **Power**: package_watts (CPU/GPU power consumption)
- **Performance**: gpu_busy, freq_hz, gpu_freq_mhz
- **Input**: backlight, keyboard_backlight
- **Network**: ibyte_rate, obyte_rate (input/output bytes per second)
- **Disk I/O**: rbytes_per_s, wbytes_per_s (read/write bytes per second)

## Dashboard Features

- **Overview Stats**: Total records, unique machines, max values
- **Distribution Charts**: Thermal pressure, GPU utilization, power consumption
- **Machine Table**: Per-machine averages and last seen timestamp
- **Dark Theme**: GitHub-inspired color scheme

## Manual Operations

```bash
# Collect data once
python collect_usage_stats.py

# Generate dashboard from history
python analyze_usage_stats.py

# View history
tail -f usage_stats_history.jsonl | jq .

# Query specific machine
cat usage_stats_history.jsonl | jq 'select(.hostname=="MBP-12418")'
```

## File Organization

```
mr_api2/
├── get_data.py / get_data.sh        # Machine inventory
├── health_report.py                  # Health analysis
├── thermal_pressure_report.py        # Thermal metrics
├── collect_usage_stats.py            # Usage stats collection
├── analyze_usage_stats.py            # Dashboard generation
├── index.html                        # Dashboard (auto-generated)
├── usage_stats_history.jsonl         # Running history
├── usage_stats_*.json                # Timestamped snapshots
└── .github/workflows/                # GitHub Actions
    └── collect-stats.yml             # Hourly collection workflow
```

## License

Internal use only
