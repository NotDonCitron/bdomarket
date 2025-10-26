#!/usr/bin/env python3
"""Test optimizer with mock data (since market has no opportunities)."""
from optimizer import FlipOptimizer, FlipCandidate, OptimizedPosition

# Create mock candidates
candidates = [
    FlipCandidate(
        item_id=16001,
        item_name="Black Stone (Weapon)",
        buy_at=175000,
        sell_at=230000,
        profit=47500,  # Assuming 35% tax
        roi=0.27,
        stock=1000,
        trades=500000,
        competition_score=0.4,
        risk_level="MEDIUM"
    ),
    FlipCandidate(
        item_id=16002,
        item_name="Black Stone (Armor)",
        buy_at=180000,
        sell_at=250000,
        profit=62500,
        roi=0.35,
        stock=800,
        trades=400000,
        competition_score=0.3,
        risk_level="LOW"
    ),
    FlipCandidate(
        item_id=16004,
        item_name="Cron Stone",
        buy_at=6900000,
        sell_at=8500000,
        profit=625000,
        roi=0.09,
        stock=50,
        trades=50000,
        competition_score=0.7,
        risk_level="HIGH"
    ),
]

# Test optimizer
budget = 500_000_000  # 500M
optimizer = FlipOptimizer(budget=budget)

print("Testing optimizer with mock data...")
positions = optimizer.optimize(candidates, max_positions=10)

optimizer.display_portfolio(positions)

