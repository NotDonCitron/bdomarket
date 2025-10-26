#!/usr/bin/env python3
"""Test hot list and wait list functionality."""
import asyncio
from utils.market_client import MarketClient
from rich.console import Console
from rich.table import Table
from rich import box


console = Console()


async def test_hot_and_wait_lists():
    """Test hot list and wait list features."""
    async with MarketClient(region='eu') as client:
        # Test hot list
        console.print("\n[cyan]═══ Hot Items (Trending) ═══[/cyan]\n")
        hot_items = await client.get_hot_list()
        
        if hot_items:
            table = Table(box=box.ROUNDED)
            table.add_column("ID", style="dim")
            table.add_column("Name", style="bright_white")
            table.add_column("Price", style="yellow", justify="right")
            table.add_column("Stock", style="green", justify="right")
            
            for item in hot_items[:20]:  # Show top 20
                table.add_row(
                    str(item.get('id', '?')),
                    item.get('name', 'Unknown'),
                    f"{item.get('basePrice', 0):,}",
                    str(item.get('stock', 0))
                )
            
            console.print(table)
        else:
            console.print("[yellow]No hot items found.[/yellow]")
        
        # Test wait list
        console.print("\n[cyan]═══ Wait List (Low Stock) ═══[/cyan]\n")
        wait_items = await client.get_wait_list()
        
        if wait_items:
            table = Table(box=box.ROUNDED)
            table.add_column("ID", style="dim")
            table.add_column("Name", style="bright_white")
            table.add_column("Price", style="yellow", justify="right")
            table.add_column("Stock", style="red", justify="right")
            
            for item in wait_items[:20]:  # Show top 20
                table.add_row(
                    str(item.get('id', '?')),
                    item.get('name', 'Unknown'),
                    f"{item.get('basePrice', 0):,}",
                    str(item.get('stock', 0))
                )
            
            console.print(table)
        else:
            console.print("[yellow]No wait list items found.[/yellow]")
        
        console.print("\n[green]✅ Test completed![/green]")


if __name__ == '__main__':
    asyncio.run(test_hot_and_wait_lists())



