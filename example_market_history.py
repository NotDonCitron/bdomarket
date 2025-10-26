#!/usr/bin/env python3
"""
Simple example showing how to use market history tracking.

This demonstrates the basic workflow:
1. Record a snapshot
2. Query historical data
3. Analyze trends
"""
import asyncio
from utils.market_history_tracker import MarketHistoryTracker


async def example_basic_usage():
    """Basic usage example."""
    print("\n" + "="*60)
    print("Market History Tracking - Basic Example")
    print("="*60 + "\n")
    
    # Initialize tracker
    tracker = MarketHistoryTracker(region='eu')
    
    # Check what data we have
    summary = tracker.get_summary()
    print(f"Current database status:")
    print(f"  Total snapshots: {summary['total_snapshots']}")
    print(f"  Days of data: {summary['days_of_data']}")
    
    if summary['total_snapshots'] == 0:
        print("\n📝 No data yet - recording first snapshot...")
        success = await tracker.record_snapshot()
        
        if success:
            print("✅ Snapshot recorded!")
            print("\n💡 Run this script daily to build up historical data")
        else:
            print("❌ Failed to record snapshot")
            return
    else:
        print(f"  Latest snapshot: {summary['latest_snapshot']}")
    
    # Query example: Popular trading items
    print("\n" + "="*60)
    print("Example Query: Stock & Trades History")
    print("="*60 + "\n")
    
    # Black Stone (Weapon), Black Stone (Armor), Caphras Stone
    example_items = [16001, 16002, 44195]
    
    # Get last 7 days of stock history
    stock_history = tracker.get_stock_history(example_items, days=7)
    
    print("Stock History (last 7 days):")
    for item_id, history in stock_history.items():
        if not history:
            print(f"\n  Item {item_id}: No data available")
            continue
        
        print(f"\n  Item {item_id}:")
        for date, stock in history:
            print(f"    {date}: {stock:,} in stock")
    
    # Get daily sales (calculated from trades delta)
    print("\n" + "="*60)
    print("Daily Sales Analysis")
    print("="*60 + "\n")
    
    daily_sales = tracker.get_daily_sales(example_items, days=7)
    
    for item_id, sales in daily_sales.items():
        if not sales:
            print(f"  Item {item_id}: Not enough data for analysis")
            continue
        
        print(f"\n  Item {item_id} - Daily Sales:")
        total_sales = 0
        for date, sold in sales:
            print(f"    {date}: {sold:,} sold")
            total_sales += sold
        
        avg_daily = total_sales / len(sales) if sales else 0
        print(f"    Average: {avg_daily:,.0f} per day")


async def example_trend_analysis():
    """Example: Detect trending items."""
    print("\n" + "="*60)
    print("Advanced Example: Trend Detection")
    print("="*60 + "\n")
    
    tracker = MarketHistoryTracker(region='eu')
    
    summary = tracker.get_summary()
    if summary['days_of_data'] < 7:
        print("⚠️ Need at least 7 days of data for trend analysis")
        print(f"   Current: {summary['days_of_data']} days")
        print("   Come back after collecting more data!")
        return
    
    # Analyze some items
    items = [16001, 16002, 44195, 721003]
    daily_sales = tracker.get_daily_sales(items, days=7)
    
    print("Trending Analysis:")
    for item_id, sales in daily_sales.items():
        if len(sales) < 7:
            continue
        
        # Compare first half vs second half
        mid = len(sales) // 2
        first_half = sum(s for _, s in sales[:mid]) / mid
        second_half = sum(s for _, s in sales[mid:]) / (len(sales) - mid)
        
        change = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if abs(change) > 20:  # More than 20% change
            trend = "🔥 UP" if change > 0 else "📉 DOWN"
            print(f"\n  Item {item_id}: {trend}")
            print(f"    Early period: {first_half:,.0f} sales/day")
            print(f"    Recent period: {second_half:,.0f} sales/day")
            print(f"    Change: {change:+.1f}%")


async def main():
    """Run all examples."""
    await example_basic_usage()
    
    # Only run trend analysis if we have data
    tracker = MarketHistoryTracker()
    if tracker.get_summary()['days_of_data'] >= 2:
        await example_trend_analysis()
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Run 'python record_market_snapshot.py' daily")
    print("2. Or use 'python watch_market_history.py' for automation")
    print("3. See MARKET_HISTORY_GUIDE.md for full documentation")
    print("="*60 + "\n")


if __name__ == '__main__':
    asyncio.run(main())

