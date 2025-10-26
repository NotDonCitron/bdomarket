# Market History Tracking Guide

## Overview

This feature allows you to build your own **local database of market history** (stock & trades over time), similar to what Garmoth.com displays with their 3-plot graphs.

Since there's no API endpoint for historical data, you need to **collect it yourself daily** by running snapshots.

## 🎯 What You Get

After collecting data for 7-90 days, you can query:

1. **Stock History** - How many items were in stock each day
2. **Trades History** - Total trades count over time  
3. **Daily Sales** - Calculated sales per day (delta of trades)

Perfect for:
- Analyzing demand trends
- Identifying popular items
- Finding seasonal patterns
- Market intelligence

## 🚀 Quick Start

### 1. Record Your First Snapshot

```bash
python record_market_snapshot.py
```

This records stock & trades for **all ~8,000 items** in the marketplace.

**Takes:** 10-20 seconds  
**Stores:** `data/market_history/YYYY-MM/YYYY-MM-DD.jsonl`

### 2. Schedule Daily Collection

**Option A: Manual (Simple)**
```bash
# Run once per day manually
python record_market_snapshot.py
```

**Option B: Automated Watcher (Recommended)**
```bash
# Runs continuously, records at midnight
python watch_market_history.py

# Or in background (Windows)
pythonw watch_market_history.py
```

**Option C: Task Scheduler (Windows)**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 00:00
4. Action: `pythonw.exe C:\path\to\record_market_snapshot.py`

**Option D: Cron (Linux/Mac)**
```bash
# Add to crontab (run at midnight)
0 0 * * * cd /path/to/project && python3 record_market_snapshot.py
```

### 3. Query Historical Data

After collecting for a few days:

```python
from utils.market_history_tracker import MarketHistoryTracker

tracker = MarketHistoryTracker(region='eu')

# Get stock history for last 7 days
stock_history = tracker.get_stock_history([16001, 16002], days=7)
# Returns: {16001: [('2025-10-19', 150), ('2025-10-20', 145), ...]}

# Get total trades history
trades_history = tracker.get_trades_history([16001], days=30)

# Get calculated daily sales
daily_sales = tracker.get_daily_sales([16001], days=90)
# Returns: {16001: [('2025-10-20', 180), ('2025-10-21', 210), ...]}
```

## 📊 Example Use Cases

### 1. Find Trending Items

```python
import asyncio
from utils.market_history_tracker import MarketHistoryTracker
from utils.item_helper import ItemHelper

async def find_trending():
    tracker = MarketHistoryTracker()
    helper = ItemHelper(region='eu')
    await helper.initialize()
    
    # Get popular items
    popular_items = [16001, 16002, 44195, 721003, 15640]
    
    # Check daily sales trend
    daily_sales = tracker.get_daily_sales(popular_items, days=7)
    
    for item_id, sales in daily_sales.items():
        if not sales:
            continue
        
        item_info = await helper.get_item_info(item_id)
        recent_avg = sum(s for _, s in sales[-3:]) / 3  # Last 3 days
        older_avg = sum(s for _, s in sales[:3]) / 3     # First 3 days
        
        if recent_avg > older_avg * 1.5:  # 50% increase
            print(f"🔥 TRENDING: {item_info.name}")
            print(f"   Sales increased from {older_avg:.0f} to {recent_avg:.0f}/day")

asyncio.run(find_trending())
```

### 2. Stock Availability Monitor

```python
def check_stock_availability(tracker, item_ids, threshold=100):
    """Find items with consistently low stock (high demand)."""
    stock_history = tracker.get_stock_history(item_ids, days=7)
    
    low_stock_items = []
    for item_id, history in stock_history.items():
        if not history:
            continue
        
        avg_stock = sum(s for _, s in history) / len(history)
        if avg_stock < threshold:
            low_stock_items.append((item_id, avg_stock))
    
    return sorted(low_stock_items, key=lambda x: x[1])
```

### 3. Trading Volume Analysis

```python
def analyze_trading_volume(tracker, item_id, days=30):
    """Analyze if item has stable trading volume."""
    daily_sales = tracker.get_daily_sales([item_id], days=days)
    
    if not daily_sales or item_id not in daily_sales:
        return None
    
    sales = [s for _, s in daily_sales[item_id]]
    
    avg = sum(sales) / len(sales)
    std_dev = (sum((s - avg) ** 2 for s in sales) / len(sales)) ** 0.5
    
    volatility = std_dev / avg if avg > 0 else 0
    
    return {
        'avg_daily_sales': avg,
        'volatility': volatility,
        'stable': volatility < 0.3  # Less than 30% volatility
    }
```

## 📁 Data Storage

```
data/market_history/
├── 2025-10/
│   ├── 2025-10-20.jsonl
│   ├── 2025-10-21.jsonl
│   ├── 2025-10-22.jsonl
│   └── ...
├── 2025-11/
│   └── ...
└── recorder.log  (if using watch_market_history.py)
```

**Format (JSONL):**
```json
{"date": "2025-10-25", "item_id": 16001, "stock": 150, "trades": 45000, "base_price": 180000}
{"date": "2025-10-25", "item_id": 16002, "stock": 200, "trades": 38000, "base_price": 190000}
...
```

**Storage Size:**
- ~1-2 MB per day (compressed text)
- 90 days ≈ 100-200 MB
- Very reasonable!

## 🔧 API Reference

### MarketHistoryTracker

```python
from utils.market_history_tracker import MarketHistoryTracker

tracker = MarketHistoryTracker(region='eu', history_dir='data/market_history')
```

#### Methods

**`async record_snapshot(verbose=True) -> bool`**
- Records current market snapshot
- Returns True if successful

**`get_stock_history(item_ids, days=90) -> Dict[int, List[Tuple[str, int]]]`**
- Get stock count history
- Returns: `{item_id: [('YYYY-MM-DD', stock), ...]}`

**`get_trades_history(item_ids, days=90) -> Dict[int, List[Tuple[str, int]]]`**
- Get total trades history
- Returns: `{item_id: [('YYYY-MM-DD', total_trades), ...]}`

**`get_daily_sales(item_ids, days=90) -> Dict[int, List[Tuple[str, int]]]`**
- Calculate daily sales (delta of trades)
- Returns: `{item_id: [('YYYY-MM-DD', sales_that_day), ...]}`
- **Most useful** for analyzing daily activity!

**`get_summary() -> dict`**
- Get statistics about collected data
- Returns: `{'total_snapshots', 'date_range', 'days_of_data', 'latest_snapshot'}`

**`get_available_dates() -> List[str]`**
- Get list of dates with snapshots
- Returns: `['2025-10-20', '2025-10-21', ...]`

## 📈 Comparison to Garmoth

| Feature | Garmoth.com | This Tool |
|---------|-------------|-----------|
| Price History | ✅ Yes (90 days) | ❌ Not yet |
| Stock History | ✅ Yes | ✅ Yes |
| Trade Volume | ✅ Yes | ✅ Yes |
| Data Storage | Server-side | Local |
| Historical Access | Instant | After collecting |
| Privacy | Public | Private |

**Why build your own?**
- ✅ **Private** - Your data stays local
- ✅ **Custom** - Track exactly what you want
- ✅ **Free** - No rate limits
- ✅ **Control** - Own your data
- ✅ **Extensible** - Add custom analysis

## ❓ FAQ

**Q: How long until I have useful data?**  
A: 7 days = good trends, 30 days = solid analysis, 90 days = comprehensive

**Q: What if I miss a day?**  
A: No problem! The data will have a gap, but queries still work

**Q: Can I backfill historical data?**  
A: Unfortunately no, the API only provides current data. Start collecting now!

**Q: Does this include price history?**  
A: Not yet. Stock and trades only. Price history could be added later.

**Q: How do I visualize this data?**  
A: Use matplotlib/pandas:
```python
import matplotlib.pyplot as plt

stock_history = tracker.get_stock_history([16001], days=30)
dates = [d for d, _ in stock_history[16001]]
stocks = [s for _, s in stock_history[16001]]

plt.plot(dates, stocks)
plt.title('Black Stone (Weapon) - Stock History')
plt.xticks(rotation=45)
plt.show()
```

**Q: Can I share my data with others?**  
A: Yes! Just share your `data/market_history/` folder

## 🎯 Next Steps

1. **Start collecting:** `python record_market_snapshot.py`
2. **Set up automation:** Use `watch_market_history.py` or Task Scheduler
3. **Come back in 7 days** and run `python test_market_history.py`
4. **Build custom analysis** using the API

## 💡 Tips

- Run snapshots at consistent times (midnight recommended)
- Don't run more than once per day (same data, wastes space)
- Keep your system time accurate
- Back up your `data/market_history/` folder
- Use `--summary` to check your data anytime

## 🤝 Credits

- Inspired by [Garmoth.com](https://garmoth.com/market) by Fizzor
- Uses [bdomarket](https://github.com/Fizzor96/bdomarket) library
- Built for BDO marketplace analysis

---

**Happy Trading!** 📊💰

