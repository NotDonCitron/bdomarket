#!/usr/bin/env python3
"""
Test Market Trader - Test trading functionality with mock credentials.

⚠️  This is a DRY RUN test - no actual trades will be executed.
    The API will reject requests with invalid credentials.
"""
import asyncio
from utils.market_trader import MarketTrader, TradeCredentials


async def test_trader():
    """Test trader with mock credentials (will fail auth, but tests structure)."""
    print("Testing Market Trader functionality...\n")
    
    # Mock credentials (won't work for actual trading)
    creds = TradeCredentials(
        session_id="test_session_id",
        user_no="test_user_no",
        region='eu'
    )
    
    async with MarketTrader(creds) as trader:
        print("✅ Trader initialized")
        print(f"   Region: {trader.credentials.region}")
        print(f"   Base URL: {trader.base_url}\n")
        
        # Test buy (will fail auth)
        print("Testing buy_item()...")
        result = await trader.buy_item(
            item_id=16001,
            price=180000,
            quantity=100
        )
        print(f"   Result: {'✅ Success' if result.success else '❌ Failed (expected)'}")
        print(f"   Message: {result.message}\n")
        
        # Test sell
        print("Testing sell_item()...")
        result = await trader.sell_item(
            item_id=16001,
            price=250000,
            quantity=50
        )
        print(f"   Result: {'✅ Success' if result.success else '❌ Failed (expected)'}")
        print(f"   Message: {result.message}\n")
        
        # Test collect
        print("Testing collect_funds()...")
        result = await trader.collect_funds()
        print(f"   Result: {'✅ Success' if result.success else '❌ Failed (expected)'}")
        print(f"   Message: {result.message}\n")
        
        # Test inventory
        print("Testing get_inventory()...")
        inventory = await trader.get_inventory()
        print(f"   Result: {len(inventory)} items (expected 0 with mock auth)\n")
        
        # Test listings
        print("Testing get_bid_listings()...")
        listings = await trader.get_bid_listings()
        print(f"   Result: {len(listings)} listings (expected 0 with mock auth)\n")
        
        print("✅ All tests completed (authentication failures are expected)")
        print("\n💡 To test actual trading:")
        print("   1. Run: python trader.py auth")
        print("   2. Enter your real credentials from market.blackdesertonline.com")
        print("   3. Run: python trader.py inventory")


if __name__ == '__main__':
    asyncio.run(test_trader())



