"""
Test Pearl Sniper with mock data.

This script tests the pearl sniper system with predefined mock items
to verify calculations, alerts, and system behavior without hitting
the live API.

Usage:
    python tests/test_pearl_mock.py
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.pearl_calculator import PearlValueCalculator, OutfitExtractionData
from utils.smart_poller import SmartPoller
from utils.pearl_alerts import PearlAlerter


# ========== MOCK DATA ==========

MOCK_PRICES = {
    'cron_stone': 2_500_000,   # 2.5M per Cron (marketplace price, NPC = 3M)
    'valks_cry': 20_000_000    # 20M per Valks (marketplace price)
}

MOCK_PEARL_ITEMS = [
    {
        'id': 40001,
        'name': '[Kibelius] Outfit Set (Premium)',
        'price': 1_350_000_000,  # 1.35B
        'outfit_type': 'premium',
        'expected_crons': 993,
        'expected_valks': 331
    },
    {
        'id': 40002,
        'name': '[Karlstein] Classic Outfit',
        'price': 1_800_000_000,  # 1.8B
        'outfit_type': 'classic',
        'expected_crons': 801,
        'expected_valks': 267
    },
    {
        'id': 40003,
        'name': 'Simple Desert Outfit',
        'price': 900_000_000,    # 900M
        'outfit_type': 'simple',
        'expected_crons': 543,
        'expected_valks': 181
    },
    {
        'id': 40004,
        'name': 'Dream Horse Gear Set',
        'price': 2_000_000_000,  # 2B
        'outfit_type': 'mount',
        'expected_crons': 900,
        'expected_valks': 300
    },
    {
        'id': 40005,
        'name': '[Test] Unprofitable Outfit',
        'price': 10_000_000_000,  # 10B (too expensive)
        'outfit_type': 'premium',
        'expected_crons': 993,
        'expected_valks': 331
    }
]


# ========== MOCK MARKET CLIENT ==========

class MockMarketClient:
    """Mock market client for testing."""
    
    def __init__(self, region='eu'):
        self.region = region
    
    async def get_orderbook_batch(self, item_ids):
        """Return mock orderbook data."""
        from utils.market_client import OrderbookData, ItemInfo, OrderLevel
        
        result = {}
        
        # Cron Stone (16004)
        if 16004 in item_ids:
            result[16004] = OrderbookData(
                item=ItemInfo(id=16004, name='Cron Stone'),
                orders=[
                    OrderLevel(
                        price=MOCK_PRICES['cron_stone'],
                        buyers=100,
                        sellers=50
                    )
                ]
            )
        
        # Valks' Cry (16003)
        if 16003 in item_ids:
            result[16003] = OrderbookData(
                item=ItemInfo(id=16003, name="Valks' Cry"),
                orders=[
                    OrderLevel(
                        price=MOCK_PRICES['valks_cry'],
                        buyers=50,
                        sellers=25
                    )
                ]
            )
        
        return result
    
    def close(self):
        """Mock close."""
        pass


# ========== TEST FUNCTIONS ==========

def test_calculator():
    """Test pearl value calculator."""
    print("\n" + "=" * 60)
    print("TEST: Pearl Value Calculator")
    print("=" * 60)
    
    client = MockMarketClient()
    calculator = PearlValueCalculator(client)
    
    # Manually set mock prices
    calculator.cron_price = MOCK_PRICES['cron_stone']
    calculator.valks_price = MOCK_PRICES['valks_cry']
    calculator.last_price_update = datetime.now()
    
    print(f"\nMock Prices:")
    print(f"  Cron Stone: {calculator.cron_price:,}")
    print(f"  Valks' Cry: {calculator.valks_price:,}")
    
    # Test each mock item
    print(f"\nTesting {len(MOCK_PEARL_ITEMS)} mock items:\n")
    
    passed = 0
    failed = 0
    
    for item in MOCK_PEARL_ITEMS:
        result = calculator.calculate_value(item['outfit_type'], item['price'])
        
        if not result:
            print(f"❌ {item['name']}: Calculation failed!")
            failed += 1
            continue
        
        # Verify extraction amounts
        crons_match = result.cron_stones == item['expected_crons']
        valks_match = result.valks_cry == item['expected_valks']
        
        if crons_match and valks_match:
            print(f"✅ {item['name']}")
            print(f"   Price: {item['price']:,}")
            print(f"   Extraction: {result.extraction_value:,}")
            print(f"   Profit: {result.profit:,} ({result.roi * 100:.1f}%)")
            print(f"   Profitable: {result.is_profitable}")
            passed += 1
        else:
            print(f"❌ {item['name']}: Extraction mismatch!")
            print(f"   Expected: {item['expected_crons']} Crons, {item['expected_valks']} Valks")
            print(f"   Got: {result.cron_stones} Crons, {result.valks_cry} Valks")
            failed += 1
        
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_poller():
    """Test smart poller."""
    print("\n" + "=" * 60)
    print("TEST: Smart Poller")
    print("=" * 60)
    
    poller = SmartPoller(
        base_interval=2.0,
        peak_interval=1.0,
        activity_interval=1.5
    )
    
    # Test base interval
    interval = poller.get_interval()
    print(f"\nBase interval: {interval}s")
    assert interval == 2.0 or interval == 1.0, "Base interval incorrect"
    
    # Test activity boost
    poller.record_activity()
    interval = poller.get_interval()
    print(f"After activity: {interval}s")
    assert interval == 1.5, "Activity interval incorrect"
    
    # Test stats
    stats = poller.get_stats()
    print(f"\nStats:")
    print(f"  Total polls: {stats['total_polls']}")
    print(f"  Activity count: {stats['activity_count']}")
    print(f"  Peak hours: {stats['is_peak_hours']}")
    print(f"  Recent activity: {stats['has_recent_activity']}")
    
    print("\n✅ Smart Poller: All tests passed")
    return True


async def test_alerter():
    """Test alert system."""
    print("\n" + "=" * 60)
    print("TEST: Alert System")
    print("=" * 60)
    
    # Create alerter (no webhook for testing)
    alerter = PearlAlerter(
        terminal_enabled=True,
        terminal_beep=False,  # Don't beep during tests
        toast_enabled=False,  # Don't show toasts during tests
        webhook_url=None
    )
    
    # Create mock calculator
    client = MockMarketClient()
    calculator = PearlValueCalculator(client)
    calculator.cron_price = MOCK_PRICES['cron_stone']
    calculator.valks_price = MOCK_PRICES['valks_cry']
    
    print("\nTesting alerts for profitable items:\n")
    
    for item in MOCK_PEARL_ITEMS[:3]:  # Test first 3 profitable items
        result = calculator.calculate_value(item['outfit_type'], item['price'])
        
        if result and result.is_profitable:
            await alerter.send_alert(item, result)
    
    # Get stats
    stats = alerter.get_stats()
    print(f"\nAlert Stats:")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Critical: {stats['critical']}")
    print(f"  High: {stats['high']}")
    print(f"  Normal: {stats['normal']}")
    
    print("\n✅ Alert System: Test completed")
    return True


async def test_full_integration():
    """Test full integration of all components."""
    print("\n" + "=" * 60)
    print("TEST: Full Integration")
    print("=" * 60)
    
    # Initialize components
    client = MockMarketClient()
    calculator = PearlValueCalculator(client)
    poller = SmartPoller()
    alerter = PearlAlerter(
        terminal_enabled=True,
        terminal_beep=False,
        toast_enabled=False
    )
    
    # Update prices
    await calculator.update_prices()
    
    print("\nProcessing mock items...\n")
    
    items_checked = 0
    alerts_sent = 0
    
    for item in MOCK_PEARL_ITEMS:
        items_checked += 1
        
        result = calculator.calculate_value(item['outfit_type'], item['price'])
        
        if result and result.is_profitable:
            await alerter.send_alert(item, result)
            alerts_sent += 1
            poller.record_activity()
    
    # Get final stats
    poller_stats = poller.get_stats()
    alerter_stats = alerter.get_stats()
    
    print(f"\nIntegration Test Results:")
    print(f"  Items checked: {items_checked}")
    print(f"  Alerts sent: {alerts_sent}")
    print(f"  Poller activity count: {poller_stats['activity_count']}")
    print(f"  Current interval: {poller_stats['current_interval']}s")
    
    print("\n✅ Full Integration: Test completed")
    return True


# ========== MAIN ==========

async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PEARL SNIPER - MOCK DATA TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    try:
        results.append(("Calculator", test_calculator()))
        results.append(("Poller", test_poller()))
        results.append(("Alerter", await test_alerter()))
        results.append(("Integration", await test_full_integration()))
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:15} {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

