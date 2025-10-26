# 🚀 Pearl Auto-Buy - Quick Start Guide

Get up and running with Pearl Auto-Buy in 5 minutes!

## Prerequisites

- Python 3.8+
- Windows 10+ (for desktop notifications)
- Internet connection
- BDO account with Steam login

## Step 1: Install Dependencies (2 minutes)

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Step 2: Setup Authentication (2 minutes)

```bash
python setup_session.py
```

**What happens:**
1. Browser opens automatically
2. Navigate to BDO marketplace
3. **Click "Login" and login via Steam**
4. Wait until fully logged in
5. **Press ENTER in the terminal**
6. Session is extracted and saved

**Output:**
```
✅ Session extracted successfully!
   Session file: config/session.json

You can now run the auto-buy system:
  python pearl_autobuy.py
```

## Step 3: Test in Dry Run Mode (1 minute)

```bash
python pearl_autobuy.py --dry-run
```

**What to check:**
- ✅ Session loads successfully
- ✅ Prices are fetched
- ✅ Detection loop starts
- ✅ No authentication errors

**Expected output:**
```
Pearl Auto-Buy v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Region: EU
Polling: 0.1s (10.0 checks/sec)
Dry Run: ON
Auto-buy: DISABLED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[14:30:15] Initializing session...
[14:30:15] ✅ Session loaded (age: 0.1h)
[14:30:16] Updating material prices...
[14:30:17] 📊 Prices: Cron: 2.5M | Valks: 18M
[14:30:17] 🚀 Starting detection loop...
[14:30:17] Polling interval: 0.1s (10.0 checks/sec)
[14:30:17] ⚠️  DRY RUN MODE - No actual purchases will be made
```

Press `CTRL+C` to stop.

## Step 4: Configure (Optional)

Edit `config/pearl_autobuy.yaml`:

```yaml
pearl_autobuy:
  alert_threshold:
    minimum_profit: 100_000_000  # Lower = more items detected
    minimum_roi: 0.05            # Lower = more items detected
  
  auto_buy:
    max_price: 5_000_000_000     # Maximum price per item
    max_purchases_per_hour: 10   # Rate limit
```

**Recommended settings for beginners:**
```yaml
pearl_autobuy:
  alert_threshold:
    minimum_profit: 200_000_000  # 200M (conservative)
    minimum_roi: 0.10            # 10% ROI (conservative)
  
  auto_buy:
    max_price: 3_000_000_000     # 3B max (conservative)
    max_purchases_per_hour: 5    # Limit spending
```

## Step 5: Run Production Mode

```bash
# Foreground (see console output)
python pearl_autobuy.py

# Background (Windows, no console)
pythonw pearl_autobuy.py
```

**What it does:**
- Monitors all 8 pearl categories every 100ms
- Detects new listings in ~200-500ms
- Validates profit and ROI
- Attempts to purchase automatically
- Shows real-time status and statistics

## Monitoring

**While running, you'll see:**

```
[14:45:12] 🔥 PROFITABLE PEARL ITEM DETECTED!
======================================================================
[Male Outfits (Set)] [Kibelius] Outfit Set
  ID: 40001
  Price: 2,170,000,000 silver
  Quantity: 1
  Detected: 14:45:12
  
Extraction Value: 8.94B
Profit: 6.77B (312.0% ROI)
======================================================================
[14:45:12] ✅ Purchase successful: [Kibelius] Outfit Set for 2,170,000,000
```

## Stopping

Press `CTRL+C` to stop gracefully.

**Final statistics will be shown:**
```
📊 FINAL STATISTICS
======================================================================
Runtime: 01:23:45
Items Detected: 47
Items Purchased: 2
Items Skipped: 45

Purchase Attempts: 5
Success Rate: 40.0%
Total Spent: 4,340,000,000 silver
Total Profit: 13,540,000,000 silver
======================================================================
```

## Troubleshooting

### Session expired

```bash
# Re-run setup
python setup_session.py
```

### No items detected

- Check if there are actually pearl items listed on the market
- Try lowering `minimum_profit` and `minimum_roi` in config
- Verify your session is valid (run dry-run mode first)

### Items detected but not purchased

- Check `max_price` isn't too low
- Check you haven't hit `max_purchases_per_hour` limit
- Check cooldown settings
- Remember: Detection ≠ Purchase guarantee (BDO has registration queue)

## Next Steps

- Read [AUTOBUY_GUIDE.md](AUTOBUY_GUIDE.md) for detailed documentation
- Adjust settings based on your results
- Set up Discord webhook for remote notifications
- Monitor your silver balance and adjust limits

## Tips

✅ **Always test in dry-run first**
✅ **Start with conservative limits**
✅ **Monitor the first hour to verify settings**
✅ **Refresh session daily (or when errors occur)**
✅ **Check your silver balance regularly**

## Support

For detailed information:
- **[AUTOBUY_GUIDE.md](AUTOBUY_GUIDE.md)** - Complete documentation
- **[README.md](README.md)** - Main project documentation
- **[PEARL_SNIPER.md](PEARL_SNIPER.md)** - Alert-only version (no auto-buy)

Happy auto-buying! 🛒💎
