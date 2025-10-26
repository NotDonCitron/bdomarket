"""
Test all relevant bdomarket API endpoints for Pearl monitoring.
"""
import asyncio
from bdomarket import Market
from bdomarket.identifiers import MarketRegion
from rich.console import Console
from rich.table import Table
from rich import box
import json

console = Console()


async def test_pearl_items():
    """Test get_pearl_items() - Should return ALL pearl items."""
    console.print("\n[cyan]=== Testing: get_pearl_items() ===[/cyan]\n")
    
    async with Market(region=MarketRegion.EU) as market:
        result = await market.post_pearl_items()
        
        if result.success:
            items = result.content if isinstance(result.content, list) else []
            console.print(f"[green]✅ Success![/green] Found {len(items)} pearl items")
            
            if items:
                table = Table(box=box.ROUNDED, title="Pearl Items (First 10)")
                table.add_column("ID", style="dim")
                table.add_column("Name", style="bright_white")
                table.add_column("Stock", style="green", justify="right")
                table.add_column("Price", style="yellow", justify="right")
                
                for item in items[:10]:
                    table.add_row(
                        str(item.get('id', '?')),
                        item.get('name', 'Unknown'),
                        str(item.get('stock', 0)),
                        f"{item.get('basePrice', 0):,}"
                    )
                
                console.print(table)
                
                # Count items with stock
                with_stock = [i for i in items if int(i.get('stock', 0) or 0) > 0]
                console.print(f"\n[yellow]Items with stock > 0: {len(with_stock)}[/yellow]")
            else:
                console.print("[yellow]No pearl items returned[/yellow]")
        else:
            console.print(f"[red]❌ Failed: {result.message}[/red]")
        
        return result


async def test_wait_list():
    """Test post_world_market_wait_list() - Items being registered."""
    console.print("\n[cyan]=== Testing: post_world_market_wait_list() ===[/cyan]\n")
    
    async with Market(region=MarketRegion.EU) as market:
        result = await market.post_world_market_wait_list()
        
        if result.success:
            items = result.content if isinstance(result.content, list) else []
            console.print(f"[green]✅ Success![/green] Found {len(items)} items in wait list")
            
            if items:
                table = Table(box=box.ROUNDED, title="Wait List (First 10)")
                table.add_column("ID", style="dim")
                table.add_column("Name", style="bright_white")
                table.add_column("Count", style="green", justify="right")
                table.add_column("Price", style="yellow", justify="right")
                
                for item in items[:10]:
                    table.add_row(
                        str(item.get('id', '?')),
                        item.get('name', 'Unknown'),
                        str(item.get('count', 0)),
                        f"{item.get('basePrice', 0):,}"
                    )
                
                console.print(table)
                
                # Check for pearl items (category 55)
                # Note: bdomarket might not include category info in wait list
                console.print(f"\n[yellow]Total wait list items: {len(items)}[/yellow]")
            else:
                console.print("[yellow]Wait list is empty[/yellow]")
        else:
            console.print(f"[red]❌ Failed: {result.message}[/red]")
        
        return result


async def test_hot_list():
    """Test post_world_market_hot_list() - Trending items."""
    console.print("\n[cyan]=== Testing: post_world_market_hot_list() ===[/cyan]\n")
    
    async with Market(region=MarketRegion.EU) as market:
        result = await market.post_world_market_hot_list()
        
        if result.success:
            items = result.content if isinstance(result.content, list) else []
            console.print(f"[green]✅ Success![/green] Found {len(items)} hot items")
            
            if items:
                table = Table(box=box.ROUNDED, title="Hot List (First 10)")
                table.add_column("ID", style="dim")
                table.add_column("Name", style="bright_white")
                table.add_column("Stock", style="green", justify="right")
                table.add_column("Price", style="yellow", justify="right")
                
                for item in items[:10]:
                    table.add_row(
                        str(item.get('id', '?')),
                        item.get('name', 'Unknown'),
                        str(item.get('stock', 0)),
                        f"{item.get('basePrice', 0):,}"
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No hot items[/yellow]")
        else:
            console.print(f"[red]❌ Failed: {result.message}[/red]")
        
        return result


async def test_market_list_pearl_category():
    """Test post_world_market_list() for Pearl category 55."""
    console.print("\n[cyan]=== Testing: post_world_market_list(55, 1) - Pearl Category ===[/cyan]\n")
    
    async with Market(region=MarketRegion.EU) as market:
        result = await market.post_world_market_list('55', '1')
        
        if result.success:
            items = result.content if isinstance(result.content, list) else []
            console.print(f"[green]✅ Success![/green] Found {len(items)} items in category 55-1")
            
            if items:
                table = Table(box=box.ROUNDED, title="Category 55-1 (First 10)")
                table.add_column("ID", style="dim")
                table.add_column("Name", style="bright_white")
                table.add_column("Stock", style="green", justify="right")
                table.add_column("Price", style="yellow", justify="right")
                
                for item in items[:10]:
                    table.add_row(
                        str(item.get('id', '?')),
                        item.get('name', 'Unknown'),
                        str(item.get('stock', 0)),
                        f"{item.get('basePrice', 0):,}"
                    )
                
                console.print(table)
                
                # Count with stock
                with_stock = [i for i in items if int(i.get('stock', 0) or 0) > 0]
                console.print(f"\n[yellow]Items with stock > 0: {len(with_stock)}[/yellow]")
            else:
                console.print("[yellow]No items in this category[/yellow]")
        else:
            console.print(f"[red]❌ Failed: {result.message}[/red]")
        
        return result


async def test_all_pearl_categories():
    """Test all 8 Pearl categories (55-1 through 55-8)."""
    console.print("\n[cyan]=== Testing: All Pearl Categories (55-1 to 55-8) ===[/cyan]\n")
    
    categories = [
        ("55", "1", "Männliche Outfits (Set)"),
        ("55", "2", "Weibliche Outfits (Set)"),
        ("55", "3", "Männliche Outfits (Einzel)"),
        ("55", "4", "Weibliche Outfits (Einzel)"),
        ("55", "5", "Klassen-Outfits (Set)"),
        ("55", "6", "Funktional"),
        ("55", "7", "Reittiere"),
        ("55", "8", "Begleiter (Pets)"),
    ]
    
    async with Market(region=MarketRegion.EU) as market:
        results = []
        total_items = 0
        total_with_stock = 0
        
        for main_cat, sub_cat, name in categories:
            result = await market.post_world_market_list(main_cat, sub_cat)
            
            if result.success:
                items = result.content if isinstance(result.content, list) else []
                with_stock = [i for i in items if int(i.get('stock', 0) or 0) > 0]
                
                total_items += len(items)
                total_with_stock += len(with_stock)
                
                status = f"[green]{len(items)} items, {len(with_stock)} with stock[/green]" if with_stock else f"[dim]{len(items)} items, 0 with stock[/dim]"
                console.print(f"  {name}: {status}")
                
                results.append((name, items, with_stock))
            else:
                console.print(f"  [red]{name}: Failed[/red]")
        
        console.print(f"\n[yellow]Total: {total_items} items, {total_with_stock} with stock[/yellow]")
        
        return results


async def compare_api_performance():
    """Compare response times of different APIs."""
    console.print("\n[cyan]=== API Performance Comparison ===[/cyan]\n")
    
    import time
    
    async with Market(region=MarketRegion.EU) as market:
        # Test 1: get_pearl_items()
        start = time.time()
        result1 = await market.post_pearl_items()
        time1 = time.time() - start
        
        # Test 2: All categories sequentially
        start = time.time()
        for i in range(1, 9):
            await market.post_world_market_list('55', str(i))
        time2 = time.time() - start
        
        # Test 3: Wait list
        start = time.time()
        result3 = await market.post_world_market_wait_list()
        time3 = time.time() - start
        
        # Test 4: Hot list
        start = time.time()
        result4 = await market.post_world_market_hot_list()
        time4 = time.time() - start
        
        table = Table(box=box.ROUNDED, title="API Performance")
        table.add_column("API", style="cyan")
        table.add_column("Time (s)", style="yellow", justify="right")
        table.add_column("Items", style="green", justify="right")
        
        table.add_row(
            "post_pearl_items()",
            f"{time1:.3f}",
            str(len(result1.content) if result1.success and result1.content else 0)
        )
        table.add_row(
            "8x post_world_market_list(55, X)",
            f"{time2:.3f}",
            "varies"
        )
        table.add_row(
            "post_world_market_wait_list()",
            f"{time3:.3f}",
            str(len(result3.content) if result3.success and result3.content else 0)
        )
        table.add_row(
            "post_world_market_hot_list()",
            f"{time4:.3f}",
            str(len(result4.content) if result4.success and result4.content else 0)
        )
        
        console.print(table)


async def main():
    """Run all tests."""
    console.print("\n[bold cyan]=======================================================[/bold cyan]")
    console.print("[bold cyan]      BDO MARKET API TESTING - PEARL MONITORING       [/bold cyan]")
    console.print("[bold cyan]=======================================================[/bold cyan]")
    
    try:
        # Test 1: Pearl Items API (dedicated endpoint)
        await test_pearl_items()
        
        # Test 2: Wait List (new registrations)
        await test_wait_list()
        
        # Test 3: Hot List (trending)
        await test_hot_list()
        
        # Test 4: Single Pearl Category
        await test_market_list_pearl_category()
        
        # Test 5: All Pearl Categories
        await test_all_pearl_categories()
        
        # Test 6: Performance Comparison
        await compare_api_performance()
        
        console.print("\n[bold green]=======================================================[/bold green]")
        console.print("[bold green]                   ALL TESTS COMPLETE                   [/bold green]")
        console.print("[bold green]=======================================================[/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]ERROR: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())

