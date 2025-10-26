#!/usr/bin/env python3
"""
BDO Portfolio Tracker

Tracks your trades with CSV-based logging and provides P&L reports.
"""
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from utils.market_client import MarketClient
from utils.calculations import calculate_profit, calculate_roi, format_silver, format_percentage
from utils.storage import load_json, save_json

console = Console()


@dataclass
class Trade:
    """Single trade entry."""
    timestamp: str
    item_id: int
    item_name: str
    qty: int
    price: int
    trade_type: str  # 'buy' or 'sell'
    notes: str = ""
    
    @property
    def total_cost(self) -> int:
        """Total cost/revenue of trade."""
        return self.qty * self.price


class PortfolioTracker:
    """Manages trading portfolio and P&L calculations."""
    
    def __init__(
        self,
        portfolio_path: str = "data/portfolio.csv",
        settings_path: str = "data/portfolio_settings.json"
    ):
        self.portfolio_path = Path(portfolio_path)
        self.settings_path = Path(settings_path)
        self.settings = self._load_settings()
        
        # Ensure data directory exists
        self.portfolio_path.parent.mkdir(exist_ok=True)
        
        # Ensure portfolio.csv exists
        if not self.portfolio_path.exists():
            df = pd.DataFrame(columns=[
                'timestamp', 'item_id', 'item_name', 'qty', 'price', 'type', 'notes'
            ])
            df.to_csv(self.portfolio_path, index=False)
            console.print(f"[green]Created portfolio file: {self.portfolio_path}[/green]")
    
    def _load_settings(self) -> Dict:
        """Load portfolio settings."""
        default_settings = {
            "tax_rate": 0.35,           # 35% base tax
            "value_pack": True,         # -30% tax reduction
            "familia_fame_bonus": 0.0,  # 0-5% bonus
        }
        
        if self.settings_path.exists():
            settings = load_json(str(self.settings_path))
            if settings:
                return {**default_settings, **settings}
        
        # Save default settings
        save_json(str(self.settings_path), default_settings)
        return default_settings
    
    def _calculate_effective_tax(self) -> float:
        """Calculate effective tax rate with bonuses."""
        base_tax = self.settings['tax_rate']
        
        if self.settings.get('value_pack', False):
            base_tax *= 0.7  # 30% reduction
        
        bonus = self.settings.get('familia_fame_bonus', 0.0)
        effective_tax = base_tax * (1 - bonus)
        
        return max(0.0, min(1.0, effective_tax))
    
    def log_trade(self, trade: Trade):
        """
        Log a trade to the portfolio CSV.
        
        Args:
            trade: Trade object to log
        """
        # Read existing portfolio
        df = pd.read_csv(self.portfolio_path)
        
        # Add new trade
        new_row = {
            'timestamp': trade.timestamp,
            'item_id': trade.item_id,
            'item_name': trade.item_name,
            'qty': trade.qty,
            'price': trade.price,
            'type': trade.trade_type,
            'notes': trade.notes
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(self.portfolio_path, index=False)
        
        console.print(f"[green]✓ Logged {trade.trade_type}: {trade.item_name} x{trade.qty} @ {format_silver(trade.price)}[/green]")
    
    async def interactive_log(self):
        """Interactive TUI for logging trades."""
        console.print("[bold cyan]Portfolio Trade Logger[/bold cyan]\n")
        
        # Get trade type
        trade_type = Prompt.ask(
            "Trade type",
            choices=["buy", "sell"],
            default="buy"
        )
        
        # Get item ID
        item_id_str = Prompt.ask("Item ID (e.g. 16001 for Black Stone)")
        try:
            item_id = int(item_id_str)
        except ValueError:
            console.print("[red]Invalid item ID![/red]")
            return
        
        # Fetch item name from market
        console.print(f"[dim]Fetching item info...[/dim]")
        async with MarketClient(region='eu') as client:
            orderbook = await client.get_orderbook(item_id)
            
            if orderbook and orderbook.item:
                item_name = orderbook.item.name
                console.print(f"[green]Item: {item_name}[/green]\n")
            else:
                item_name = f"Item_{item_id}"
                console.print(f"[yellow]Warning: Could not fetch item name, using {item_name}[/yellow]\n")
        
        # Get quantity
        qty_str = Prompt.ask("Quantity")
        try:
            qty = int(qty_str)
        except ValueError:
            console.print("[red]Invalid quantity![/red]")
            return
        
        # Get price
        price_str = Prompt.ask("Price per item (e.g. 177000)")
        try:
            price = int(price_str.replace(',', '').replace('.', ''))
        except ValueError:
            console.print("[red]Invalid price![/red]")
            return
        
        # Get notes
        notes = Prompt.ask("Notes (optional)", default="")
        
        # Confirm
        total = qty * price
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Type: {trade_type.upper()}")
        console.print(f"  Item: {item_name} (ID: {item_id})")
        console.print(f"  Qty: {qty:,}")
        console.print(f"  Price: {format_silver(price)} each")
        console.print(f"  Total: {format_silver(total)}")
        if notes:
            console.print(f"  Notes: {notes}")
        
        if Confirm.ask("\nLog this trade?"):
            trade = Trade(
                timestamp=datetime.now().isoformat(),
                item_id=item_id,
                item_name=item_name,
                qty=qty,
                price=price,
                trade_type=trade_type,
                notes=notes
            )
            self.log_trade(trade)
        else:
            console.print("[yellow]Trade cancelled[/yellow]")
    
    def generate_report(self):
        """Generate P&L report from portfolio."""
        console.print("[bold cyan]Portfolio P&L Report[/bold cyan]\n")
        
        # Read portfolio
        df = pd.read_csv(self.portfolio_path)
        
        if df.empty:
            console.print("[yellow]No trades logged yet![/yellow]")
            return
        
        # Group by item
        items = df.groupby('item_id')
        
        table = Table(title="Holdings & P&L")
        table.add_column("Item", style="bold")
        table.add_column("ID", style="dim")
        table.add_column("Bought", style="cyan", justify="right")
        table.add_column("Sold", style="yellow", justify="right")
        table.add_column("Holding", style="magenta", justify="right")
        table.add_column("Avg Buy", style="green", justify="right")
        table.add_column("Avg Sell", style="yellow", justify="right")
        table.add_column("Realized P&L", style="bold", justify="right")
        
        total_realized_pl = 0
        effective_tax = self._calculate_effective_tax()
        
        for item_id, trades in items:
            item_name = trades.iloc[0]['item_name']
            
            buys = trades[trades['type'] == 'buy']
            sells = trades[trades['type'] == 'sell']
            
            total_bought = buys['qty'].sum() if not buys.empty else 0
            total_sold = sells['qty'].sum() if not sells.empty else 0
            holding = total_bought - total_sold
            
            avg_buy_price = (buys['price'] * buys['qty']).sum() / total_bought if total_bought > 0 else 0
            avg_sell_price = (sells['price'] * sells['qty']).sum() / total_sold if total_sold > 0 else 0
            
            # Calculate realized P&L (on sold items)
            if total_sold > 0 and avg_buy_price > 0:
                realized_pl = calculate_profit(
                    buy_price=avg_buy_price,
                    sell_price=avg_sell_price,
                    quantity=total_sold,
                    tax_rate=effective_tax
                )
                total_realized_pl += realized_pl
                pl_str = format_silver(realized_pl)
                pl_color = "green" if realized_pl > 0 else "red"
            else:
                pl_str = "-"
                pl_color = "dim"
            
            table.add_row(
                item_name,
                str(item_id),
                f"{total_bought:,}" if total_bought > 0 else "-",
                f"{total_sold:,}" if total_sold > 0 else "-",
                f"{holding:,}" if holding > 0 else "-",
                format_silver(int(avg_buy_price)) if avg_buy_price > 0 else "-",
                format_silver(int(avg_sell_price)) if avg_sell_price > 0 else "-",
                f"[{pl_color}]{pl_str}[/{pl_color}]"
            )
        
        console.print(table)
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Effective Tax Rate: {effective_tax * 100:.1f}%")
        pl_color = "green" if total_realized_pl > 0 else "red"
        console.print(f"  Total Realized P&L: [{pl_color}]{format_silver(total_realized_pl)}[/{pl_color}]")
    
    async def live_status(self):
        """Show live portfolio status with current market prices."""
        console.print("[bold cyan]Live Portfolio Status[/bold cyan]\n")
        
        # Read portfolio
        df = pd.read_csv(self.portfolio_path)
        
        if df.empty:
            console.print("[yellow]No trades logged yet![/yellow]")
            return
        
        # Calculate holdings
        holdings = {}
        for _, trade in df.iterrows():
            item_id = trade['item_id']
            if item_id not in holdings:
                holdings[item_id] = {
                    'name': trade['item_name'],
                    'qty': 0,
                    'total_cost': 0
                }
            
            if trade['type'] == 'buy':
                holdings[item_id]['qty'] += trade['qty']
                holdings[item_id]['total_cost'] += trade['qty'] * trade['price']
            elif trade['type'] == 'sell':
                holdings[item_id]['qty'] -= trade['qty']
                holdings[item_id]['total_cost'] -= trade['qty'] * trade['price']
        
        # Filter only items we're holding
        current_holdings = {k: v for k, v in holdings.items() if v['qty'] > 0}
        
        if not current_holdings:
            console.print("[yellow]No current holdings (all sold)![/yellow]")
            return
        
        console.print(f"[dim]Fetching live prices for {len(current_holdings)} items...[/dim]\n")
        
        # Fetch live prices
        async with MarketClient(region='eu') as client:
            table = Table(title="Current Holdings (Live)")
            table.add_column("Item", style="bold")
            table.add_column("Holding", style="cyan", justify="right")
            table.add_column("Avg Buy", style="green", justify="right")
            table.add_column("Current Sell", style="yellow", justify="right")
            table.add_column("Unrealized P&L", style="bold", justify="right")
            table.add_column("ROI", style="magenta", justify="right")
            
            total_unrealized_pl = 0
            effective_tax = self._calculate_effective_tax()
            
            for item_id, holding in current_holdings.items():
                # Fetch current price
                orderbook = await client.get_orderbook(item_id)
                
                if orderbook and orderbook.orders:
                    # Find lowest sell price
                    lowest_sell = None
                    for order in orderbook.orders:
                        if order.sellers > 0:
                            if lowest_sell is None or order.price < lowest_sell:
                                lowest_sell = order.price
                    
                    if lowest_sell:
                        avg_buy = holding['total_cost'] / holding['qty']
                        unrealized_pl = calculate_profit(
                            buy_price=avg_buy,
                            sell_price=lowest_sell,
                            quantity=holding['qty'],
                            tax_rate=effective_tax
                        )
                        total_unrealized_pl += unrealized_pl
                        
                        roi = calculate_roi(avg_buy, lowest_sell, effective_tax)
                        
                        pl_color = "green" if unrealized_pl > 0 else "red"
                        roi_color = "green" if roi > 0 else "red"
                        
                        table.add_row(
                            holding['name'],
                            f"{holding['qty']:,}",
                            format_silver(int(avg_buy)),
                            format_silver(lowest_sell),
                            f"[{pl_color}]{format_silver(unrealized_pl)}[/{pl_color}]",
                            f"[{roi_color}]{format_percentage(roi)}[/{roi_color}]"
                        )
                    else:
                        table.add_row(
                            holding['name'],
                            f"{holding['qty']:,}",
                            format_silver(int(holding['total_cost'] / holding['qty'])),
                            "[dim]No sellers[/dim]",
                            "-",
                            "-"
                        )
                else:
                    table.add_row(
                        holding['name'],
                        f"{holding['qty']:,}",
                        format_silver(int(holding['total_cost'] / holding['qty'])),
                        "[dim]N/A[/dim]",
                        "-",
                        "-"
                    )
            
            console.print(table)
            
            # Summary
            console.print(f"\n[bold]Live Summary:[/bold]")
            pl_color = "green" if total_unrealized_pl > 0 else "red"
            console.print(f"  Total Unrealized P&L: [{pl_color}]{format_silver(total_unrealized_pl)}[/{pl_color}]")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="BDO Portfolio Tracker")
    parser.add_argument(
        'command',
        choices=['log', 'report', 'status'],
        help='Command to execute'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Show live prices (for status command)'
    )
    
    args = parser.parse_args()
    
    tracker = PortfolioTracker()
    
    if args.command == 'log':
        await tracker.interactive_log()
    elif args.command == 'report':
        tracker.generate_report()
    elif args.command == 'status':
        if args.live:
            await tracker.live_status()
        else:
            tracker.generate_report()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise

