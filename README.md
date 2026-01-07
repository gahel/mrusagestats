# MunkiReport Usage Stats - Automated Collection & Dashboard

Continuous collection and visualization of MacBook usage statistics from MunkiReport API with automated GitHub Actions pipeline and GitHub Pages dashboard.

## 🎯 Overview

This project automates the collection of performance metrics from managed MacBooks:
- **Hourly automatic collection** via GitHub Actions
- **Interactive web dashboard** with live charts
- **Historical trend data** in JSONL format
- **GitHub Pages hosting** for public/private access

## 📊 Dashboard

Live dashboard: [View Dashboard](https://gahel.github.io/mrusagestats/)

The dashboard shows:
- Real-time system metrics (thermal, power, GPU, CPU)
- Distribution charts and trends
- Per-machine performance comparison
- Data collection history

## 🔧 Collected Metrics

From `usage_stats` module:
- **Thermal**: thermal_pressure (Nominal/Warning/Critical)
- **Power**: package_watts (CPU/GPU consumption)
- **Performance**: GPU utilization, CPU frequency
- **Peripherals**: Backlight levels
- **Network**: I/O rates (bytes/sec)
- **Disk**: Read/write performance metrics

## 📁 Project Structure

```
mrusagestats/
├── .github/
│   └── workflows/
│       └── collect-stats.yml          # Hourly collection schedule
├── .gitignore
├── README.md                           # This file
├── README_GITHUB_SETUP.md              # Detailed setup guide
├── index.html                          # Generated dashboard
├── analyze_usage_stats.py              # Dashboard generator
├── collect_usage_stats.py              # Data collector
├── collect_usage_stats.sh              # Shell wrapper
├── usage_stats_history.jsonl           # Running history (JSONL)
├── get_data.py & get_data.sh           # Full inventory collection
├── health_report.py                    # Health analysis
├── thermal_pressure_report.py          # Thermal metrics
└── mr_api/                             # Archive of test scripts
```

## 🚀 Getting Started

### For Viewing

Simply visit the live dashboard: https://gahel.github.io/mrusagestats/

### For Local Development

```bash
# Clone repo
git clone https://github.com/gahel/mrusagestats.git
cd mrusagestats

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install requests

# Set up API credentials
security add-generic-password -a localuser -s munkireport-api -w "your_password"

# Collect data manually
python collect_usage_stats.py

# Generate dashboard
python analyze_usage_stats.py

# View locally
open index.html
```

### For GitHub Actions

1. **Fork/Clone** this repository
2. **Add GitHub Secret**: `MR_API_PASSWORD` in Settings → Secrets
3. **Enable GitHub Pages**: Settings → Pages → Deploy from `gh-pages` branch
4. Workflow runs automatically every hour

## 📈 Data Format

### usage_stats_history.jsonl
Newline-delimited JSON, one record per line:

```json
{
  "collected_at": "2026-01-07T21:50:46",
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

## 🔍 Usage Examples

```bash
# View latest records
tail -20 usage_stats_history.jsonl | jq .

# Query specific machine
cat usage_stats_history.jsonl | jq 'select(.hostname=="MBP-12418")'

# Filter by thermal state
cat usage_stats_history.jsonl | jq 'select(.thermal_pressure=="Critical")'

# Get average power per machine
cat usage_stats_history.jsonl | jq -s 'group_by(.hostname) | map({hostname: .[0].hostname, avg_watts: (map(.package_watts) | add / length)})'
```

## 🛠 Scripts Reference

### `collect_usage_stats.py`
Collects usage statistics from MunkiReport API.
- Output: `usage_stats_YYYYMMDD_HHMMSS.json` (snapshot)
- Output: Appends to `usage_stats_history.jsonl` (history)
- Runs: Every hour via GitHub Actions

### `analyze_usage_stats.py`
Generates interactive HTML dashboard from collected data.
- Input: `usage_stats_history.jsonl`
- Output: `index.html` (GitHub Pages)
- Charts: Thermal distribution, power trends, GPU usage
- Table: Per-machine statistics

### `get_data.py` / `get_data.sh`
Complete machine inventory with disk information.
- Queries: All machines with 16 data fields
- Output: JSON format
- Usage: One-time or manual inventory snapshots

### `health_report.py` / `thermal_pressure_report.py`
Specialized analysis scripts for health and thermal metrics.

## 📋 GitHub Actions Workflow

```yaml
Event: Every hour (cron: '0 * * * *')

Steps:
1. Checkout repository
2. Set up Python environment
3. Collect usage stats from API
4. Generate dashboard HTML
5. Commit changes to main branch
6. Deploy to GitHub Pages (gh-pages branch)
```

## ⚙️ Configuration

### API Credentials
Stored in GitHub Secrets as `MR_API_PASSWORD`:
- Used by: GitHub Actions workflow
- Security: Encrypted by GitHub, only available to workflows

### Collection Schedule
Edit `.github/workflows/collect-stats.yml` to change:
- `cron: '0 * * * *'` → Every hour
- `cron: '0 */6 * * *'` → Every 6 hours
- `cron: '0 9,17 * * 1-5'` → 9 AM and 5 PM weekdays

## 📊 Analytics Ideas

Possible future enhancements:
- Anomaly detection for unusual power consumption
- Email alerts for critical thermal states
- Trend forecasting (ML)
- Slack notifications
- Comparison reports across machines
- Power cost estimations

## 🔐 Security Notes

- API credentials stored in GitHub Secrets (encrypted)
- HTTPS only for API communication
- No sensitive data in public dashboard
- GitHub Pages can be made private via repo settings

## 📝 License

Internal use - Managed MacBook monitoring

## 🤝 Contributing

To add new metrics or improve the dashboard:
1. Edit `collect_usage_stats.py` to add columns
2. Update `analyze_usage_stats.py` to visualize new data
3. Commit and push - workflow handles the rest

## 📞 Support

For issues with:
- **API Connection**: Check MunkiReport server status
- **GitHub Actions**: View Actions tab → Workflow runs
- **Dashboard**: Check browser console for JS errors

---

**Last Updated**: 2026-01-07  
**Repository**: https://github.com/gahel/mrusagestats
