#!/usr/bin/env python3
"""
BDO Market Trader - Authenticated trading CLI tool.

Executes trading actions on BDO Central Market:
- Buy items
- Sell items
- Cancel listings
- Collect funds
- View inventory
- View bid listings

Based on kookehs/bdo-marketplace functionality.
"""
import asyncio
import argparse
from rich.console import Console
from rich.table import Table
from rich import box

from utils.market_trader import MarketTrader, load_credentials, save_credentials, TradeCredentials
from utils.item_helper import ItemHelper


console = Console()


async def cmd_buy(args):
    """Buy an item from marketplace."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    # Resolve item name to ID if needed
    if args.item.isdigit():
        item_id = int(args.item)
    else:
        helper = ItemHelper(region=creds.region)
        item = await helper.search(args.item, limit=1)
        if not item:
            console.print(f"[red]❌ Item not found: {args.item}[/red]")
            return
        item_id = item[0]['id']
        console.print(f"[cyan]Found item: {item[0]['name']} (ID: {item_id})[/cyan]")
    
    # Execute buy
    async with MarketTrader(creds) as trader:
        console.print(f"\n[yellow]Placing buy order...[/yellow]")
        console.print(f"  Item ID: {item_id}")
        console.print(f"  Price: {args.price:,}")
        console.print(f"  Quantity: {args.quantity}")
        
        if not args.confirm:
            confirm = input("\n⚠️  Proceed with purchase? (y/N): ")
            if confirm.lower() != 'y':
                console.print("[yellow]Cancelled.[/yellow]")
                return
        
        result = await trader.buy_item(
            item_id=item_id,
            sid=args.sid,
            price=args.price,
            quantity=args.quantity
        )
        
        if result.success:
            console.print(f"\n[green]✅ {result.message}[/green]")
        else:
            console.print(f"\n[red]❌ {result.message}[/red]")
            if result.details:
                console.print(f"[dim]{result.details}[/dim]")


async def cmd_sell(args):
    """Sell an item to marketplace."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    # Resolve item name to ID if needed
    if args.item.isdigit():
        item_id = int(args.item)
    else:
        helper = ItemHelper(region=creds.region)
        item = await helper.search(args.item, limit=1)
        if not item:
            console.print(f"[red]❌ Item not found: {args.item}[/red]")
            return
        item_id = item[0]['id']
        console.print(f"[cyan]Found item: {item[0]['name']} (ID: {item_id})[/cyan]")
    
    # Execute sell
    async with MarketTrader(creds) as trader:
        console.print(f"\n[yellow]Placing sell order...[/yellow]")
        console.print(f"  Item ID: {item_id}")
        console.print(f"  Price: {args.price:,}")
        console.print(f"  Quantity: {args.quantity}")
        
        if not args.confirm:
            confirm = input("\n⚠️  Proceed with listing? (y/N): ")
            if confirm.lower() != 'y':
                console.print("[yellow]Cancelled.[/yellow]")
                return
        
        result = await trader.sell_item(
            item_id=item_id,
            sid=args.sid,
            price=args.price,
            quantity=args.quantity
        )
        
        if result.success:
            console.print(f"\n[green]✅ {result.message}[/green]")
        else:
            console.print(f"\n[red]❌ {result.message}[/red]")
            if result.details:
                console.print(f"[dim]{result.details}[/dim]")


async def cmd_cancel(args):
    """Cancel a listing."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    async with MarketTrader(creds) as trader:
        result = await trader.cancel_listing(
            item_id=args.item_id,
            sid=args.sid,
            order_no=args.order_no
        )
        
        if result.success:
            console.print(f"[green]✅ {result.message}[/green]")
        else:
            console.print(f"[red]❌ {result.message}[/red]")


async def cmd_collect(args):
    """Collect funds from completed sales."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    async with MarketTrader(creds) as trader:
        console.print("[yellow]Collecting funds...[/yellow]")
        result = await trader.collect_funds()
        
        if result.success:
            total = result.details.get('totalSilver', 0) if result.details else 0
            console.print(f"[green]✅ Collected: {total:,} silver[/green]")
        else:
            console.print(f"[red]❌ {result.message}[/red]")


async def cmd_inventory(args):
    """View Central Market inventory."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    async with MarketTrader(creds) as trader:
        inventory = await trader.get_inventory()
        
        if not inventory:
            console.print("[yellow]Inventory is empty.[/yellow]")
            return
        
        table = Table(title="Central Market Inventory", box=box.ROUNDED)
        table.add_column("Item ID", style="cyan")
        table.add_column("Name", style="bright_white")
        table.add_column("Quantity", style="green", justify="right")
        table.add_column("Enhancement", style="yellow")
        
        for item in inventory:
            table.add_row(
                str(item.get('mainKey', '?')),
                item.get('name', 'Unknown'),
                str(item.get('count', 0)),
                f"+{item.get('subKey', 0)}" if item.get('subKey', 0) > 0 else "-"
            )
        
        console.print(table)


async def cmd_listings(args):
    """View active bid/sell listings."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    async with MarketTrader(creds) as trader:
        listings = await trader.get_bid_listings()
        
        if not listings:
            console.print("[yellow]No active listings.[/yellow]")
            return
        
        table = Table(title="Active Listings", box=box.ROUNDED)
        table.add_column("Order #", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Item ID", style="cyan")
        table.add_column("Name", style="bright_white")
        table.add_column("Price", style="yellow", justify="right")
        table.add_column("Quantity", style="green", justify="right")
        
        for listing in listings:
            order_type = "BUY" if listing.get('isBuy') else "SELL"
            table.add_row(
                str(listing.get('orderNo', '?')),
                order_type,
                str(listing.get('mainKey', '?')),
                listing.get('name', 'Unknown'),
                f"{listing.get('price', 0):,}",
                str(listing.get('count', 0))
            )
        
        console.print(table)


async def cmd_funds(args):
    """View available trading funds."""
    creds = load_credentials()
    if not creds:
        console.print("[red]❌ No credentials found. Run 'trader.py auth' first.[/red]")
        return
    
    async with MarketTrader(creds) as trader:
        funds = await trader.get_funds_available()
        console.print(f"\n[green]Available funds: {funds:,} silver[/green]\n")


def cmd_auth(args):
    """Setup authentication credentials."""
    console.print("[cyan]═══ BDO Market Trader - Authentication Setup ═══[/cyan]\n")
    console.print("To trade on the Central Market, you need authentication cookies.")
    console.print("\n[yellow]Steps to get credentials:[/yellow]")
    console.print("  1. Log into https://market.blackdesertonline.com/ in your browser")
    console.print("  2. Open DevTools (F12) → Network tab")
    console.print("  3. Make any action (search for an item, etc.)")
    console.print("  4. Click on any request and check the 'Cookies' section")
    console.print("  5. Copy the values for these cookies:")
    console.print("     - [cyan]__RequestVerificationToken[/cyan]")
    console.print("     - [cyan]userNo[/cyan]\n")
    
    region = input("Region (eu/na/kr/sa) [eu]: ").strip().lower() or 'eu'
    session_id = input("__RequestVerificationToken: ").strip()
    user_no = input("userNo: ").strip()
    
    if not session_id or not user_no:
        console.print("\n[red]❌ Both cookies are required.[/red]")
        return
    
    creds = TradeCredentials(
        session_id=session_id,
        user_no=user_no,
        region=region
    )
    
    save_credentials(creds)
    console.print("\n[green]✅ Credentials saved to config/trader_auth.json[/green]")
    console.print("\n[yellow]⚠️  Note: These credentials will expire after your session ends.")
    console.print("     You'll need to update them periodically.[/yellow]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BDO Market Trader - Authenticated trading tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup authentication
  python trader.py auth
  
  # Buy 100 Black Stones at 180k each
  python trader.py buy "Black Stone" --price 180000 --quantity 100
  
  # Sell 50 Black Stones at 250k each
  python trader.py sell 16001 --price 250000 --quantity 50
  
  # View inventory
  python trader.py inventory
  
  # View active listings
  python trader.py listings
  
  # Collect funds
  python trader.py collect
  
  # Cancel a listing
  python trader.py cancel --item-id 16001 --order-no 12345
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Auth command
    parser_auth = subparsers.add_parser('auth', help='Setup authentication')
    parser_auth.set_defaults(func=cmd_auth)
    
    # Buy command
    parser_buy = subparsers.add_parser('buy', help='Buy an item')
    parser_buy.add_argument('item', help='Item ID or name')
    parser_buy.add_argument('--price', type=int, required=True, help='Buy price')
    parser_buy.add_argument('--quantity', type=int, default=1, help='Quantity to buy')
    parser_buy.add_argument('--sid', type=int, default=0, help='Sub-item ID (enhancement)')
    parser_buy.add_argument('--confirm', action='store_true', help='Skip confirmation')
    parser_buy.set_defaults(func=cmd_buy)
    
    # Sell command
    parser_sell = subparsers.add_parser('sell', help='Sell an item')
    parser_sell.add_argument('item', help='Item ID or name')
    parser_sell.add_argument('--price', type=int, required=True, help='Sell price')
    parser_sell.add_argument('--quantity', type=int, default=1, help='Quantity to sell')
    parser_sell.add_argument('--sid', type=int, default=0, help='Sub-item ID (enhancement)')
    parser_sell.add_argument('--confirm', action='store_true', help='Skip confirmation')
    parser_sell.set_defaults(func=cmd_sell)
    
    # Cancel command
    parser_cancel = subparsers.add_parser('cancel', help='Cancel a listing')
    parser_cancel.add_argument('--item-id', type=int, required=True, help='Item ID')
    parser_cancel.add_argument('--sid', type=int, default=0, help='Sub-item ID')
    parser_cancel.add_argument('--order-no', type=int, required=True, help='Order number')
    parser_cancel.set_defaults(func=cmd_cancel)
    
    # Collect command
    parser_collect = subparsers.add_parser('collect', help='Collect funds')
    parser_collect.set_defaults(func=cmd_collect)
    
    # Inventory command
    parser_inv = subparsers.add_parser('inventory', help='View inventory')
    parser_inv.set_defaults(func=cmd_inventory)
    
    # Listings command
    parser_list = subparsers.add_parser('listings', help='View active listings')
    parser_list.set_defaults(func=cmd_listings)
    
    # Funds command
    parser_funds = subparsers.add_parser('funds', help='View available funds')
    parser_funds.set_defaults(func=cmd_funds)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run command
    if asyncio.iscoroutinefunction(args.func):
        asyncio.run(args.func(args))
    else:
        args.func(args)


if __name__ == '__main__':
    main()



