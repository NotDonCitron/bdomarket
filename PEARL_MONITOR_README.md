# Pearl Shop Monitor

Chrome MCP-based web traffic monitor for Black Desert Online Pearl shop listings.

## Features

- **Real-time Monitoring**: Uses Chrome DevTools Protocol (MCP) to monitor network traffic
- **Authentication**: Handles BDO website authentication with session persistence
- **Profit Analysis**: Calculates extraction values and ROI for Pearl items
- **Smart Alerts**: Multi-channel notifications (Terminal, Discord, Sound)
- **Adaptive Polling**: Configurable monitoring intervals
- **Session Management**: Saves and restores authentication sessions

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Edit `config/pearl_monitor.yaml`:

```yaml
pearl_monitor:
  poll_interval: 1              # Check interval in seconds
  headless: false               # Show browser for debugging
  alert_threshold:
    minimum_profit: 100_000_000  # 100M minimum profit
    minimum_roi: 0.05            # 5% minimum ROI
  notifications:
    terminal: true
    discord_webhook: null        # Optional Discord webhook
    sound_alert: true
```

### Usage

```bash
# Run with browser window (for initial setup)
python pearl_monitor.py

# Run in headless mode
python pearl_monitor.py --headless

# Test extraction calculations
python pearl_monitor.py --test

# Run without alerts (dry run)
python pearl_monitor.py --dry-run
```

### First Time Setup

1. Run without `--headless` flag to see browser window
2. Log in to BDO website when prompted
3. Session will be saved for future runs
4. After successful authentication, you can use `--headless` mode

## How It Works

### Chrome MCP Integration

The monitor uses Chrome DevTools Protocol via MCP to:

1. **Intercept Network Requests**: Monitors XHR calls to Pearl shop APIs
2. **Parse Responses**: Extracts item data from API responses
3. **Fallback Scanning**: Direct DOM parsing as backup method

### Profit Calculation

Based on BDO extraction mechanics:

- **Premium Outfit** (7 parts): 993 Cron + 331 Valks → ~9.1B value
- **Classic Outfit** (6 parts): 801 Cron + 267 Valks → ~7.3B value  
- **Simple Outfit** (4 parts): 543 Cron + 181 Valks → ~5B value
- **Mount Gear**: ~900 Cron + ~300 Valks → ~8.3B value

### Alert System

Alerts trigger when:
- Profit margin ≥ minimum threshold (default: 100M)
- ROI ≥ minimum threshold (default: 5%)
- Item is newly listed (not seen before)

## Example Output

```
💎 PEARL ALERT! Kibelius Outfit Set (PREMIUM)
   Listed: 1,350,000,000 Pearl
   Extraction: 9,100,000,000 (3,033 Crons)
   Profit: +7,750,000,000 (+574.0% ROI) ✓✓✓
   Time: 17:46:15 (ACT NOW!)
============================================================
```

## Testing

Run the test suite:

```bash
python tests/test_pearl_monitor.py
```

This tests:
- Pearl extraction value calculations
- Item categorization logic
- Edge cases and error handling
- ROI and profit calculations

## Configuration Options

### Monitoring Settings

- `poll_interval`: How often to check for updates (seconds)
- `headless`: Run browser without UI
- `user_agent`: Browser user agent string

### Alert Thresholds

- `minimum_profit`: Minimum profit margin in Pearl
- `minimum_roi`: Minimum return on investment (decimal)

### Notifications

- `terminal`: Show alerts in terminal
- `discord_webhook`: Discord webhook URL for notifications
- `sound_alert`: Play system beep on alerts

## Troubleshooting

### Authentication Issues

1. Clear saved session: Remove `auth` section from config
2. Run without `--headless` to see browser window
3. Manually log in when prompted
4. Check for CAPTCHA or 2FA requirements

### Chrome Driver Issues

1. Ensure Chrome browser is installed
2. Check internet connection for driver download
3. Try running with `--headless` disabled for debugging

### Network Monitoring

1. Some corporate networks may block DevTools Protocol
2. Check firewall settings for Chrome
3. Try different polling intervals if rate limited

## Dependencies

- `selenium`: Chrome browser automation
- `webdriver-manager`: Automatic Chrome driver management
- `mcp`: Chrome DevTools Protocol client
- `pyyaml`: Configuration file parsing
- `aiohttp`: Async HTTP requests (Discord notifications)
- `rich`: Terminal formatting (optional)

## Security Notes

- Session tokens are stored in plain text in config file
- Use appropriate file permissions on config directory
- Consider environment variables for sensitive data
- Never share config file with authentication tokens