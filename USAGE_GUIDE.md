# BDO Trading Tools - Usage Guide

Complete command-line reference for all trading tools.

---

## 🎯 Pearl Sniper

**Purpose**: Monitor Pearl items for profitable Cron Stone extraction opportunities

### Basic Usage
```bash
# Test mode (mock data, no API calls)
python pearl_sniper.py --test

# Live monitoring
python pearl_sniper.py

# Dry run (real API, no Discord alerts)
python pearl_sniper.py --dry-run
```

### Options
- `--test` - Use mock data for testing
- `--dry-run` - Real monitoring without sending alerts
- `--config CONFIG` - Custom config file (default: `config/pearl_sniper.yaml`)

### Configuration
Edit `config/pearl_sniper.yaml` to customize:
- Alert channels (Terminal, Toast, Discord)
- Profit thresholds
- Polling intervals
- Market intelligence tracking
- Prime time detection

---

## 📢 Item Sniper

**Purpose**: Monitor specific items from watchlist and alert when prices hit targets

### Basic Usage
```bash
# Start monitoring with default config
python sniper.py

# Use custom watchlist
python sniper.py --config path/to/watchlist.yaml
```

### Configuration
Edit `config/sniper_watchlist.yaml`:
```yaml
watchlist:
  - item_id: 16001
    item_name: "Black Stone (Weapon)"
    target_buy_max: 1000000
    target_sell_min: 1500000
    alert_on: "both"  # "buy", "sell", or "both"
```

---

## 💼 Portfolio Tracker

**Purpose**: Log trades and generate P&L reports

### Commands

#### 1. Log a Trade
```bash
python portfolio.py log
```
Interactive mode - prompts for:
- Item name (search with auto-complete)
- Quantity
- Price
- Trade type (buy/sell)
- Notes (optional)

#### 2. Generate Report
```bash
python portfolio.py report
```
Shows complete trading history with:
- Total buys/sells
- Realized profit/loss
- Current holdings
- P&L breakdown by item

#### 3. Live Status
```bash
python portfolio.py status --live
```
Shows current positions with live market prices:
- Holdings
- Current market value
- Unrealized P&L

### Settings
Edit `data/portfolio_settings.json`:
```json
{
  "tax_rate": 0.35,
  "value_pack": true,
  "familia_fame_bonus": 0.0
}
```

---

## 🔄 Flip Scanner

**Purpose**: Scan entire market for profitable flip opportunities

### Basic Usage
```bash
# Quick scan with defaults
python flip_scanner.py

# Advanced scan
python flip_scanner.py --region eu --tax 0.245 --min-roi 0.10 --max-items 200
```

### Options
- `--region` - Market region: `eu`, `na`, `kr`, `sa` (default: `eu`)
- `--tax` - Effective tax rate (default: `0.35`)
- `--min-roi` - Minimum ROI threshold (default: `0.05` = 5%)
- `--max-items` - Maximum items to scan (default: `150`)
- `--filter-risk` - Filter by risk level: `LOW`, `MEDIUM`, `HIGH`
- `--no-competition` - Disable competition analysis (faster)
- `--no-timing` - Disable market timing info (faster)

### Examples
```bash
# Find only low-risk flips
python flip_scanner.py --filter-risk LOW

# Fast scan (no analysis)
python flip_scanner.py --no-competition --no-timing

# High ROI hunting with Value Pack tax
python flip_scanner.py --tax 0.245 --min-roi 0.15
```

---

## 📊 Market Analyzer

**Purpose**: Analyze market competition and timing

### Commands

#### 1. Competition Analysis
```bash
# Analyze popular items
python analyzer.py competition

# Analyze specific items
python analyzer.py competition --items 16001,16002,16003

# Save analysis to history
python analyzer.py competition --save
```

#### 2. Market Timing
```bash
python analyzer.py timing
```
Shows optimal trading windows based on:
- Maintenance schedules
- Peak hours
- Historical data

### Options
- `--region` - Market region (default: `eu`)
- `--items` - Comma-separated item IDs
- `--save` - Save snapshots to history folder

---

## 🎲 Portfolio Optimizer

**Purpose**: Optimize budget allocation across multiple items

### Basic Usage
```bash
# Interactive mode
python optimizer.py
```

Prompts for:
- Total budget
- Tax rate
- Items to optimize (ID, buy price, sell price, target ROI)

### Output
- Optimal quantity for each item
- Expected profit per item
- Total portfolio profit
- Risk distribution

---

## 💡 Quick Start Recommendations

### For Beginners
1. **Start with Pearl Sniper (test mode)**
   ```bash
   python pearl_sniper.py --test
   ```

2. **Log your first trades**
   ```bash
   python portfolio.py log
   ```

3. **Check market for easy flips**
   ```bash
   python flip_scanner.py --filter-risk LOW
   ```

### For Active Traders
1. **Run Pearl Sniper live**
   ```bash
   python pearl_sniper.py
   ```

2. **Monitor specific items**
   - Edit `config/sniper_watchlist.yaml`
   - Run `python sniper.py`

3. **Daily flip scan**
   ```bash
   python flip_scanner.py --min-roi 0.10
   ```

4. **Track all trades**
   ```bash
   python portfolio.py report
   ```

### For Advanced Users
1. **Competition analysis before trading**
   ```bash
   python analyzer.py competition --items YOUR_ITEMS --save
   ```

2. **Optimize budget allocation**
   ```bash
   python optimizer.py
   ```

3. **Monitor prime time windows**
   - Pearl Sniper auto-detects EU prime time
   - Check console for 🔥 PRIME TIME notifications

---

## 🔧 Common Issues

### "Missing command argument"
✅ **Solution**: Many tools require commands
```bash
# Wrong
python portfolio.py

# Correct
python portfolio.py report
```

### "Config file not found"
✅ **Solution**: Copy example configs
```bash
cp config/sniper_watchlist.example.yaml config/sniper_watchlist.yaml
cp config.example.json config.json
```

### "UnicodeEncodeError on Windows"
✅ **Solution**: Already fixed! All tools now handle Windows encoding automatically.

### "API rate limiting"
✅ **Solution**: Tools automatically handle rate limits with smart polling intervals.

---

## 📝 Tips & Best Practices

1. **Test mode first**: Always test new tools with `--test` flag before live use
2. **Track everything**: Use Portfolio Tracker religiously for accurate P&L
3. **Prime time advantage**: Pearl Sniper is most effective during EU prime hours
4. **Risk management**: Start with LOW risk flips, increase as you gain experience
5. **Regular scans**: Run Flip Scanner 2-3 times daily for best opportunities
6. **Competition matters**: Use Analyzer before investing heavily in any item

---

## 🆘 Support

- Check `README.md` for project overview
- See `PEARL_SNIPER.md` for Pearl Sniper deep dive
- Review `PRICING_REFERENCE.md` for Cron Stone economics
- Read `.plan.md` files for implementation details

---

**Last Updated**: October 25, 2025
**All Tools Status**: ✅ Operational & Production Ready

