#!/usr/bin/env python3
"""
BDO Multi-Item Flip Optimizer

Optimizes flip portfolio allocation with budget constraints using knapsack algorithm.
"""
import argparse
import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from flip_scanner import EnhancedFlipScanner, FlipCandidate
from utils.calculations import format_silver, format_percentage

console = Console()


@dataclass
class OptimizedPosition:
    """An optimized trading position."""
    candidate: FlipCandidate
    quantity: int
    total_cost: int
    expected_profit: int
    roi: float


class FlipOptimizer:
    """
    Optimizes flip portfolio allocation with budget constraints.
    
    Uses modified knapsack algorithm with competition-weighted scoring.
    """
    
    def __init__(self, budget: int):
        """
        Initialize optimizer.
        
        Args:
            budget: Total budget in silver
        """
        self.budget = budget
    
    def calculate_score(self, candidate: FlipCandidate) -> float:
        """
        Calculate weighted score for a flip candidate.
        
        Score formula: (ROI * speed_factor) / (competition + 1)
        
        Args:
            candidate: FlipCandidate object
            
        Returns:
            Weighted score
        """
        # Speed factor based on stock/trades (high liquidity = faster flips)
        speed_factor = 1.0
        if candidate.trades > 100000:
            speed_factor = 1.5  # Very liquid
        elif candidate.trades > 50000:
            speed_factor = 1.2  # Liquid
        elif candidate.trades < 10000:
            speed_factor = 0.7  # Illiquid
        
        # Competition penalty (higher competition = lower score)
        competition_factor = 1.0 / (candidate.competition_score + 1)
        
        # Final score
        score = (candidate.roi * speed_factor) * competition_factor
        
        return score
    
    def optimize(
        self,
        candidates: List[FlipCandidate],
        max_positions: int = 10
    ) -> List[OptimizedPosition]:
        """
        Optimize portfolio allocation.
        
        Args:
            candidates: List of FlipCandidate objects
            max_positions: Maximum number of positions to hold
            
        Returns:
            List of OptimizedPosition objects
            
        Algorithm:
            1. Sort candidates by weighted score
            2. Greedy allocation: pick best items that fit budget
            3. Consider quantity constraints (max 1000 per item for safety)
        """
        if not candidates:
            return []
        
        # Calculate scores
        scored = [(self.calculate_score(c), c) for c in candidates]
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Greedy allocation
        positions = []
        remaining_budget = self.budget
        
        for score, candidate in scored:
            if len(positions) >= max_positions:
                break
            
            # Max quantity: either budget limit or 1000 items (safety)
            max_qty = min(
                remaining_budget // candidate.buy_at,
                1000
            )
            
            if max_qty <= 0:
                continue  # Can't afford even one
            
            # Calculate optimal quantity
            # For simplicity, buy as many as possible within limits
            quantity = max_qty
            
            total_cost = quantity * candidate.buy_at
            expected_profit = quantity * candidate.profit
            
            positions.append(OptimizedPosition(
                candidate=candidate,
                quantity=quantity,
                total_cost=total_cost,
                expected_profit=expected_profit,
                roi=candidate.roi
            ))
            
            remaining_budget -= total_cost
            
            if remaining_budget < candidate.buy_at:
                break  # Not enough budget for more items
        
        return positions
    
    def display_portfolio(self, positions: List[OptimizedPosition]):
        """
        Display optimized portfolio.
        
        Args:
            positions: List of OptimizedPosition objects
        """
        if not positions:
            console.print("[yellow]No positions to display.[/yellow]")
            return
        
        console.print(f"[bold cyan]💰 Budget: {format_silver(self.budget)} | Optimized Portfolio[/bold cyan]\n")
        
        table = Table(title="Optimized Positions")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Item", style="bold")
        table.add_column("Qty", style="cyan", justify="right")
        table.add_column("Cost", style="yellow", justify="right")
        table.add_column("Exp. Profit", style="green", justify="right")
        table.add_column("ROI", style="magenta", justify="right")
        table.add_column("Risk", style="dim", justify="center")
        
        total_cost = 0
        total_profit = 0
        
        for i, pos in enumerate(positions, 1):
            total_cost += pos.total_cost
            total_profit += pos.expected_profit
            
            roi_color = "green" if pos.roi > 0.2 else "yellow"
            risk_emoji = {
                'LOW': '✓',
                'MEDIUM': '~',
                'HIGH': '⚠'
            }.get(pos.candidate.risk_level, '?')
            
            table.add_row(
                str(i),
                pos.candidate.item_name[:25],
                f"{pos.quantity:,}",
                format_silver(pos.total_cost),
                format_silver(pos.expected_profit),
                f"[{roi_color}]{format_percentage(pos.roi)}[/{roi_color}]",
                f"{risk_emoji} {pos.candidate.risk_level}"
            )
        
        console.print(table)
        
        # Summary
        avg_roi = total_profit / total_cost if total_cost > 0 else 0.0
        remaining = self.budget - total_cost
        
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total Cost: {format_silver(total_cost)} / {format_silver(self.budget)}")
        console.print(f"  Remaining: {format_silver(remaining)}")
        console.print(f"  Expected Profit: [green]{format_silver(total_profit)}[/green]")
        console.print(f"  Portfolio ROI: [bold green]{format_percentage(avg_roi)}[/bold green]")
        console.print(f"  Positions: {len(positions)}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="BDO Multi-Item Flip Optimizer")
    parser.add_argument('--budget', type=int, required=True, help='Total budget in silver (e.g. 500000000)')
    parser.add_argument('--region', default='eu', choices=['eu', 'na', 'kr', 'sa'])
    parser.add_argument('--tax', type=float, default=0.35)
    parser.add_argument('--min-roi', type=float, default=0.05)
    parser.add_argument('--max-items', type=int, default=200)
    parser.add_argument('--max-positions', type=int, default=10)
    parser.add_argument('--filter-risk', choices=['LOW', 'MEDIUM', 'HIGH'])
    
    args = parser.parse_args()
    
    # Scan for opportunities
    console.print("[cyan]Step 1: Scanning market for flip opportunities...[/cyan]\n")
    scanner = EnhancedFlipScanner(
        region=args.region,
        tax_rate=args.tax,
        min_roi=args.min_roi,
        max_items=args.max_items
    )
    
    candidates = await scanner.scan(show_competition=True, show_timing=True)
    
    if not candidates:
        console.print("[yellow]No flip candidates found. Market may be efficient right now.[/yellow]")
        return
    
    # Filter by risk if requested
    if args.filter_risk:
        candidates = [c for c in candidates if c.risk_level == args.filter_risk.upper()]
        console.print(f"\n[dim]Filtered to {len(candidates)} {args.filter_risk} risk candidates[/dim]\n")
    
    # Optimize portfolio
    console.print("\n[cyan]Step 2: Optimizing portfolio allocation...[/cyan]\n")
    optimizer = FlipOptimizer(budget=args.budget)
    positions = optimizer.optimize(candidates, max_positions=args.max_positions)
    
    # Display results
    optimizer.display_portfolio(positions)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise

