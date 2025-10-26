#!/usr/bin/env python3
"""Test portfolio tracker with sample data."""
import asyncio
from datetime import datetime
from portfolio import PortfolioTracker, Trade

async def test_portfolio():
    """Test portfolio with sample trades."""
    print("Testing Portfolio Tracker...\n")
    
    tracker = PortfolioTracker()
    
    # Log some sample trades
    print("1. Logging sample trades...")
    
    # Buy Black Stone
    tracker.log_trade(Trade(
        timestamp=datetime.now().isoformat(),
        item_id=16001,
        item_name="Black Stone (Weapon)",
        qty=100,
        price=175000,
        trade_type='buy',
        notes="Good price!"
    ))
    
    # Sell some Black Stone
    tracker.log_trade(Trade(
        timestamp=datetime.now().isoformat(),
        item_id=16001,
        item_name="Black Stone (Weapon)",
        qty=50,
        price=185000,
        trade_type='sell',
        notes="Quick flip"
    ))
    
    # Buy Cron Stone
    tracker.log_trade(Trade(
        timestamp=datetime.now().isoformat(),
        item_id=16004,
        item_name="Concentrated Magical Black Stone",
        qty=10,
        price=6900000,
        trade_type='buy',
        notes="Investment"
    ))
    
    print("\n2. Generating P&L Report...")
    tracker.generate_report()
    
    print("\n3. Checking Live Status...")
    await tracker.live_status()

if __name__ == "__main__":
    asyncio.run(test_portfolio())

