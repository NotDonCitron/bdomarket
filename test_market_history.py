#!/usr/bin/env python3
"""
Test and demonstrate market history tracking functionality.

This shows how to:
1. Record snapshots
2. Query stock history
3. Query trades history  
4. Calculate daily sales
"""
import asyncio
from rich.console import Console
from rich.table import Table

from utils.market_history_tracker import MarketHistoryTracker
from utils.item_helper import ItemHelper


console = Console()


async def test_record_snapshot():
    """Test recording a market snapshot."""
    console.print("\n[bold]Test 1: Recording Market Snapshot[/bold]")
    console.print("=" * 60)
    
    tracker = MarketHistoryTracker(region='eu')
    
    console.print("Recording snapshot (this may take 10-20 seconds)...")
    success = await tracker.record_snapshot(verbose=True)
    
    if success:
        console.print("[green]✓ Snapshot recorded successfully[/green]")
    else:
        console.print("[red]✗ Failed to record snapshot[/red]")
    
    return success


def test_query_history():
    """Test querying historical data."""
    console.print("\n[bold]Test 2: Querying Historical Data[/bold]")
    console.print("=" * 60)
    
    tracker = MarketHistoryTracker(region='eu')
    
    # Show summary
    summary = tracker.get_summary()
    console.print(f"\nData Summary:")
    console.print(f"  Total snapshots: {summary['total_snapshots']}")
    console.print(f"  Days of data: {summary['days_of_data']}")
    
    if summary['total_snapshots'] == 0:
        console.print("\n[yellow]No historical data yet![/yellow]")
        console.print("Run [cyan]python record_market_snapshot.py[/cyan] to collect data")
        return False
    
    console.print(f"  Latest snapshot: {summary['latest_snapshot']}")
    
    # Query some popular items
    # Black Stone (Weapon), Black Stone (Armor), Caphras Stone
    test_items = [16001, 16002, 44195]
    
    console.print(f"\n[bold cyan]Stock History (last 7 days)[/bold cyan]")
    stock_history = tracker.get_stock_history(test_items, days=7)
    
    for item_id, history in stock_history.items():
        if history:
            console.print(f"\nItem {item_id}:")
            for date, stock in history[-7:]:  # Last 7 days
                console.print(f"  {date}: {stock:,} in stock")
    
    console.print(f"\n[bold cyan]Trades History (last 7 days)[/bold cyan]")
    trades_history = tracker.get_trades_history(test_items, days=7)
    
    for item_id, history in trades_history.items():
        if history:
            console.print(f"\nItem {item_id}:")
            for date, trades in history[-7:]:
                console.print(f"  {date}: {trades:,} total trades")
    
    console.print(f"\n[bold cyan]Daily Sales (calculated)[/bold cyan]")
    daily_sales = tracker.get_daily_sales(test_items, days=7)
    
    for item_id, sales in daily_sales.items():
        if sales:
            console.print(f"\nItem {item_id}:")
            for date, sold in sales[-7:]:
                console.print(f"  {date}: {sold:,} sold that day")
    
    return True


async def demo_with_item_names():
    """Demonstrate with actual item names."""
    console.print("\n[bold]Demo: Historical Data with Item Names[/bold]")
    console.print("=" * 60)
    
    tracker = MarketHistoryTracker(region='eu')
    helper = ItemHelper(region='eu')
    
    summary = tracker.get_summary()
    if summary['total_snapshots'] == 0:
        console.print("[yellow]No data to display yet[/yellow]")
        return
    
    # Popular items
    items_to_check = [
        16001,  # Black Stone (Weapon)
        16002,  # Black Stone (Armor)
        44195,  # Caphras Stone
        721003, # Sharp Black Crystal Shard
        15640,  # Memory Fragment
    ]
    
    # Get item names
    await helper.init()
    
    console.print(f"\n[bold]Stock Trends (past {min(7, summary['days_of_data'])} days)[/bold]\n")
    
    table = Table(title="Stock History")
    table.add_column("Item", style="cyan")
    table.add_column("Latest", justify="right")
    table.add_column("7d Avg", justify="right")
    table.add_column("Trend", justify="center")
    
    stock_history = tracker.get_stock_history(items_to_check, days=7)
    
    for item_id in items_to_check:
        history = stock_history.get(item_id, [])
        if not history:
            continue
        
        item_info = await helper.get_by_id(item_id)
        item_name = item_info.name if item_info else f"Item {item_id}"
        
        latest_stock = history[-1][1] if history else 0
        avg_stock = sum(s for _, s in history) // len(history) if history else 0
        
        # Calculate trend
        if len(history) >= 2:
            first_half = sum(s for _, s in history[:len(history)//2]) / (len(history)//2)
            second_half = sum(s for _, s in history[len(history)//2:]) / (len(history) - len(history)//2)
            
            if second_half > first_half * 1.1:
                trend = "📈 Up"
            elif second_half < first_half * 0.9:
                trend = "📉 Down"
            else:
                trend = "➡️ Stable"
        else:
            trend = "—"
        
        table.add_row(
            item_name[:30],
            f"{latest_stock:,}",
            f"{avg_stock:,}",
            trend
        )
    
    console.print(table)
    
    # Daily sales table
    console.print(f"\n[bold]Trading Activity (Daily Sales)[/bold]\n")
    
    sales_table = Table(title="Daily Sales")
    sales_table.add_column("Item", style="cyan")
    sales_table.add_column("Yesterday", justify="right")
    sales_table.add_column("7d Avg", justify="right")
    sales_table.add_column("Volume", justify="center")
    
    daily_sales = tracker.get_daily_sales(items_to_check, days=7)
    
    for item_id in items_to_check:
        sales = daily_sales.get(item_id, [])
        if not sales:
            continue
        
        item_info = await helper.get_by_id(item_id)
        item_name = item_info.name if item_info else f"Item {item_id}"
        
        yesterday = sales[-1][1] if sales else 0
        avg_sales = sum(s for _, s in sales) // len(sales) if sales else 0
        
        # Volume rating
        if avg_sales > 1000:
            volume = "🔥 High"
        elif avg_sales > 100:
            volume = "📊 Medium"
        else:
            volume = "📉 Low"
        
        sales_table.add_row(
            item_name[:30],
            f"{yesterday:,}",
            f"{avg_sales:,}",
            volume
        )
    
    console.print(sales_table)


async def main():
    """Run all tests and demos."""
    console.print("\n[bold green]Market History Tracking - Test Suite[/bold green]")
    console.print("[dim]This demonstrates how to collect and query market history data[/dim]")
    
    # Test 1: Record snapshot
    success = await test_record_snapshot()
    
    if not success:
        console.print("\n[red]Cannot proceed with tests - snapshot recording failed[/red]")
        return
    
    # Test 2: Query history
    test_query_history()
    
    # Demo: With names
    await demo_with_item_names()
    
    console.print("\n[bold green]✓ All tests completed![/bold green]")
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Run [cyan]python record_market_snapshot.py[/cyan] daily")
    console.print("2. After 7-90 days, you'll have rich historical data")
    console.print("3. Use the API to query trends:")
    console.print("   [dim]stock_history = tracker.get_stock_history([16001], days=90)[/dim]")
    console.print("   [dim]daily_sales = tracker.get_daily_sales([16001], days=30)[/dim]")


if __name__ == '__main__':
    asyncio.run(main())

