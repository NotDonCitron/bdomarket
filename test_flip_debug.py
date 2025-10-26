#!/usr/bin/env python3
"""Debug flip scanner to see what's happening."""
import asyncio
from utils.market_client import MarketClient
from utils.calculations import calculate_profit, calculate_roi, format_silver

async def test():
    async with MarketClient(region='eu') as client:
        # Test some known items
        test_items = [16001, 16002, 16004, 44195]
        
        for item_id in test_items:
            print(f"\n=== Testing item {item_id} ===")
            orderbook = await client.get_orderbook(item_id)
            
            if not orderbook:
                print("  No orderbook!")
                continue
            
            print(f"  Name: {orderbook.item.name}")
            print(f"  Orders: {len(orderbook.orders)}")
            
            # Find prices
            lowest_sell = None
            highest_buy = None
            
            for order in orderbook.orders:
                if order.sellers > 0:
                    if lowest_sell is None or order.price < lowest_sell:
                        lowest_sell = order.price
                if order.buyers > 0:
                    if highest_buy is None or order.price > highest_buy:
                        highest_buy = order.price
            
            print(f"  Lowest Sell: {format_silver(lowest_sell) if lowest_sell else 'N/A'}")
            print(f"  Highest Buy: {format_silver(highest_buy) if highest_buy else 'N/A'}")
            
            if lowest_sell and highest_buy:
                profit = calculate_profit(lowest_sell, highest_buy, 1, 0.35)
                roi = calculate_roi(lowest_sell, highest_buy, 0.35)
                print(f"  Profit: {format_silver(profit)} ({roi*100:+.1f}%)")
                print(f"  Profitable: {'YES' if profit > 0 and roi >= 0.01 else 'NO'}")

asyncio.run(test())

