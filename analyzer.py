#!/usr/bin/env python3
"""
BDO Market Analysis Engine

Provides heuristic-based market analysis:
- Competition Monitor (orderbook density)
- Market Cycle Detector (time-based patterns)
- Whale Watch (stock anomalies)
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

from rich.console import Console
from rich.table import Table

from utils.market_client import MarketClient, OrderbookData
from utils.calculations import format_silver

console = Console()


@dataclass
class CompetitionScore:
    """Competition analysis for an item."""
    item_id: int
    item_name: str
    score: float  # 0.0 (empty) to 1.0 (overcrowded)
    buyer_count: int
    seller_count: int
    buyer_density: float  # buyers per price level
    seller_density: float  # sellers per price level
    has_walls: bool  # Large order concentrations
    recommendation: str


@dataclass
class MarketCycleInfo:
    """Market cycle timing information."""
    current_hour: int
    is_peak_time: bool  # 18-22 UTC
    is_weekend: bool
    recommendation: str


class MarketAnalyzer:
    """Analyzes market conditions and provides trading insights."""
    
    def __init__(self, region: str = 'eu', history_dir: str = 'data/market_history'):
        self.region = region
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True, parents=True)
    
    def analyze_competition(self, orderbook: OrderbookData) -> CompetitionScore:
        """
        Analyze competition level for an item.
        
        Args:
            orderbook: OrderbookData from market client
            
        Returns:
            CompetitionScore with analysis
            
        Scoring Logic:
            - Empty orderbook: 0.0 (great opportunity)
            - Light competition: 0.0-0.3 (good)
            - Moderate: 0.3-0.6 (fair)
            - Heavy: 0.6-0.8 (risky)
            - Overcrowded: 0.8-1.0 (avoid)
        """
        if not orderbook.orders:
            return CompetitionScore(
                item_id=orderbook.item.id,
                item_name=orderbook.item.name,
                score=0.0,
                buyer_count=0,
                seller_count=0,
                buyer_density=0.0,
                seller_density=0.0,
                has_walls=False,
                recommendation="Empty market - great for flip!"
            )
        
        # Count buyers/sellers
        total_buyers = sum(order.buyers for order in orderbook.orders)
        total_sellers = sum(order.sellers for order in orderbook.orders)
        
        # Calculate density (orders per price level)
        active_levels = len([o for o in orderbook.orders if o.buyers > 0 or o.sellers > 0])
        buyer_density = total_buyers / max(1, active_levels)
        seller_density = total_sellers / max(1, active_levels)
        
        # Detect walls (single order > 30% of total)
        has_walls = False
        if total_buyers > 0:
            max_buyer_order = max(order.buyers for order in orderbook.orders)
            if max_buyer_order > total_buyers * 0.3:
                has_walls = True
        if total_sellers > 0:
            max_seller_order = max(order.sellers for order in orderbook.orders)
            if max_seller_order > total_sellers * 0.3:
                has_walls = True
        
        # Calculate competition score
        # Factors: total orders, density, and walls
        score = 0.0
        
        # Factor 1: Total volume (normalized to 0-0.4)
        total_volume = total_buyers + total_sellers
        volume_score = min(0.4, total_volume / 10000)
        score += volume_score
        
        # Factor 2: Density (normalized to 0-0.4)
        avg_density = (buyer_density + seller_density) / 2
        density_score = min(0.4, avg_density / 500)
        score += density_score
        
        # Factor 3: Walls (adds 0.2 if present)
        if has_walls:
            score += 0.2
        
        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))
        
        # Generate recommendation
        if score < 0.3:
            recommendation = "✓ LOW competition - good opportunity"
        elif score < 0.6:
            recommendation = "~ MODERATE competition - fair"
        elif score < 0.8:
            recommendation = "⚠ HIGH competition - risky"
        else:
            recommendation = "✗ OVERCROWDED - avoid"
        
        return CompetitionScore(
            item_id=orderbook.item.id,
            item_name=orderbook.item.name,
            score=score,
            buyer_count=total_buyers,
            seller_count=total_sellers,
            buyer_density=buyer_density,
            seller_density=seller_density,
            has_walls=has_walls,
            recommendation=recommendation
        )
    
    def get_market_cycle(self) -> MarketCycleInfo:
        """
        Get current market cycle information.
        
        Returns:
            MarketCycleInfo with timing recommendations
            
        Heuristics:
            - Peak hours: 18:00-22:00 UTC (EU prime time)
            - Weekend: Saturday/Sunday (more players online)
            - Best time to sell: Peak + Weekend
            - Best time to buy: Off-peak weekdays
        """
        now = datetime.now()
        current_hour = now.hour
        is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6
        
        # Peak hours: 18-22 UTC
        is_peak_time = 18 <= current_hour < 22
        
        # Generate recommendation
        if is_peak_time and is_weekend:
            recommendation = "✓ BEST TIME TO SELL (peak + weekend)"
        elif is_peak_time:
            recommendation = "✓ GOOD TIME TO SELL (peak hours)"
        elif is_weekend:
            recommendation = "~ FAIR TIME (weekend, but off-peak)"
        else:
            recommendation = "✓ GOOD TIME TO BUY (off-peak)"
        
        return MarketCycleInfo(
            current_hour=current_hour,
            is_peak_time=is_peak_time,
            is_weekend=is_weekend,
            recommendation=recommendation
        )
    
    def save_snapshot(self, item_id: int, orderbook: OrderbookData, competition: CompetitionScore):
        """
        Save market snapshot to JSONL for historical analysis.
        
        Args:
            item_id: Item ID
            orderbook: OrderbookData
            competition: CompetitionScore
        """
        snapshot_file = self.history_dir / f"item_{item_id}.jsonl"
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'item_id': item_id,
            'item_name': orderbook.item.name,
            'competition_score': competition.score,
            'buyers': competition.buyer_count,
            'sellers': competition.seller_count,
            'price_levels': len(orderbook.orders),
            'orders': [
                {
                    'price': order.price,
                    'buyers': order.buyers,
                    'sellers': order.sellers
                }
                for order in orderbook.orders
            ]
        }
        
        # Append to JSONL
        with open(snapshot_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(snapshot) + '\n')
    
    async def analyze_item(self, item_id: int, save_history: bool = False) -> Optional[CompetitionScore]:
        """
        Analyze a single item.
        
        Args:
            item_id: Item ID
            save_history: Whether to save snapshot to history
            
        Returns:
            CompetitionScore or None
        """
        async with MarketClient(region=self.region) as client:
            orderbook = await client.get_orderbook(item_id)
            
            if not orderbook:
                console.print(f"[red]Failed to fetch orderbook for item {item_id}[/red]")
                return None
            
            competition = self.analyze_competition(orderbook)
            
            if save_history:
                self.save_snapshot(item_id, orderbook, competition)
            
            return competition
    
    async def analyze_batch(
        self,
        item_ids: List[int],
        save_history: bool = False
    ) -> Dict[int, CompetitionScore]:
        """
        Analyze multiple items.
        
        Args:
            item_ids: List of item IDs
            save_history: Whether to save snapshots
            
        Returns:
            Dict mapping item_id to CompetitionScore
        """
        tasks = [self.analyze_item(item_id, save_history) for item_id in item_ids]
        results = await asyncio.gather(*tasks)
        
        return {
            result.item_id: result
            for result in results
            if result is not None
        }


async def cmd_competition(args):
    """Command: Analyze competition for items."""
    analyzer = MarketAnalyzer(region=args.region)
    
    if args.items:
        item_ids = [int(x.strip()) for x in args.items.split(',')]
    else:
        # Default popular items
        item_ids = [
            16001,  # Black Stone (Weapon)
            16002,  # Black Stone (Armor)
            16004,  # Cron Stone
            44195,  # Memory Fragment
        ]
    
    console.print(f"[cyan]Analyzing competition for {len(item_ids)} items...[/cyan]\n")
    
    results = await analyzer.analyze_batch(item_ids, save_history=args.save)
    
    # Display table
    table = Table(title="Competition Analysis")
    table.add_column("Item", style="bold")
    table.add_column("Score", style="cyan", justify="right")
    table.add_column("Buyers", style="yellow", justify="right")
    table.add_column("Sellers", style="green", justify="right")
    table.add_column("Walls", style="magenta", justify="center")
    table.add_column("Recommendation")
    
    for item_id, comp in sorted(results.items(), key=lambda x: x[1].score):
        score_color = "green" if comp.score < 0.3 else "yellow" if comp.score < 0.6 else "red"
        table.add_row(
            comp.item_name,
            f"[{score_color}]{comp.score:.2f}[/{score_color}]",
            f"{comp.buyer_count:,}",
            f"{comp.seller_count:,}",
            "⚠" if comp.has_walls else "-",
            comp.recommendation
        )
    
    console.print(table)


def cmd_timing(args):
    """Command: Show market cycle timing."""
    analyzer = MarketAnalyzer()
    cycle = analyzer.get_market_cycle()
    
    console.print("[bold cyan]Market Timing Analysis[/bold cyan]\n")
    
    console.print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    console.print(f"Hour: {cycle.current_hour}:00")
    console.print(f"Peak Time (18-22 UTC): {'YES ✓' if cycle.is_peak_time else 'NO'}")
    console.print(f"Weekend: {'YES ✓' if cycle.is_weekend else 'NO'}")
    console.print(f"\n{cycle.recommendation}")
    
    console.print("\n[dim]Heuristics:[/dim]")
    console.print("  • Best time to SELL: Peak hours (18-22 UTC) + Weekend")
    console.print("  • Best time to BUY: Off-peak weekdays")
    console.print("  • Weekend bonus: ~15% higher prices on average")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="BDO Market Analysis Engine")
    parser.add_argument('--region', default='eu', choices=['eu', 'na', 'kr', 'sa'])
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Competition command
    comp_parser = subparsers.add_parser('competition', help='Analyze competition')
    comp_parser.add_argument('--items', help='Comma-separated item IDs (default: popular items)')
    comp_parser.add_argument('--save', action='store_true', help='Save snapshots to history')
    
    # Timing command
    subparsers.add_parser('timing', help='Show market cycle timing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'competition':
        await cmd_competition(args)
    elif args.command == 'timing':
        cmd_timing(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise

