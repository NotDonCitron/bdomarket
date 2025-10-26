#!/usr/bin/env python3
"""
Query Market History - Simple script to view collected data.

This script only READS data (no API calls), so it's fast and doesn't
have encoding issues.
"""
from rich.console import Console
from rich.table import Table

from utils.market_history_tracker import MarketHistoryTracker


console = Console()


def show_summary():
    """Show database summary."""
    tracker = MarketHistoryTracker(region='eu')
    summary = tracker.get_summary()
    
    console.print("\n[bold cyan]Market History Database Summary[/bold cyan]")
    console.print("=" * 60)
    
    if summary['total_snapshots'] == 0:
        console.print("\n[yellow]No data collected yet![/yellow]")
        console.print("Run: [cyan]python record_market_snapshot.py[/cyan]")
        return False
    
    console.print(f"Total Snapshots:  {summary['total_snapshots']}")
    console.print(f"Date Range:       {summary['date_range'][0]} to {summary['date_range'][1]}")
    console.print(f"Days of Data:     {summary['days_of_data']}")
    console.print(f"Latest Snapshot:  {summary['latest_snapshot']}")
    
    console.print("\n[dim]Available dates:[/dim]")
    dates = tracker.get_available_dates()
    for i in range(0, len(dates), 5):
        week = dates[i:i+5]
        console.print("  " + "  ".join(week))
    
    return True


def show_stock_history(item_ids, days=7):
    """Show stock history for items."""
    tracker = MarketHistoryTracker(region='eu')
    
    console.print(f"\n[bold cyan]Stock History (last {days} days)[/bold cyan]")
    console.print("=" * 60)
    
    stock_history = tracker.get_stock_history(item_ids, days=days)
    
    for item_id, history in stock_history.items():
        if not history:
            console.print(f"\n[yellow]Item {item_id}: No data[/yellow]")
            continue
        
        console.print(f"\n[bold]Item {item_id}:[/bold]")
        
        # Show last 10 days
        for date, stock in history[-10:]:
            console.print(f"  {date}: {stock:>8,} in stock")
        
        # Calculate trend
        if len(history) >= 2:
            first = history[0][1]
            last = history[-1][1]
            change = last - first
            pct = (change / first * 100) if first > 0 else 0
            
            trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            console.print(f"  [dim]Trend: {change:+,} ({pct:+.1f}%) {trend}[/dim]")


def show_daily_sales(item_ids, days=7):
    """Show daily sales for items."""
    tracker = MarketHistoryTracker(region='eu')
    
    console.print(f"\n[bold cyan]Daily Sales (last {days} days)[/bold cyan]")
    console.print("=" * 60)
    
    daily_sales = tracker.get_daily_sales(item_ids, days=days)
    
    for item_id, sales in daily_sales.items():
        if not sales:
            console.print(f"\n[yellow]Item {item_id}: Need 2+ days of data[/yellow]")
            continue
        
        console.print(f"\n[bold]Item {item_id}:[/bold]")
        
        total = 0
        for date, sold in sales[-10:]:
            console.print(f"  {date}: {sold:>8,} sold")
            total += sold
        
        avg = total / len(sales) if sales else 0
        console.print(f"  [dim]Average: {avg:,.0f} per day[/dim]")


def show_comparison_table(item_ids, days=7):
    """Show comparison table for multiple items."""
    tracker = MarketHistoryTracker(region='eu')
    
    console.print(f"\n[bold cyan]Item Comparison (last {days} days)[/bold cyan]\n")
    
    table = Table(title="Market Activity")
    table.add_column("Item ID", style="cyan")
    table.add_column("Latest Stock", justify="right")
    table.add_column("Avg Stock", justify="right")
    table.add_column("Daily Sales", justify="right")
    table.add_column("Trend", justify="center")
    
    stock_history = tracker.get_stock_history(item_ids, days=days)
    daily_sales = tracker.get_daily_sales(item_ids, days=days)
    
    for item_id in item_ids:
        history = stock_history.get(item_id, [])
        sales = daily_sales.get(item_id, [])
        
        if not history:
            continue
        
        latest_stock = history[-1][1] if history else 0
        avg_stock = sum(s for _, s in history) // len(history) if history else 0
        avg_sales = sum(s for _, s in sales) // len(sales) if sales else 0
        
        # Trend
        if len(history) >= 2:
            first = history[0][1]
            last = history[-1][1]
            if last > first * 1.1:
                trend = "📈 Up"
            elif last < first * 0.9:
                trend = "📉 Down"
            else:
                trend = "➡️ Flat"
        else:
            trend = "—"
        
        table.add_row(
            str(item_id),
            f"{latest_stock:,}",
            f"{avg_stock:,}",
            f"{avg_sales:,}",
            trend
        )
    
    console.print(table)


def main():
    """Main function."""
    console.print("\n[bold green]Market History Query Tool[/bold green]")
    console.print("[dim]Read-only queries (no API calls)[/dim]")
    
    # Show summary
    has_data = show_summary()
    
    if not has_data:
        return
    
    # Example: Popular trading items
    # Black Stone (Weapon), Black Stone (Armor), Caphras Stone
    example_items = [16001, 16002, 44195]
    
    # Get number of days
    tracker = MarketHistoryTracker()
    days_available = tracker.get_summary()['days_of_data']
    days_to_show = min(7, days_available)
    
    # Show detailed views
    show_stock_history(example_items, days=days_to_show)
    
    if days_available >= 2:
        show_daily_sales(example_items, days=days_to_show)
        show_comparison_table(example_items, days=days_to_show)
    else:
        console.print("\n[yellow]Need 2+ days for sales calculations[/yellow]")
    
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("- Add your own item IDs to example_items list")
    console.print("- Collect more days for better trends")
    console.print("- See MARKET_HISTORY_GUIDE.md for API usage")


if __name__ == '__main__':
    main()

