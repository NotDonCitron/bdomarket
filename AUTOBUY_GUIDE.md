# 🛒 BDO Pearl Shop Auto-Buy System

## Overview

The **Pearl Auto-Buy System** is a complete solution for real-time monitoring and automatic purchasing of profitable Pearl Shop items from the Black Desert Online Central Market.

### Key Features

✅ **Millisecond-Level Detection**
- HTTP/2 parallel polling of all 8 pearl categories
- 100ms poll interval = 10 checks per second
- New listings detected within ~100-200ms

✅ **Automatic Purchasing**
- Validates profitability before buying
- Safety checks (price limits, rate limits, cooldowns)
- Configurable purchase criteria

✅ **Persistent Authentication**
- Login once via Steam, session persists
- No manual re-login required
- Automatic session validation

✅ **Profit Validation**
- Automatic extraction value calculation
- NO TAX profit calculations (extraction bypasses marketplace)
- Configurable profit/ROI thresholds

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt

# If not installed yet:
pip install playwright httpx pyyaml rich aiohttp
playwright install chromium
```

### 2. Setup Authentication Session

Run the interactive setup tool to login via Steam and extract your session:

```bash
python setup_session.py
```

**What this does:**
1. Opens a browser
2. You login via Steam
3. Script extracts and saves your session to `config/session.json`
4. Session persists for ~24 hours (usually longer)

### 3. Configure Auto-Buy Settings

Edit `config/pearl_autobuy.yaml`:

```yaml
region: eu

pearl_autobuy:
  enabled: true
  
  detection:
    # Poll interval: 0.1 = 100ms = 10 checks/sec
    poll_interval: 0.1
  
  alert_threshold:
    minimum_profit: 100_000_000  # 100M silver
    minimum_roi: 0.05            # 5% ROI
  
  auto_buy:
    enabled: true
    max_price: 5_000_000_000          # 5B max per item
    max_purchases_per_hour: 10         # Rate limit
    cooldown_seconds: 2.0              # Cooldown between purchases
    require_confirmation: false        # Set true for manual approval
  
  notifications:
    terminal_beep: true
    windows_toast: true
    discord_webhook: null  # Add your webhook URL for Discord alerts
```

### 4. Run the Auto-Buy System

**Dry run (test without buying):**
```bash
python pearl_autobuy.py --dry-run
```

**Production (live auto-buy):**
```bash
python pearl_autobuy.py
```

**Background mode (Windows):**
```bash
pythonw pearl_autobuy.py
```

## 📋 How It Works

### Detection Pipeline

```
1. HTTP/2 Parallel Polling (100ms interval)
   ├─ Fetches all 8 pearl categories simultaneously
   ├─ Uses keep-alive connections for minimal latency
   └─ Detects new listings & stock increases

2. Profit Validation
   ├─ Detects outfit type (Premium/Classic/Simple/Mount)
   ├─ Calculates extraction value (Cron Stones + Valks' Cry)
   ├─ Compares to purchase price
   └─ Validates profit > threshold and ROI > threshold

3. Safety Checks
   ├─ Price < max_price
   ├─ Profit > min_profit
   ├─ ROI > min_roi
   ├─ Purchases this hour < max_purchases_per_hour
   └─ Cooldown elapsed

4. Purchase Execution
   ├─ Sends buy request to BDO API
   ├─ Enters registration queue (1-90 seconds)
   └─ May or may not be successful (competition)
```

### Pearl Item Values

The system automatically calculates extraction values:

| Outfit Type | Cron Stones | Valks' Cry | Extraction Value |
|-------------|-------------|------------|------------------|
| **Premium** (7 parts) | 993 | 331 | ~9.1B |
| **Classic** (6 parts) | 801 | 267 | ~7.3B |
| **Simple** (4 parts) | 543 | 181 | ~5.0B |
| **Mount Gear** | ~900 | ~300 | ~8.3B |

**Reference Prices:**
- Cron Stone: 3M (NPC vendor)
- Valks' Cry: ~18M (community average)

**Example:**
```
Premium Outfit listed at 2.17B:
  993 Crons × 3M = 2.98B
  331 Valks × 18M = 5.96B
  Total = 8.94B

  Profit: 6.77B (312% ROI) ✅ AUTO-BUY!
```

## ⚙️ Configuration

### Detection Settings

```yaml
detection:
  poll_interval: 0.1  # 0.05-1.0 seconds
```

**Recommended intervals:**
- `0.05` (50ms) - Absolute maximum speed, may hit rate limits
- `0.1` (100ms) - **Recommended** - Fast with safety margin
- `0.2` (200ms) - Balanced speed/load
- `0.5` (500ms) - Conservative

### Profit Thresholds

```yaml
alert_threshold:
  minimum_profit: 100_000_000  # Absolute profit in silver
  minimum_roi: 0.05            # Relative ROI (0.05 = 5%)
```

**Both conditions must be met!**

**Examples:**
- Item with 200M profit and 10% ROI → ✅ Triggers
- Item with 50M profit and 50% ROI → ❌ Blocked (profit too low)
- Item with 500M profit and 2% ROI → ❌ Blocked (ROI too low)

### Auto-Buy Safety

```yaml
auto_buy:
  enabled: true                      # Master switch
  max_price: 5_000_000_000          # Won't buy above this
  max_purchases_per_hour: 10         # Rate limit
  cooldown_seconds: 2.0              # Wait between purchases
  require_confirmation: false        # Manual approval
```

**Safety features:**
- **max_price**: Prevents buying overpriced items (even if profitable)
- **max_purchases_per_hour**: Prevents excessive spending
- **cooldown_seconds**: Prevents rapid-fire purchases
- **require_confirmation**: (Not yet implemented) Would ask for approval before each purchase

### Notifications

```yaml
notifications:
  terminal_beep: true           # ASCII beep on detection
  windows_toast: true           # Desktop notification (Windows 10+)
  discord_webhook: "https://discord.com/api/webhooks/..."  # Optional
```

## 🔐 Authentication & Session Management

### Session Lifecycle

```
1. Initial Setup (One-Time)
   └─ Run: python setup_session.py
   └─ Login via Steam in browser
   └─ Session saved to config/session.json

2. Daily Use
   └─ Auto-buy system loads session
   └─ Validates session (cached for 60s)
   └─ Runs until session expires (~24h)

3. Session Expired
   └─ System detects 401/403 error
   └─ Exits with error message
   └─ Re-run: python setup_session.py
```

### Manual Session Creation

If you prefer, create `config/session.json` manually:

```json
{
  "cookie": "your_full_cookie_string_from_browser",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "request_verification_token": "your_token_here",
  "user_no": "optional_user_number",
  "created_at": 1234567890.0,
  "last_validated": 1234567890.0,
  "is_valid": true
}
```

**How to get these values:**
1. Open https://eu-trade.naeu.playblackdesert.com/ in browser
2. Login via Steam
3. Press F12 → Application → Cookies
4. Copy cookie string
5. Network tab → find any API call → copy User-Agent and __RequestVerificationToken

## 📊 Statistics & Monitoring

The system tracks comprehensive statistics:

```
📊 FINAL STATISTICS
======================================================================
Runtime: 02:15:45
Items Detected: 127
Items Purchased: 3
Items Skipped: 124

Total Loops: 81,450
Total API Calls: 651,600
Loops/Second: 10.01

Purchase Attempts: 5
Success Rate: 60.0%
Total Spent: 6,510,000,000 silver
Total Profit: 20,310,000,000 silver
======================================================================
```

## 🛡️ Safety Features

### Built-in Protection

1. **Price Limits**
   - Won't buy items over `max_price`
   - Prevents accidental overspending

2. **Rate Limits**
   - Max purchases per hour
   - Prevents buying spree if many items appear

3. **Cooldown Period**
   - Forced wait between purchases
   - Prevents rapid-fire buying

4. **Profit Validation**
   - Double-checks profit calculations
   - Won't buy unless thresholds met

5. **Session Validation**
   - Checks session every 60 seconds
   - Exits cleanly if session expires

6. **Dry Run Mode**
   - Test without real purchases
   - See what would be bought

### Known Limitations

⚠️ **Purchase Success Not Guaranteed**
- Detection ≠ Purchase success
- BDO has 1-90 second registration queue (random)
- High competition from other players
- Expected success rate: 1-10% per detection

⚠️ **Session Expiration**
- Sessions expire after ~24 hours
- Must re-run setup_session.py
- No automatic re-authentication yet

⚠️ **Rate Limits**
- Too many API calls may trigger throttling
- Stay at 0.1s+ interval to be safe

## 🚨 Troubleshooting

### Session expired error

```
🚨 AUTHENTICATION ERROR!
Session expired or invalid. Please refresh your session.
```

**Solution:**
```bash
python setup_session.py
```

### No items detected

**Check:**
1. Is your session valid? (run dry-run first)
2. Are there actually pearl items listed?
3. Is your poll_interval too high?
4. Check internet connection

### Items detected but not purchased

**Check:**
1. Is `auto_buy.enabled: true`?
2. Are profit thresholds met?
3. Is max_price too low?
4. Have you hit rate limits?
5. Is cooldown still active?

### Import errors

```bash
# Missing dependencies
pip install -r requirements.txt

# Playwright not installed
pip install playwright
playwright install chromium
```

## 💡 Best Practices

### 1. Start with Dry Run

Always test first:
```bash
python pearl_autobuy.py --dry-run
```

Verify:
- Session is valid
- Items are being detected
- Profit calculations are correct
- Thresholds are appropriate

### 2. Conservative Settings

Start conservative, then optimize:
```yaml
auto_buy:
  max_price: 3_000_000_000  # Start lower
  max_purchases_per_hour: 5  # Limit spending
  cooldown_seconds: 5.0      # Longer cooldown
```

### 3. Monitor Regularly

Check logs for:
- Detection rate
- Purchase success rate
- Profitability of actual purchases
- Session health

### 4. Adjust Thresholds

Based on results, adjust:
- Lower `minimum_profit` to catch more items
- Raise `minimum_roi` to filter better
- Adjust `max_price` based on market

### 5. Use Discord Webhook

Set up Discord notifications for remote monitoring:
```yaml
notifications:
  discord_webhook: "https://discord.com/api/webhooks/YOUR_WEBHOOK"
```

## 📈 Performance Expectations

### Detection Speed

- **Poll interval:** 100ms
- **Detection latency:** 100-300ms
- **Total time to detect:** 200-500ms after listing

### Success Rate

- **Detection success:** 90-99% (if polling correctly)
- **Purchase success:** 1-10% (depends on competition)
- **Overall:** Expect ~1-10 successful purchases per 100 detections

### Resource Usage

- **CPU:** <5% average
- **RAM:** ~100-150MB
- **Network:** ~50KB/s
- **API calls:** 600-3600 per minute (depending on interval)

## 🔮 Future Enhancements

### Planned Features

- [ ] **Browser-based real-time detection** (0ms latency via DOM monitoring)
- [ ] **Multi-instance coordination** (multiple processes with time offsets)
- [ ] **Machine learning profit prediction** (learn which items sell best)
- [ ] **Automatic session refresh** (no manual re-login needed)
- [ ] **Advanced profit strategies** (consider resale value, not just extraction)
- [ ] **Purchase analytics dashboard** (web UI for statistics)

## 📚 Related Documentation

- **[README.md](README.md)** - Main project documentation
- **[PEARL_SNIPER.md](PEARL_SNIPER.md)** - Alert-only pearl monitoring (no auto-buy)
- **[MANUAL_LOGIN_GUIDE.md](MANUAL_LOGIN_GUIDE.md)** - Browser-based authentication
- **[MARKET_ADVANTAGE_RESEARCH.md](MARKET_ADVANTAGE_RESEARCH.md)** - Advanced trading strategies

## ❓ FAQ

**Q: Is this against BDO ToS?**
A: This uses the official web marketplace API, same as the website. Use at your own discretion.

**Q: Will this guarantee purchases?**
A: No. BDO has registration queues and high competition. Detection ≠ Purchase success.

**Q: Can I run multiple instances?**
A: Not recommended with the same session. May cause conflicts or rate limiting.

**Q: How often should I refresh my session?**
A: Sessions last ~24 hours. Refresh daily or when you see auth errors.

**Q: What's the best poll interval?**
A: 0.1s (100ms) is recommended. Faster = more load, slower = miss items.

**Q: Can I buy specific items only?**
A: Not yet implemented. Currently buys ANY profitable pearl item.

**Q: What if I want to manually approve each purchase?**
A: Set `require_confirmation: true` (feature not yet implemented).

## 🆘 Support

If you encounter issues:

1. Check this guide
2. Verify your configuration
3. Test in dry-run mode
4. Check session validity
5. Review system logs

For bug reports, include:
- Error message
- Configuration (remove sensitive data)
- Steps to reproduce
