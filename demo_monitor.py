#!/usr/bin/env python3
"""
Simple demo script to show Chrome-based Pearl shop monitoring capabilities
without requiring actual BDO login.
"""

import asyncio
import json
from datetime import datetime
from utils.pearl_calculator import PearlItem, PearlCalculator

async def demo_monitoring():
    """Demo the monitoring logic with simulated data"""
    print("🚀 BDO Pearl Shop Monitor - Demo Mode")
    print("=" * 60)
    
    # Simulate newly detected Pearl items
    simulated_items = [
        {
            "id": "demo_001",
            "name": "Kibelius Outfit Set (PREMIUM)",
            "category": "outfit",
            "price": 1_350_000_000,
            "detected_time": datetime.now()
        },
        {
            "id": "demo_002", 
            "name": "Classic Outfit Set",
            "category": "outfit",
            "price": 980_000_000,
            "detected_time": datetime.now()
        },
        {
            "id": "demo_003",
            "name": "Mount Gear Package",
            "category": "mount",
            "price": 1_200_000_000,
            "detected_time": datetime.now()
        }
    ]
    
    print("🔍 Simulating new Pearl shop listings detection...")
    print()
    
    for item_data in simulated_items:
        # Create Pearl item
        pearl_item = PearlItem(
            item_id=item_data["id"],
            name=item_data["name"],
            category=item_data["category"],
            price=item_data["price"],
            listed_time=item_data["detected_time"]
        )
        
        # Calculate profit metrics
        calculated_item = PearlCalculator.calculate_profit_metrics(pearl_item)
        
        # Check if it meets alert criteria (100M profit, 5% ROI)
        min_profit = 100_000_000
        min_roi = 0.05
        
        if calculated_item.profit_margin >= min_profit and calculated_item.roi >= min_roi:
            # Trigger alert
            alert_msg = (
                f"💎 PEARL ALERT! {calculated_item.name}\n"
                f"   Listed: {calculated_item.price:,} Pearl\n"
                f"   Extraction: {calculated_item.extraction_value:,} ({calculated_item.extraction_value//3_000_000:,} Crons)\n"
                f"   Profit: {calculated_item.profit_margin:+,.0f} ({calculated_item.roi:+.1%} ROI) ✓✓✓\n"
                f"   Time: {calculated_item.listed_time.strftime('%H:%M:%S')} (ACT NOW!)"
            )
            
            print("\n" + "="*60)
            print(alert_msg)
            print("="*60 + "\n")
            
            # Sound alert simulation
            print("🔔 Alert sound: BEEP!")
        else:
            print(f"📋 Item detected: {calculated_item.name} - Not profitable enough")
    
    print("\n✅ Demo completed!")
    print("\n📝 How it works in production:")
    print("1. Chrome browser navigates to BDO Pearl shop")
    print("2. Monitors network traffic for API calls")
    print("3. Scans page content for new item listings")
    print("4. Calculates extraction values and profit margins")
    print("5. Triggers alerts for profitable opportunities")
    print("6. Saves authentication sessions for automatic reconnection")

if __name__ == "__main__":
    asyncio.run(demo_monitoring())