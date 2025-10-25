#!/usr/bin/env python3
"""
Test script for Pearl Shop Monitor functionality
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.pearl_calculator import PearlItem, PearlCalculator

async def test_pearl_calculations():
    """Test Pearl extraction value calculations"""
    print("🧪 Testing Pearl Extraction Calculations")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Kibelius Outfit Set (PREMIUM)",
            "category": "outfit", 
            "price": 1_350_000_000,
            "expected_type": "premium_outfit"
        },
        {
            "name": "Classic Outfit Set",
            "category": "outfit",
            "price": 980_000_000,
            "expected_type": "classic_outfit"
        },
        {
            "name": "Simple Outfit",
            "category": "outfit",
            "price": 650_000_000,
            "expected_type": "simple_outfit"
        },
        {
            "name": "Mount Gear Package",
            "category": "mount",
            "price": 1_200_000_000,
            "expected_type": "mount_gear"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        
        # Create Pearl item
        item = PearlItem(
            item_id=str(i),
            name=test_case['name'],
            category=test_case['category'],
            price=test_case['price'],
            listed_time=datetime.now()
        )
        
        # Calculate metrics
        calculated_item = PearlCalculator.calculate_profit_metrics(item)
        
        # Check categorization
        item_type = PearlCalculator.categorize_item(item.name, item.category)
        
        print(f"   🏷️  Category: {item_type}")
        print(f"   💰 Listed Price: {calculated_item.price:,} Pearl")
        print(f"   ⚡ Extraction Value: {calculated_item.extraction_value:,} Pearl")
        print(f"   📈 Profit: {calculated_item.profit_margin:+,.0f} Pearl")
        print(f"   📊 ROI: {calculated_item.roi:+.1%}")
        
        # Check if profitable
        min_profit = 100_000_000
        min_roi = 0.05
        
        if calculated_item.profit_margin >= min_profit and calculated_item.roi >= min_roi:
            print("   ✅ PROFITABLE OPPORTUNITY!")
        else:
            print("   ❌ Not profitable enough")
        
        # Verify expected type
        if item_type == test_case['expected_type']:
            print("   ✅ Correct categorization")
        else:
            print(f"   ❌ Wrong categorization (expected {test_case['expected_type']})")

async def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🔧 Testing Edge Cases")
    print("=" * 50)
    
    edge_cases = [
        {
            "name": "",  # Empty name
            "category": "outfit",
            "price": 0
        },
        {
            "name": "Unknown Item",
            "category": "unknown",
            "price": 1_000_000_000
        },
        {
            "name": "FREE ITEM",
            "category": "outfit", 
            "price": 0  # Free item
        }
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"\n🔍 Edge Case {i}: '{test_case['name']}'")
        
        try:
            item = PearlItem(
                item_id=f"edge_{i}",
                name=test_case['name'],
                category=test_case['category'],
                price=test_case['price'],
                listed_time=datetime.now()
            )
            
            calculated_item = PearlCalculator.calculate_profit_metrics(item)
            
            print(f"   🏷️  Category: {PearlCalculator.categorize_item(item.name, item.category)}")
            print(f"   💰 Price: {calculated_item.price:,}")
            print(f"   ⚡ Extraction: {calculated_item.extraction_value:,}")
            print(f"   📈 Profit: {calculated_item.profit_margin:+,.0f}")
            print(f"   📊 ROI: {calculated_item.roi:+.1%}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Run all tests"""
    print("🚀 Pearl Shop Monitor - Test Suite")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await test_pearl_calculations()
    await test_edge_cases()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())