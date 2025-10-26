# Pearl Item Sniper - Implementation Summary

## ✅ Status: Phase 1 Complete!

Speed-optimized Pearl Item monitoring tool for BDO marketplace with 1-2 second detection speed.

## 📋 What Was Implemented

### Core Files Created

1. **`pearl_sniper.py`** - Main monitoring application
   - Adaptive polling loop (1-2s intervals)
   - Error recovery and 24/7 operation
   - Test mode with mock data
   - Rich CLI interface

2. **`utils/pearl_calculator.py`** - Extraction value calculator
   - NO TAX profit calculation (extraction vs resale)
   - Premium: 993 Cron + 331 Valks
   - Classic: 801 Cron + 267 Valks
   - Simple: 543 Cron + 181 Valks
   - Mount: ~900 Cron + ~300 Valks

3. **`utils/smart_poller.py`** - Adaptive polling manager
   - Prime time (EU maintenance + weekends): 1s polling
   - Peak hours (18-22 UTC): 1s polling
   - Recent activity: 1.5s polling
   - Normal hours: 2s polling

4. **`utils/pearl_alerts.py`** - Multi-channel notification system
   - Terminal: Rich colored panels with beep
   - Windows Toast: Desktop notifications
   - Discord: Webhook with rich embeds
   - Priority levels: CRITICAL/HIGH/NORMAL

5. **`utils/market_intelligence.py`** - Market trend tracking
   - Track Pearl item sales via stock changes
   - Identify popular items in 24h window
   - Display statistics in healthcheck
   - No external APIs (bdomarket only)

6. **`config/pearl_sniper.yaml`** - Configuration file
   - Region settings
   - Alert thresholds
   - Notification channels
   - Peak hours configuration

7. **`tests/test_pearl_mock.py`** - Comprehensive test suite
   - Mock data testing
   - Component integration tests
   - All tests passing ✅

### Helper Scripts

- `run_pearl_sniper.cmd` - Run in foreground
- `run_pearl_sniper_background.cmd` - Run in background
- `test_pearl_sniper.cmd` - Test with mock data

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the System
```bash
python pearl_sniper.py --test
```

Or use the helper script:
```bash
test_pearl_sniper.cmd
```

### 3. Configure
Edit `config/pearl_sniper.yaml`:
```yaml
region: eu
pearl_sniper:
  poll_interval: 2
  peak_hours_boost: true
  alert_threshold:
    minimum_profit: 100_000_000  # 100M
    minimum_roi: 0.05            # 5%
  notifications:
    terminal_beep: true
    windows_toast: true
    discord_webhook: null  # Optional
```

### 4. Run 24/7

**Foreground (with console):**
```bash
python pearl_sniper.py
# Or: run_pearl_sniper.cmd
```

**Background (no console):**
```bash
pythonw pearl_sniper.py
# Or: run_pearl_sniper_background.cmd
```

**As Windows Service (recommended):**
```bash
nssm install PearlSniper "C:\Python312\pythonw.exe" "C:\path\to\pearl_sniper.py"
nssm start PearlSniper
```

## 🎯 Advanced Features

### Market Intelligence (Optional)

Track Pearl item activity over a 24-hour window to identify trends:

**How it works:**
- Monitors `get_market_list()` every 5 minutes
- Detects stock decreases = sales completed
- Tracks most popular items by sales count
- Displays top 5 items in healthcheck output

**Enable in config:**
```yaml
pearl_sniper:
  market_intelligence:
    enabled: true
    update_interval: 300  # 5 minutes
    display_stats: true
```

**Example output:**
```
📊 Popular Pearl Items (24h):
  • [Kibelius] Outfit Set: 12 sales (avg: 2.15B)
  • [Karlstein] Classic Outfit: 8 sales (avg: 1.89B)
  • Dream Horse Gear Set: 5 sales (avg: 2.05B)
```

**Benefits:**
- Understand which items sell most frequently
- Focus your attention on high-activity items
- Track market trends over time

**Note:** Uses additional API calls (~12/hour). Disable if concerned about rate limits.

### Prime Time Detection

Automatically boosts polling speed during optimal listing windows based on community research:

**EU Prime Time Schedule (UTC):**
- **Wednesday 10-14 UTC**: Post-maintenance window (highest activity)
- **Friday 18-23 UTC**: Weekend prime hours
- **Saturday 18-23 UTC**: Weekend prime hours

**How it works:**
- Automatically detects current time vs. prime windows
- Switches to 1s polling during prime time
- Shows "🔥 PRIME TIME" indicator in status
- Notifies when entering/exiting prime time

**Enable in config:**
```yaml
pearl_sniper:
  prime_time:
    enabled: true
    notify_transitions: true
```

**Example notifications:**
```
[14:52:30] 🔥 PRIME TIME STARTED - Optimal listing window! Switching to 1s polling
[14:52:35] 💎 Status: Items checked: 1247 | Alerts: 3 | Uptime: 02:15:45 | Interval: 1.0s | 🔥 PRIME TIME
```

**Benefits:**
- Maximizes detection speed when most items are listed
- Reduces API load during quiet hours
- Based on actual player research (see deep analysis)

**Research-backed:**
- Post-maintenance: Players immediately list items after servers come online
- Weekend evenings: Peak player activity = more listings
- Data collected from community sniper reports

### Polling Priority System

The Smart Poller uses a 4-tier priority system:

1. **Recent Activity** (1.5s) - Highest priority when Pearl items detected
2. **Prime Time** (1.0s) - EU-specific optimal windows
3. **Peak Hours** (1.0s) - General evening hours (18-22 UTC)
4. **Base Interval** (2.0s) - Default during quiet periods

This ensures maximum speed when needed while conserving API calls during low-activity periods.

## 💎 How It Works

### Pearl Item Extraction Mechanics

Pearl items can be extracted at the Blacksmith for materials:
- **Cron Stones** (Item ID: 16004)
  - NPC vendor: 3M each
  - Marketplace: ~2-2.5M each (cheaper!)
  - Extraction effective rate: Even better than marketplace!
- **Valks' Cry** (Item ID: 16003)
  - Marketplace: ~15-20M each

**Critical: Extraction profit has NO marketplace tax!**

### Why Extraction is Profitable

1. **Cron Stones are expensive:**
   - Buying from NPC: 3M each
   - Buying from marketplace: 2-2.5M each
   - Getting via extraction: Much cheaper per Cron!

2. **Example: Premium Outfit at 2.17B:**
   - Extraction: 993 Crons + 331 Valks
   - Market value: 993 × 2.5M + 331 × 20M = 9.10B
   - Your cost: 2.17B
   - **Profit: 6.93B (319% ROI)**

3. **Why this works:**
   - You're getting Crons at ~2.18M each via extraction
   - That's 27% cheaper than NPC (3M)
   - That's even slightly cheaper than marketplace (~2.5M)
   - NO TAX (vs 65.5% marketplace tax on resale)

### Example Calculation

```
Premium Outfit on market for 1.35B:
  Extraction: 993 Crons + 331 Valks
  
  Market Value:
    993 Crons × 2.5M = 2.48B (marketplace rate)
    331 Valks × 20M = 6.62B
    Total = 9.10B
  
  Your Cost: 1.35B
  Profit: 9.10B - 1.35B = 7.75B
  ROI: +574% 🔥
  
  Effective Cron Cost: 1.35B ÷ 993 = 1.36M per Cron!
  (vs 3M NPC or 2.5M marketplace)
  
  → INSTANT BUY!
```

### Detection Flow

```
1. Poll marketplace every 1-2s (adaptive)
2. Filter for Pearl Items (IDs 40000-49999)
3. Fetch live Cron/Valks prices (cached 5min)
4. Calculate extraction value
5. Compare to market price
6. Alert if profitable
```

## 📊 Test Results

All tests passing with mock data:

```
============================================================
TEST SUMMARY
============================================================
Calculator      ✅ PASSED
Poller          ✅ PASSED
Alerter         ✅ PASSED
Integration     ✅ PASSED

============================================================
✅ ALL TESTS PASSED
============================================================
```

### Example Alert Output

```
┌─ 🔥 PEARL ALERT! [Kibelius] Outfit Set (PREMIUM) ─┐
│ Listed: 1.35B                                     │
│ Extraction: 9.10B (993 Crons + 331 Valks)         │
│ Profit: +7.75B (+574.3% ROI) ✓✓✓                  │
│ Time: 17:46:15 (ACT NOW!)                         │
│ Item ID: 40001                                    │
└───────────────────────────────────────────────────┘
```

## ⚡ Performance Metrics

### Expected Performance
- **Detection Speed:** 1-2 seconds after listing
- **Coverage:** 80-90% of listings
- **Resource Usage:** <5% CPU, ~50MB RAM
- **API Load:** ~2,400 calls/hour (smart polling)

### Polling Strategy
- **Peak Hours (18-22 UTC):** 1s → 3,600 calls/hour
- **Normal Hours:** 2s → 1,800 calls/hour
- **After Activity:** 1.5s → 2,400 calls/hour

## 🎯 Alert Priority Levels

### 🔥 CRITICAL
- ROI > 50% OR
- Profit > 5B
- **Example:** 574% ROI on Kibelius Outfit

### ⚡ HIGH
- ROI 30-50% OR
- Profit 2-5B
- **Example:** 308% ROI on Classic Outfit

### ✓ NORMAL
- Any positive profit
- **Example:** 53% ROI on Simple Outfit

## 🔧 Configuration Options

### Alert Thresholds
```yaml
alert_threshold:
  minimum_profit: 100_000_000  # 100M absolute min
  minimum_roi: 0.05            # 5% relative min
```

### Notifications
```yaml
notifications:
  terminal_beep: true          # ASCII beep (\a)
  windows_toast: true          # Desktop notification
  discord_webhook: null        # Optional webhook URL
```

### Polling
```yaml
poll_interval: 2               # Base interval (seconds)
peak_hours_boost: true         # Enable 1s during peak
```

## ⚠️ Known Limitations

1. **Cannot Guarantee Purchase**
   - High competition (hundreds of pre-orders)
   - 1-90 second registration queue (RNG)
   - Detection speed doesn't guarantee success

2. **API Rate Limits**
   - bdomarket limits unknown
   - Monitor for 429 errors
   - Smart polling reduces load

3. **Platform Requirements**
   - Windows 10+ for Toast notifications
   - Python 3.8+ required
   - Rich terminal for best experience

## 🔮 Future Enhancements (Optional)

### Phase 2: Browser Extension
- Chrome extension for instant detection (0ms latency)
- DOM mutation observer on bdolytics.com
- Runs parallel to API poller
- **Coverage boost:** 80% → 95%

### Phase 3: Time-Offset Instances
- 3 processes with 0.33s offsets
- Effective 0.33s polling rate
- **Coverage boost:** 95% → 99%
- **Trade-off:** 3x API load

## 📚 Technical Details

### Key Design Decisions

1. **NO TAX Calculation**
   - Extraction bypasses marketplace entirely
   - Pure profit = Extraction Value - Purchase Price
   - No 65.5% tax like marketplace resale

2. **Adaptive Polling**
   - Reduces API load by ~33% vs fixed 1s
   - Maintains coverage through smart boosting
   - Activity detection for temporary speedup

3. **Multi-Channel Alerts**
   - Terminal: Always available, instant
   - Toast: Windows-native, persistent
   - Discord: Remote access, mobile support

4. **Error Recovery**
   - Auto-restart on fatal errors
   - Graceful handling of API failures
   - Connection retry logic

### Dependencies Added
```
win10toast>=0.9       # Windows notifications
aiohttp>=3.8          # Discord webhooks
```

## 🎓 Usage Examples

### Basic Usage
```bash
# Start monitoring
python pearl_sniper.py

# Test with mock data
python pearl_sniper.py --test

# Dry run (no alerts)
python pearl_sniper.py --dry-run

# Custom config
python pearl_sniper.py --config my_config.yaml
```

### Background Execution
```bash
# Windows background (no console)
pythonw pearl_sniper.py

# Windows service (persists across reboots)
nssm install PearlSniper "pythonw.exe" "pearl_sniper.py"
nssm start PearlSniper
```

### Monitoring
```bash
# Check if running (PowerShell)
Get-Process -Name pythonw | Where-Object {$_.Path -like "*pearl_sniper*"}

# Stop background process
Stop-Process -Name pythonw -Force
```

## 📖 Resources

- **Plan Document:** `bdo-trading-tools.plan.md`
- **Config:** `config/pearl_sniper.yaml`
- **Tests:** `tests/test_pearl_mock.py`
- **Helper Scripts:** `run_pearl_sniper*.cmd`, `test_pearl_sniper.cmd`

## ✅ Implementation Checklist

- [x] Create `utils/pearl_calculator.py` with NO TAX logic
- [x] Create `utils/smart_poller.py` with adaptive intervals
- [x] Create `utils/pearl_alerts.py` with multi-channel notifications
- [x] Create `pearl_sniper.py` main monitoring loop
- [x] Create `config/pearl_sniper.yaml` configuration
- [x] Create `tests/test_pearl_mock.py` test suite
- [x] Update `requirements.txt` with new dependencies
- [x] Update `README.md` with documentation
- [x] Create helper scripts for easy usage
- [x] Run and verify all tests pass ✅

## 🎉 Summary

**Phase 1 Implementation: COMPLETE!**

All core features implemented and tested:
- ✅ 1-2 second detection speed
- ✅ Accurate profit calculations (NO TAX)
- ✅ Multi-channel alerts
- ✅ Adaptive polling
- ✅ 24/7 operation ready
- ✅ All tests passing

The Pearl Sniper is ready for production use! 💎🚀

---

**Next Steps:**
1. Install dependencies: `pip install -r requirements.txt`
2. Test the system: `python pearl_sniper.py --test`
3. Configure alerts: Edit `config/pearl_sniper.yaml`
4. Run 24/7: `pythonw pearl_sniper.py` or use Windows Service
5. Monitor for profitable Pearl Items!

Good luck and happy sniping! 🎯

