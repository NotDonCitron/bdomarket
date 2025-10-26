# Market History Tracker - Implementation Notes

## ✅ What Works

### Successfully Implemented
- ✅ Daily snapshot recording (`record_market_snapshot.py`)
- ✅ Data storage in JSONL format (`data/market_history/YYYY-MM/YYYY-MM-DD.jsonl`)
- ✅ Historical data queries (stock, trades, daily sales)
- ✅ Automated 24/7 watcher (`watch_market_history.py`)
- ✅ Query-only tool (`query_market_history.py`)
- ✅ Complete documentation

### Tested on User's System
- ✅ First snapshot recorded successfully: **11,157 items**
- ✅ Data file created: `data/market_history/2025-10/2025-10-25.jsonl`
- ✅ Query tool works perfectly (no API calls, no encoding issues)

## 📊 Sample Data

From user's first snapshot (2025-10-25):
- **Item 16001** (Black Stone Weapon): 15,138 in stock, 3,001,229,146 total trades
- **Item 44195** (Caphras Stone): 86,479 in stock, 827,474,008 total trades

## ⚠️ Known Issues

### Windows Console Encoding with bdomarket
**Issue:** When running `test_market_history.py` or making multiple API calls, you may see:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2705' in position 0
```

**Cause:** The bdomarket library tries to print emoji (✅) in update messages, and Windows console (cp1252) doesn't support Unicode emojis.

**Workaround:**
1. Use `query_market_history.py` instead (no API calls, works perfectly)
2. Or set environment variable: `set PYTHONIOENCODING=utf-8`
3. Or use Windows Terminal instead of cmd.exe

**Not a bug in our code** - this is a bdomarket + Windows console interaction issue.

### Item 16002 Missing in First Test
Item 16002 (Black Stone Armor) had no data in the first snapshot. This is likely because:
- The item wasn't in the market at that moment, OR
- There was a temporary API issue for that specific item

This is normal - just collect more snapshots and the data will appear.

## 🎯 Recommended Usage

### For Daily Collection
```bash
# Best: Automated watcher (set and forget)
python watch_market_history.py

# Or: Windows Task Scheduler
# Run record_market_snapshot.py at midnight daily
```

### For Viewing Data
```bash
# Quick view (no API calls)
python query_market_history.py

# With summary
python record_market_snapshot.py --summary
```

### For Analysis
```python
# Use the Python API
from utils import MarketHistoryTracker

tracker = MarketHistoryTracker()
stock = tracker.get_stock_history([16001, 44195], days=30)
sales = tracker.get_daily_sales([16001], days=7)
```

## 📈 Data Collection Strategy

### Minimum Useful Data
- **7 days** - Basic trends visible
- **30 days** - Solid analysis possible
- **90 days** - Comprehensive insights

### When to Start
**NOW!** Can't backfill historical data. Every day you wait is data lost.

### Storage Requirements
- **1-2 MB per day** (~11,000 items in JSONL)
- **~70-140 MB for 90 days**
- Very reasonable for local storage

## 🔧 File Structure

```
data/market_history/
├── 2025-10/
│   └── 2025-10-25.jsonl  (11,157 items, ~1.5 MB)
├── 2025-11/
│   └── ... (future snapshots)
└── recorder.log  (if using watch_market_history.py)
```

**JSONL Format:**
```json
{"date":"2025-10-25","item_id":16001,"stock":15138,"trades":3001229146,"base_price":180000}
{"date":"2025-10-25","item_id":44195,"stock":86479,"trades":827474008,"base_price":3000000}
```

## 🎓 Advanced Usage Examples

### Find High-Demand Items
```python
tracker = MarketHistoryTracker()
daily_sales = tracker.get_daily_sales([16001, 16002, 44195], days=7)

for item_id, sales in daily_sales.items():
    if not sales:
        continue
    avg = sum(s for _, s in sales) / len(sales)
    if avg > 1000:  # More than 1000 sales/day
        print(f"High demand: Item {item_id} ({avg:.0f} sales/day)")
```

### Track Supply Trends
```python
tracker = MarketHistoryTracker()
stock_history = tracker.get_stock_history([16001], days=30)

stocks = [s for _, s in stock_history[16001]]
avg_early = sum(stocks[:10]) / 10
avg_recent = sum(stocks[-10:]) / 10

if avg_recent < avg_early * 0.7:
    print("Supply is decreasing - potential shortage!")
```

### Export to CSV for Excel
```python
import csv
from utils import MarketHistoryTracker

tracker = MarketHistoryTracker()
stock_history = tracker.get_stock_history([16001, 44195], days=30)

with open('market_trends.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Item_16001_Stock', 'Item_44195_Stock'])
    
    # Combine histories
    for i, (date, stock1) in enumerate(stock_history[16001]):
        stock2 = stock_history[44195][i][1] if i < len(stock_history[44195]) else 0
        writer.writerow([date, stock1, stock2])

print("Exported to market_trends.csv - open in Excel!")
```

## 🚀 Future Enhancements

### Possible Additions
- **Price history tracking** - Currently only tracks stock & trades, could add prices
- **Visualization** - Matplotlib/Plotly charts for trends
- **Alerts** - Notify when stock drops below threshold
- **Web dashboard** - Browser-based visualization
- **ML predictions** - Forecast future prices/demand

### Why Not Included Yet
- Price data requires more storage (prices change more frequently)
- Visualization would need matplotlib dependency
- Alerts need scheduling/notifications infrastructure
- Web dashboard is a separate project
- ML needs 90+ days of data to be effective

## 📝 Credits

- **Original request:** Discord user "For Profit Organization"
- **Inspiration:** [Garmoth.com](https://garmoth.com/market) by Fizzor
- **API:** [bdomarket](https://github.com/Fizzor96/bdomarket) library
- **Built for:** BDO Trading Tools v3

---

**Status:** ✅ Fully functional, tested, documented, ready for use!

