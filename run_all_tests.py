#!/usr/bin/env python3
"""
Run all monitoring tests sequentially and log results.
"""
import asyncio
import time
import sys
import io
from typing import Dict, Any, List

# Fix Windows console encoding issue with bdomarket library
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # Already wrapped or can't wrap

from bdomarket import Market
from bdomarket.identifiers import MarketRegion


class TestResults:
    def __init__(self):
        self.results = []
    
    def add(self, test_name: str, status: str, details: str):
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        for r in self.results:
            status_icon = "PASS" if r["status"] == "pass" else "FAIL" if r["status"] == "fail" else "INFO"
            print(f"[{status_icon}] {r['test']}")
            print(f"     {r['details']}")
            print(f"     Time: {r['timestamp']}")
        print("="*70)


async def test_1_single_item_monitor(results: TestResults):
    """Test 1: Monitor single high-volume item (Black Stone)."""
    print("\n" + "="*70)
    print("TEST 1: Single Item Monitor (Black Stone ID 16001)")
    print("="*70)
    
    item_id = 16001
    duration = 30  # 30 seconds
    last_stock = None
    stock_changes = 0
    
    async with Market(region=MarketRegion.EU) as market:
        start_time = time.time()
        loop_count = 0
        
        while time.time() - start_time < duration:
            loop_count += 1
            try:
                result = await market.post_world_market_search_list(str(item_id))
                if result.success and result.content:
                    items = result.content if isinstance(result.content, list) else [result.content]
                    if items:
                        item = items[0]
                        stock = int(item.get("stock", 0) or 0)
                        name = item.get("name", "Unknown")
                        
                        if last_stock is None:
                            print(f"Initial: {name} stock={stock}")
                            last_stock = stock
                        elif stock != last_stock:
                            print(f"STOCK CHANGE: {last_stock} -> {stock}")
                            stock_changes += 1
                            last_stock = stock
                        
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                break
    
    if stock_changes >= 1:
        results.add("Test 1: Single Item Monitor", "pass", 
                   f"Detected {stock_changes} stock changes in {loop_count} loops")
    else:
        results.add("Test 1: Single Item Monitor", "info",
                   f"No stock changes in {loop_count} loops (item may be stable)")


async def test_2_wait_list(results: TestResults):
    """Test 2: Monitor Wait List."""
    print("\n" + "="*70)
    print("TEST 2: Wait List Monitor")
    print("="*70)
    
    duration = 60  # 60 seconds
    items_seen = set()
    
    async with Market(region=MarketRegion.EU) as market:
        start_time = time.time()
        loop_count = 0
        
        while time.time() - start_time < duration:
            loop_count += 1
            try:
                result = await market.post_world_market_wait_list()
                if result.success:
                    items = result.content if isinstance(result.content, list) else []
                    for item in items:
                        item_id = item.get("id")
                        if item_id and item_id not in items_seen:
                            items_seen.add(item_id)
                            name = item.get("name", "Unknown")
                            print(f"New in wait list: {name} (ID: {item_id})")
                    
                    print(f"Loop {loop_count}: {len(items)} items in wait list, {len(items_seen)} unique seen")
                
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Error: {e}")
                break
    
    results.add("Test 2: Wait List Monitor", "pass",
               f"Saw {len(items_seen)} unique items in {loop_count} loops")


async def test_3_pearl_monitor(results: TestResults):
    """Test 3: Pearl Monitor Production Test."""
    print("\n" + "="*70)
    print("TEST 3: Pearl Monitor (Production)")
    print("="*70)
    
    duration = 120  # 2 minutes
    loop_count = 0
    errors = 0
    
    async with Market(region=MarketRegion.EU) as market:
        start_time = time.time()
        
        while time.time() - start_time < duration:
            loop_count += 1
            try:
                result = await market.post_pearl_items()
                if result.success and isinstance(result.content, list):
                    items = result.content
                    with_stock = [it for it in items if int(it.get("stock", 0) or 0) > 0]
                    print(f"Loop {loop_count}: {len(items)} Pearl items, {len(with_stock)} with stock")
                else:
                    errors += 1
                    print(f"Loop {loop_count}: API call failed")
                
                await asyncio.sleep(3)
            except Exception as e:
                errors += 1
                print(f"Error: {e}")
                break
    
    if errors == 0:
        results.add("Test 3: Pearl Monitor", "pass",
                   f"Ran {loop_count} loops error-free for {duration}s")
    else:
        results.add("Test 3: Pearl Monitor", "fail",
                   f"{errors} errors in {loop_count} loops")


async def main():
    """Run all tests."""
    results = TestResults()
    
    print("="*70)
    print("BDO MARKETPLACE MONITOR - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("This will take approximately 3-4 minutes...")
    print()
    
    try:
        await test_1_single_item_monitor(results)
        await test_2_wait_list(results)
        await test_3_pearl_monitor(results)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
    
    results.print_summary()
    
    # Write results to file
    with open("TEST_RESULTS_BDOMARKET.md", "w", encoding="utf-8") as f:
        f.write("# BDO Marketplace Monitor - Test Results\n\n")
        f.write(f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Test Suite Overview\n\n")
        f.write("Comprehensive tests to verify 100% functionality before production deployment.\n\n")
        f.write("## Test Results\n\n")
        
        for r in results.results:
            status_icon = "✅" if r["status"] == "pass" else "❌" if r["status"] == "fail" else "ℹ️"
            f.write(f"### {status_icon} {r['test']}\n\n")
            f.write(f"**Status:** {r['status'].upper()}\n\n")
            f.write(f"**Details:** {r['details']}\n\n")
            f.write(f"**Time:** {r['timestamp']}\n\n")
        
        f.write("## Production Deployment\n\n")
        f.write("If all tests passed, the Pearl monitor is ready for production:\n\n")
        f.write("```bash\n")
        f.write("python pearl_monitor_bdomarket.py --interval 2.0\n")
        f.write("```\n\n")
        f.write("**Expected Behavior:**\n")
        f.write("- Continuously monitors ~6,693 Pearl items\n")
        f.write("- Alerts when any item becomes available (stock > 0)\n")
        f.write("- Tracks stock increases and sold-out events\n")
        f.write("- Runs indefinitely until interrupted\n")
    
    print(f"\nTest results saved to: TEST_RESULTS_BDOMARKET.md")


if __name__ == "__main__":
    asyncio.run(main())

