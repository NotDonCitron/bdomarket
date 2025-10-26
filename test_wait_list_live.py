#!/usr/bin/env python3
"""
BDO Wait List Live Monitor
Monitors items being registered for sale (more active than just stock monitoring).
"""
import asyncio
import time
import argparse
import os
from typing import Dict, Any, List, Set

# Fix Windows console encoding issue - set BEFORE importing bdomarket
if os.name == 'nt':
	os.environ['PYTHONIOENCODING'] = 'utf-8'

from bdomarket import Market
from bdomarket.identifiers import MarketRegion


async def monitor_wait_list(interval: float, duration: float) -> None:
    """Monitor Wait List for items being registered."""
    print("=== BDO Wait List Live Monitor ===")
    print(f"Interval: {interval:.2f}s")
    print(f"Duration: {duration:.0f}s")
    print("Press CTRL+C to stop early.\n")
    
    seen_items: Set[int] = set()
    loop_count = 0
    start_time = time.time()
    
    async with Market(region=MarketRegion.EU) as market:
        while time.time() - start_time < duration:
            loop_count += 1
            loop_start = time.time()
            
            try:
                result = await market.post_world_market_wait_list()
                if not result.success:
                    print(f"[ERROR] API call failed: {result.status_code}")
                    await asyncio.sleep(interval)
                    continue
                
                items = result.content if isinstance(result.content, list) else []
                
                # Track new items
                new_items = []
                for item in items:
                    item_id = int(item.get("id", 0))
                    if item_id and item_id not in seen_items:
                        seen_items.add(item_id)
                        new_items.append(item)
                
                # Alert on new items
                for item in new_items:
                    name = item.get("name", "Unknown")
                    item_id = item.get("id", "?")
                    price = int(item.get("basePrice", 0) or 0)
                    print("="*60)
                    print("NEW ITEM IN WAIT LIST!")
                    print("="*60)
                    print(f"Name: {name}")
                    print(f"ID: {item_id}")
                    print(f"Price: {price:,}")
                    print("="*60)
                
                elapsed = time.time() - loop_start
                total_time = time.time() - start_time
                print(f"[Loop #{loop_count}] wait_list={len(items)} new={len(new_items)} "
                      f"time={elapsed:.2f}s total={total_time:.0f}s")
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nStopped by user.")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                await asyncio.sleep(interval)
    
    print(f"\n=== Test Complete ===")
    print(f"Total items seen: {len(seen_items)}")
    print(f"Total loops: {loop_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="BDO Wait List Live Monitor")
    parser.add_argument("--interval", type=float, default=2.0, 
                        help="Polling interval in seconds (default 2.0)")
    parser.add_argument("--duration", type=float, default=120.0,
                        help="Test duration in seconds (default 120)")
    args = parser.parse_args()
    
    try:
        asyncio.run(monitor_wait_list(max(0.5, args.interval), args.duration))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

