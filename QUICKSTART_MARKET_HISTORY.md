# Quick Start: Market History Tracking

## What is this?

Build your own **Garmoth-style historical database** of BDO market data (stock & trades over time).

Since the API doesn't provide historical data, you need to **collect it yourself daily**.

## ⚡ 5-Minute Setup

### 1. Record Your First Snapshot

```bash
python record_market_snapshot.py
```

✅ Done! You now have day 1 of data.

### 2. Automate Daily Collection

**Option A: Manual (Run daily)**
```bash
python record_market_snapshot.py
```

**Option B: Automated (Recommended)**
```bash
# Windows - Double-click
run_market_history_watcher.cmd

# Or command line
python watch_market_history.py
```

This runs 24/7 and records at midnight automatically.

### 3. Come Back in 7 Days

After collecting for a week, you can:

```python
from utils import MarketHistoryTracker

tracker = MarketHistoryTracker()

# Get stock history
stock = tracker.get_stock_history([16001], days=7)
print(stock)
# {16001: [('2025-10-19', 150), ('2025-10-20', 145), ...]}

# Get daily sales (most useful!)
sales = tracker.get_daily_sales([16001], days=7)
print(sales)
# {16001: [('2025-10-20', 180), ('2025-10-21', 210), ...]}
```

## 🎯 What You Get

| Metric | Description | Use Case |
|--------|-------------|----------|
| **Stock History** | Items in stock each day | Supply trends |
| **Trades History** | Total trades over time | Popularity |
| **Daily Sales** | Items sold per day | Demand analysis |

## 📊 Example Use Case

**Find items with increasing demand:**

```python
tracker = MarketHistoryTracker()
daily_sales = tracker.get_daily_sales([16001, 16002, 44195], days=7)

for item_id, sales in daily_sales.items():
    recent = sum(s for _, s in sales[-3:]) / 3  # Last 3 days avg
    older = sum(s for _, s in sales[:3]) / 3     # First 3 days avg
    
    if recent > older * 1.5:  # 50% increase
        print(f"Item {item_id} is trending! 📈")
        print(f"  Sales up from {older:.0f} to {recent:.0f}/day")
```

## 📁 Where is Data Stored?

```
data/market_history/
├── 2025-10/
│   ├── 2025-10-20.jsonl  (~1-2 MB)
│   ├── 2025-10-21.jsonl
│   └── ...
└── recorder.log
```

- **Format:** JSONL (one JSON per line)
- **Size:** ~1-2 MB per day, ~100-200 MB for 90 days
- **Local:** Your data, your control

## 🔥 Pro Tips

1. **Start collecting NOW** - Can't backfill historical data
2. **Consistent timing** - Run at same time daily (midnight recommended)
3. **Don't skip days** - Gaps are okay but less data = less insights
4. **Backup your data** - Copy `data/market_history/` folder

## 📚 Full Documentation

- **Complete Guide:** [MARKET_HISTORY_GUIDE.md](MARKET_HISTORY_GUIDE.md)
- **Test Suite:** `python test_market_history.py`
- **Examples:** `python example_market_history.py`

## ❓ FAQ

**Q: Can I get historical data from before I started?**  
A: No, API only provides current data. Start collecting now!

**Q: How long until useful?**  
A: 7 days = good trends, 30 days = solid analysis, 90 days = comprehensive

**Q: What if I miss a day?**  
A: Not a problem, you'll just have a gap in the data

**Q: Can I run multiple times per day?**  
A: You can, but it's the same data. Once per day is enough.

## 🚀 Next Steps

1. ✅ Run setup: `python setup_market_history.cmd` (Windows) or `python record_market_snapshot.py`
2. ⏰ Schedule daily: Use `watch_market_history.py` or Task Scheduler
3. 📊 After 7+ days: Start analyzing trends
4. 🎓 Learn more: Read [MARKET_HISTORY_GUIDE.md](MARKET_HISTORY_GUIDE.md)

---

**Happy Trading!** 📈💰

