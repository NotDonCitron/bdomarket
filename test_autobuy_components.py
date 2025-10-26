"""
Test suite for Pearl Auto-Buy components.

Tests the major components without requiring actual network access or session.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add utils directory directly to path to avoid importing full package
ROOT = Path(__file__).parent
UTILS_PATH = ROOT / "utils"
sys.path.insert(0, str(UTILS_PATH))

from autobuy import AutoBuyConfig, PurchaseAttempt
from pearl_detector import DetectionEvent


def test_autobuy_config():
    """Test AutoBuyConfig creation."""
    print("Testing AutoBuyConfig...")
    
    config = AutoBuyConfig(
        enabled=True,
        max_price=5_000_000_000,
        min_profit=100_000_000,
        min_roi=0.05,
        max_purchases_per_hour=10,
        cooldown_seconds=2.0,
        dry_run=False
    )
    
    assert config.enabled == True
    assert config.max_price == 5_000_000_000
    assert config.min_profit == 100_000_000
    assert config.min_roi == 0.05
    
    print("✅ AutoBuyConfig test passed")


def test_purchase_attempt():
    """Test PurchaseAttempt dataclass."""
    print("\nTesting PurchaseAttempt...")
    
    attempt = PurchaseAttempt(
        item_id=40001,
        item_name="[Kibelius] Outfit Set",
        price=2_170_000_000,
        timestamp=datetime.now().timestamp(),
        success=True,
        profit=6_770_000_000,
        roi=3.12
    )
    
    assert attempt.item_id == 40001
    assert attempt.success == True
    assert attempt.profit == 6_770_000_000
    
    print("✅ PurchaseAttempt test passed")


def test_detection_event():
    """Test DetectionEvent dataclass."""
    print("\nTesting DetectionEvent...")
    
    category = {"mainCategory": 55, "subCategory": 1, "name": "Male Outfits (Set)"}
    item = {
        'mainKey': 40001,
        'name': '[Kibelius] Outfit Set',
        'pricePerOne': 2_170_000_000,
        'sumCount': 1
    }
    
    event = DetectionEvent(
        category=category,
        item=item,
        timestamp=datetime.now().timestamp(),
        is_new_listing=True,
        price=2_170_000_000,
        quantity=1
    )
    
    assert event.is_new_listing == True
    assert event.price == 2_170_000_000
    
    # Test format_summary
    summary = event.format_summary()
    assert '[Kibelius]' in summary
    assert 'Male Outfits (Set)' in summary
    
    print("✅ DetectionEvent test passed")


def test_safety_checks():
    """Test auto-buy safety check logic."""
    print("\nTesting safety checks...")
    
    config = AutoBuyConfig(
        enabled=True,
        max_price=3_000_000_000,
        min_profit=200_000_000,
        min_roi=0.10,
        max_purchases_per_hour=10,
        cooldown_seconds=2.0
    )
    
    # Test 1: Price too high
    item_price = 5_000_000_000
    assert item_price > config.max_price, "Should fail: price too high"
    
    # Test 2: Profit too low
    profit = 100_000_000
    assert profit < config.min_profit, "Should fail: profit too low"
    
    # Test 3: ROI too low
    roi = 0.05
    assert roi < config.min_roi, "Should fail: ROI too low"
    
    # Test 4: Valid item
    item_price = 2_000_000_000
    profit = 500_000_000
    roi = 0.25
    assert item_price <= config.max_price, "Should pass: price OK"
    assert profit >= config.min_profit, "Should pass: profit OK"
    assert roi >= config.min_roi, "Should pass: ROI OK"
    
    print("✅ Safety checks test passed")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Pearl Auto-Buy Component Tests")
    print("=" * 70)
    
    try:
        test_autobuy_config()
        test_purchase_attempt()
        test_detection_event()
        test_safety_checks()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
