#!/usr/bin/env python3
"""Quick test of sniper with 1 check cycle."""
import asyncio
from sniper import ItemSniper

async def test_sniper():
    """Test sniper for one cycle."""
    sniper = ItemSniper()
    
    if not sniper.load_config():
        print("Failed to load config")
        return
    
    print(f"Loaded {len(sniper.watchlist)} items")
    
    # Do ONE check cycle
    from utils.market_client import MarketClient
    async with MarketClient(region=sniper.region) as client:
        sniper.client = client
        
        for watch_item in sniper.watchlist:
            print(f"\nChecking: {watch_item.item_name} (ID: {watch_item.item_id})")
            result = await sniper.check_item(watch_item)
            
            if result:
                print(f"  ALERT would be triggered!")
                sniper.print_alert(result)
            else:
                print(f"  No alert (name: {watch_item.item_name})")

if __name__ == "__main__":
    asyncio.run(test_sniper())

