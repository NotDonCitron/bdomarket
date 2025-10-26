#!/usr/bin/env python3
"""
BDO Item Sniper - Price Alert Tool

Monitors items from watchlist and alerts when prices hit targets.
"""
import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console
from rich.table import Table

from utils.market_client import MarketClient
from utils.item_helper import ItemHelper
from utils.calculations import calculate_roi, format_silver, format_percentage


console = Console()


class WatchlistItem:
    """A single item to watch."""
    
    def __init__(
        self,
        item_id: int,
        item_name: str,
        target_buy_max: Optional[int] = None,
        target_sell_min: Optional[int] = None,
        alert_on: str = "both"
    ):
        self.item_id = item_id
        self.item_name = item_name
        self.target_buy_max = target_buy_max
        self.target_sell_min = target_sell_min
        self.alert_on = alert_on  # "buy", "sell", "both"
        
        # Track last seen prices to avoid spam
        self.last_buy_price: Optional[int] = None
        self.last_sell_price: Optional[int] = None
    
    def should_alert_buy(self, current_price: int) -> bool:
        """Check if we should alert for buy price."""
        if self.alert_on not in ("buy", "both"):
            return False
        if self.target_buy_max is None:
            return False
        if current_price > self.target_buy_max:
            return False
        # Alert if price changed or first time
        return self.last_buy_price != current_price
    
    def should_alert_sell(self, current_price: int) -> bool:
        """Check if we should alert for sell price."""
        if self.alert_on not in ("sell", "both"):
            return False
        if self.target_sell_min is None:
            return False
        if current_price < self.target_sell_min:
            return False
        return self.last_sell_price != current_price


class ItemSniper:
    """Main sniper class."""
    
    def __init__(self, config_path: str = "config/sniper_watchlist.yaml"):
        self.config_path = Path(config_path)
        self.watchlist: List[WatchlistItem] = []
        self.region = "eu"
        self.poll_interval = 5
        self.webhook = None
        self.item_helper = ItemHelper()
        self.client: Optional[MarketClient] = None
    
    def load_config(self) -> bool:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            console.print(f"[red]Config file not found: {self.config_path}[/red]")
            console.print("[yellow]Create config/sniper_watchlist.yaml from example[/yellow]")
            return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            console.print(f"[red]Failed to load config: {e}[/red]")
            return False
        
        # Load settings
        self.region = config.get('region', 'eu')
        self.poll_interval = config.get('poll_interval', 5)
        self.webhook = config.get('webhook')
        
        # Load watchlist
        watchlist_items = config.get('watchlist', [])
        if not watchlist_items:
            console.print("[yellow]Watchlist is empty![/yellow]")
            return False
        
        for item_cfg in watchlist_items:
            # Resolve item name to ID if needed
            if 'id' in item_cfg:
                item_id = item_cfg['id']
                # Item name will be fetched from orderbook later
                item_name = item_cfg.get('name', f"Item_{item_id}")
            elif 'name' in item_cfg:
                item_name = item_cfg['name']
                # For now, user must provide ID
                # We'll fetch real name from orderbook on first check
                console.print(f"[yellow]Note: Item '{item_name}' must have 'id' field. Skipping.[/yellow]")
                console.print(f"[dim]Search by name coming soon. Please add 'id' field to config.[/dim]")
                continue
            else:
                console.print(f"[yellow]Skipping invalid watchlist entry (no 'id')[/yellow]")
                continue
            
            watch_item = WatchlistItem(
                item_id=item_id,
                item_name=item_name,
                target_buy_max=item_cfg.get('target_buy_max'),
                target_sell_min=item_cfg.get('target_sell_min'),
                alert_on=item_cfg.get('alert_on', 'both')
            )
            self.watchlist.append(watch_item)
        
        return True
    
    async def check_item(self, watch_item: WatchlistItem) -> Optional[Dict]:
        """
        Check a single item and return alert info if triggered.
        
        Returns:
            Dict with alert info or None
        """
        try:
            orderbook = await self.client.get_orderbook(watch_item.item_id)
        except Exception as e:
            console.print(f"[red]Error fetching {watch_item.item_name}: {e}[/red]")
            return None
        
        if not orderbook or not orderbook.orders:
            return None
        
        # Update item name if we got a real one
        if orderbook.item and orderbook.item.name and not orderbook.item.name.startswith("Item_"):
            watch_item.item_name = orderbook.item.name
        
        # Find lowest sell (ask) and highest buy (bid)
        lowest_sell = None
        highest_buy = None
        
        for order in orderbook.orders:
            if order.sellers > 0:
                if lowest_sell is None or order.price < lowest_sell:
                    lowest_sell = order.price
            if order.buyers > 0:
                if highest_buy is None or order.price > highest_buy:
                    highest_buy = order.price
        
        alerts = []
        
        # Check buy alert (we want to buy at low price)
        if lowest_sell and watch_item.should_alert_buy(lowest_sell):
            diff_pct = ((watch_item.target_buy_max - lowest_sell) / watch_item.target_buy_max) * 100
            alerts.append({
                'type': 'BUY',
                'price': lowest_sell,
                'target': watch_item.target_buy_max,
                'diff_pct': diff_pct
            })
            watch_item.last_buy_price = lowest_sell
        
        # Check sell alert (we want to sell at high price)
        if highest_buy and watch_item.should_alert_sell(highest_buy):
            diff_pct = ((highest_buy - watch_item.target_sell_min) / watch_item.target_sell_min) * 100
            alerts.append({
                'type': 'SELL',
                'price': highest_buy,
                'target': watch_item.target_sell_min,
                'diff_pct': diff_pct
            })
            watch_item.last_sell_price = highest_buy
        
        if not alerts:
            return None
        
        # Calculate potential ROI if both prices available
        roi = None
        if lowest_sell and highest_buy:
            roi = calculate_roi(lowest_sell, highest_buy, tax_rate=0.35)
        
        return {
            'item': watch_item,
            'alerts': alerts,
            'lowest_sell': lowest_sell,
            'highest_buy': highest_buy,
            'roi': roi
        }
    
    def print_alert(self, alert_info: Dict):
        """Print alert to console with nice formatting."""
        item = alert_info['item']
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Beep!
        print('\a', end='')
        
        # Build alert message
        console.print(f"\n[bold yellow]🔔 ALERT![/bold yellow] {timestamp} - [bold]{item.item_name}[/bold]")
        
        for alert in alert_info['alerts']:
            alert_type = alert['type']
            price = alert['price']
            target = alert['target']
            diff_pct = alert['diff_pct']
            
            if alert_type == 'BUY':
                console.print(f"  [green]✓ BUY:[/green] {format_silver(price)} (Target: <{format_silver(target)}) | {diff_pct:+.1f}%")
            else:
                console.print(f"  [green]✓ SELL:[/green] {format_silver(price)} (Target: >{format_silver(target)}) | {diff_pct:+.1f}%")
        
        # Show ROI if available
        if alert_info['roi'] is not None:
            roi = alert_info['roi']
            roi_color = "green" if roi > 0 else "red"
            console.print(f"  [cyan]Potential ROI:[/cyan] [{roi_color}]{format_percentage(roi)}[/{roi_color}]")
    
    async def run(self):
        """Main monitoring loop."""
        console.print("[bold green]BDO Item Sniper[/bold green]")
        console.print(f"Region: {self.region} | Poll interval: {self.poll_interval}s")
        console.print(f"Watching {len(self.watchlist)} items\n")
        
        # Show watchlist
        table = Table(title="Watchlist")
        table.add_column("ID", style="cyan")
        table.add_column("Item", style="bold")
        table.add_column("Buy Alert", style="green")
        table.add_column("Sell Alert", style="yellow")
        
        for item in self.watchlist:
            buy_str = format_silver(item.target_buy_max) if item.target_buy_max else "-"
            sell_str = format_silver(item.target_sell_min) if item.target_sell_min else "-"
            table.add_row(str(item.item_id), item.item_name, f"≤ {buy_str}", f"≥ {sell_str}")
        
        console.print(table)
        console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")
        
        async with MarketClient(region=self.region) as client:
            self.client = client
            
            while True:
                try:
                    # Check all items
                    tasks = [self.check_item(item) for item in self.watchlist]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results:
                        if isinstance(result, Exception):
                            continue
                        if result:
                            self.print_alert(result)
                    
                    # Wait for next poll
                    await asyncio.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping sniper...[/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(5)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="BDO Item Sniper - Price Alert Tool")
    parser.add_argument(
        '--config',
        default='config/sniper_watchlist.yaml',
        help='Path to watchlist config file'
    )
    
    args = parser.parse_args()
    
    sniper = ItemSniper(config_path=args.config)
    
    if not sniper.load_config():
        console.print("[red]Failed to load configuration[/red]")
        sys.exit(1)
    
    try:
        asyncio.run(sniper.run())
    except KeyboardInterrupt:
        console.print("\n[green]Goodbye![/green]")
        sys.exit(0)


if __name__ == "__main__":
    main()

