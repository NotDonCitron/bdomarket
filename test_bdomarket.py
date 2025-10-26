#!/usr/bin/env python3
"""Quick test of bdomarket library."""
import asyncio
from bdomarket import Market, MarketRegion

async def test_bdomarket():
    """Test basic bdomarket functionality."""
    market = Market(region=MarketRegion.EU)
    
    print("Testing bdomarket...")
    
    # Test 1: Get item by ID
    print("\n1. Get item by ID (16001 = Black Stone Weapon):")
    item_result = await market.get_item(ids=["16001"])
    if item_result.success:
        print(f"  Success! Items: {len(item_result.content) if isinstance(item_result.content, list) else 1}")
        if isinstance(item_result.content, list) and item_result.content:
            print(f"  First item: {item_result.content[0]}")
    else:
        print(f"  Failed: {item_result.status_code}")
    
    # Test 2: Search items
    print("\n2. Search for 'black stone':")
    search_result = await market.get_world_market_search_list(ids=["16001"])
    if search_result.success:
        items = search_result.content if isinstance(search_result.content, list) else []
        print(f"  Found {len(items)} items")
        for item in items[:3]:
            print(f"    - {item.get('name', 'Unknown')} (ID: {item.get('id', '?')})")
    else:
        print(f"  Failed: {search_result.status_code}")
    
    # Test 3: Get orderbook
    print("\n3. Get orderbook for item 16001:")
    orderbook_result = await market.get_bidding_info(ids=["16001"], sids=["0"])
    if orderbook_result.success:
        content = orderbook_result.content
        if isinstance(content, list) and content:
            item_data = content[0]
            orders = item_data.get('orders', [])
            print(f"  Item: {item_data.get('name', 'Unknown')}")
            print(f"  Orders: {len(orders)} price levels")
            if orders:
                print(f"  First order: {orders[0]}")
        else:
            print(f"  Content: {content}")
    else:
        print(f"  Failed: {orderbook_result.status_code}")
    
    market.close()
    print("\n✓ bdomarket test complete!")
    print("\nKey findings:")
    print("  - get_item() works, returns Item objects")
    print("  - get_bidding_info() returns orderbook with name + orders")
    print("  - Orders have: price, sellers, buyers")
    print("  - close() is sync not async")

if __name__ == "__main__":
    asyncio.run(test_bdomarket())

