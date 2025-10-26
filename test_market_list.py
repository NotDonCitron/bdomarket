#!/usr/bin/env python3
"""Test get_market_list to see what it returns."""
import asyncio
from utils.market_client import MarketClient

async def test():
    async with MarketClient(region='eu') as client:
        market_list = await client.get_market_list()
        print(f"Market list length: {len(market_list) if market_list else 0}")
        
        if market_list:
            print(f"\nFirst 5 items:")
            for item in market_list[:5]:
                print(f"  {item}")
        else:
            print("Market list is empty or None!")

asyncio.run(test())

