#!/usr/bin/env python3
"""Test the new MarketClient wrapper."""
import asyncio
from utils.market_client import MarketClient

async def test_client():
    """Test MarketClient functionality."""
    print("Testing MarketClient wrapper...")
    
    async with MarketClient(region='eu') as client:
        # Test single orderbook
        print("\n1. Get orderbook for Black Stone (Weapon) - ID: 16001")
        orderbook = await client.get_orderbook(16001)
        
        if orderbook:
            print(f"  Item: {orderbook.item.name} (ID: {orderbook.item.id})")
            print(f"  Price levels: {len(orderbook.orders)}")
            
            # Find lowest sell and highest buy
            lowest_sell = None
            highest_buy = None
            
            for order in orderbook.orders:
                if order.sellers > 0:
                    if lowest_sell is None or order.price < lowest_sell:
                        lowest_sell = order.price
                if order.buyers > 0:
                    if highest_buy is None or order.price > highest_buy:
                        highest_buy = order.price
            
            print(f"  Lowest Sell: {lowest_sell:,}" if lowest_sell else "  No sellers")
            print(f"  Highest Buy: {highest_buy:,}" if highest_buy else "  No buyers")
        else:
            print("  Failed to fetch orderbook")
        
        # Test batch
        print("\n2. Get batch orderbooks for items 16001, 16002")
        orderbooks = await client.get_orderbook_batch([16001, 16002])
        
        for item_id, ob in orderbooks.items():
            print(f"  {ob.item.name} (ID: {item_id}): {len(ob.orders)} levels")
    
    print("\n✓ MarketClient test complete!")

if __name__ == "__main__":
    asyncio.run(test_client())

