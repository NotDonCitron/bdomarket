#!/usr/bin/env python3
"""
BDO Enhanced Flip Scanner

Scans market for profitable flip opportunities with intelligent analysis.

Features:
- Item names (auto-fetched)
- Competition scoring
- Market cycle timing
- Risk level filtering
"""
import argparse
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from utils.market_client import MarketClient
from utils.calculations import calculate_profit, calculate_roi, format_silver, format_percentage
from analyzer import MarketAnalyzer

console = Console()


@dataclass
class FlipCandidate:
    """A profitable flip opportunity."""
    item_id: int
    item_name: str
    buy_at: int
    sell_at: int
    profit: int
    roi: float
    stock: int
    trades: int
    competition_score: float
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'


class EnhancedFlipScanner:
    """Enhanced flip scanner with market intelligence."""
    
    def __init__(
        self,
        region: str = 'eu',
        tax_rate: float = 0.35,
        min_roi: float = 0.05,
        max_items: int = 150
    ):
        self.region = region
        self.tax_rate = tax_rate
        self.min_roi = min_roi
        self.max_items = max_items
        self.analyzer = MarketAnalyzer(region=region)
    
    async def scan(self, show_competition: bool = True, show_timing: bool = True) -> List[FlipCandidate]:
        """
        Scan market for flip opportunities.
        
        Args:
            show_competition: Include competition analysis
            show_timing: Include market timing info
            
        Returns:
            List of FlipCandidate objects
        """
        console.print("[bold cyan]BDO Enhanced Flip Scanner[/bold cyan]\n")
        
        # Show timing info if requested
        if show_timing:
            cycle = self.analyzer.get_market_cycle()
            console.print(f"[dim]Market Timing: {cycle.recommendation}[/dim]\n")
        
        async with MarketClient(region=self.region) as client:
            # Get market list
            console.print("[dim]Fetching market data...[/dim]")
            market_list = await client.get_market_list()
            
            if not market_list:
                console.print("[red]Failed to fetch market list![/red]")
                return []
            
            # Sort by trades and stock
            market_list.sort(key=lambda x: (x.get('totalTrades', 0), x.get('currentStock', 0)), reverse=True)
            
            # Select top items
            selected = market_list[:self.max_items]
            console.print(f"[dim]Analyzing top {len(selected)} items...[/dim]\n")
            
            # Scan for opportunities
            candidates = []
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Scanning items...", total=len(selected))
                
                # Process items one by one (batch not working reliably)
                for item_data in selected:
                    item_id = item_data['id']
                    
                    try:
                        # Fetch orderbook
                        orderbook = await client.get_orderbook(item_id)
                        
                        if not orderbook or not orderbook.orders:
                            progress.update(task, advance=1)
                            continue
                        
                        # Find flip opportunity
                        lowest_sell = None
                        highest_buy = None
                        
                        for order in orderbook.orders:
                            if order.sellers > 0:
                                if lowest_sell is None or order.price < lowest_sell:
                                    lowest_sell = order.price
                            if order.buyers > 0:
                                if highest_buy is None or order.price > highest_buy:
                                    highest_buy = order.price
                        
                        if not (lowest_sell and highest_buy):
                            progress.update(task, advance=1)
                            continue
                        
                        # Calculate profit and ROI
                        profit = calculate_profit(
                            buy_price=lowest_sell,
                            sell_price=highest_buy,
                            quantity=1,
                            tax_rate=self.tax_rate
                        )
                        roi = calculate_roi(lowest_sell, highest_buy, self.tax_rate)
                        
                        # Filter by ROI
                        if profit <= 0 or roi < self.min_roi:
                            progress.update(task, advance=1)
                            continue
                        
                        # Competition analysis if requested
                        competition_score = 0.0
                        if show_competition:
                            comp = self.analyzer.analyze_competition(orderbook)
                            competition_score = comp.score
                        
                        # Determine risk level
                        if competition_score < 0.3:
                            risk_level = "LOW"
                        elif competition_score < 0.6:
                            risk_level = "MEDIUM"
                        else:
                            risk_level = "HIGH"
                        
                        candidates.append(FlipCandidate(
                            item_id=item_id,
                            item_name=orderbook.item.name,
                            buy_at=lowest_sell,
                            sell_at=highest_buy,
                            profit=profit,
                            roi=roi,
                            stock=item_data.get('currentStock', 0),
                            trades=item_data.get('totalTrades', 0),
                            competition_score=competition_score,
                            risk_level=risk_level
                        ))
                        
                        progress.update(task, advance=1)
                    except Exception as e:
                        progress.update(task, advance=1)
                        continue
                    
                    # Small delay between requests
                    if (selected.index(item_data) + 1) % 10 == 0:
                        await asyncio.sleep(0.2)
            
            return candidates
    
    def display_results(
        self,
        candidates: List[FlipCandidate],
        filter_risk: Optional[str] = None,
        show_competition: bool = True
    ):
        """
        Display scan results.
        
        Args:
            candidates: List of FlipCandidate objects
            filter_risk: Filter by risk level ('LOW', 'MEDIUM', 'HIGH')
            show_competition: Show competition column
        """
        # Filter by risk if requested
        if filter_risk:
            candidates = [c for c in candidates if c.risk_level == filter_risk.upper()]
        
        if not candidates:
            console.print("[yellow]No candidates found with current filters.[/yellow]")
            return
        
        # Sort by ROI
        candidates.sort(key=lambda c: (c.roi, c.profit), reverse=True)
        
        # Display table
        table = Table(title=f"Top {len(candidates[:20])} Flip Candidates")
        table.add_column("ID", style="cyan")
        table.add_column("Item", style="bold")
        table.add_column("Buy", style="green", justify="right")
        table.add_column("Sell", style="yellow", justify="right")
        table.add_column("Profit", style="magenta", justify="right")
        table.add_column("ROI", style="bold", justify="right")
        
        if show_competition:
            table.add_column("Risk", style="dim", justify="center")
        
        table.add_column("Stock", style="dim", justify="right")
        
        for candidate in candidates[:20]:
            roi_color = "green" if candidate.roi > 0.2 else "yellow"
            risk_emoji = {
                'LOW': '✓',
                'MEDIUM': '~',
                'HIGH': '⚠'
            }.get(candidate.risk_level, '?')
            
            row = [
                str(candidate.item_id),
                candidate.item_name[:30],  # Truncate long names
                format_silver(candidate.buy_at),
                format_silver(candidate.sell_at),
                format_silver(candidate.profit),
                f"[{roi_color}]{format_percentage(candidate.roi)}[/{roi_color}]"
            ]
            
            if show_competition:
                row.append(f"{risk_emoji} {candidate.risk_level}")
            
            row.append(f"{candidate.stock:,}")
            
            table.add_row(*row)
        
        console.print(table)
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total candidates: {len(candidates)}")
        console.print(f"  Tax rate: {self.tax_rate * 100:.1f}%")
        console.print(f"  Min ROI: {self.min_roi * 100:.1f}%")
        
        if show_competition:
            low_risk = len([c for c in candidates if c.risk_level == 'LOW'])
            med_risk = len([c for c in candidates if c.risk_level == 'MEDIUM'])
            high_risk = len([c for c in candidates if c.risk_level == 'HIGH'])
            console.print(f"  Risk Distribution: {low_risk} LOW / {med_risk} MED / {high_risk} HIGH")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="BDO Enhanced Flip Scanner")
    parser.add_argument('--region', default='eu', choices=['eu', 'na', 'kr', 'sa'])
    parser.add_argument('--tax', type=float, default=0.35, help='Tax rate (default: 0.35)')
    parser.add_argument('--min-roi', type=float, default=0.05, help='Minimum ROI (default: 0.05)')
    parser.add_argument('--max-items', type=int, default=150, help='Max items to scan (default: 150)')
    parser.add_argument('--filter-risk', choices=['LOW', 'MEDIUM', 'HIGH'], help='Filter by risk level')
    parser.add_argument('--no-competition', action='store_true', help='Disable competition analysis')
    parser.add_argument('--no-timing', action='store_true', help='Disable timing info')
    
    args = parser.parse_args()
    
    scanner = EnhancedFlipScanner(
        region=args.region,
        tax_rate=args.tax,
        min_roi=args.min_roi,
        max_items=args.max_items
    )
    
    candidates = await scanner.scan(
        show_competition=not args.no_competition,
        show_timing=not args.no_timing
    )
    
    scanner.display_results(
        candidates,
        filter_risk=args.filter_risk,
        show_competition=not args.no_competition
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise

