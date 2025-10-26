import asyncio
import time
import argparse
import os
from typing import Dict, Any, List, Tuple

# Fix Windows console encoding issue - set BEFORE importing bdomarket
if os.name == 'nt':
	os.environ['PYTHONIOENCODING'] = 'utf-8'

from bdomarket import Market
from bdomarket.identifiers import MarketRegion


def build_index(items: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
	index: Dict[int, Dict[str, Any]] = {}
	for item in items:
		try:
			item_id = int(item.get("id"))
			index[item_id] = item
		except Exception:
			continue
	return index


async def monitor_pearl_items(interval: float) -> None:
	print("=== BDO Pearl Monitor (bdomarket) ===")
	print(f"Interval: {interval:.2f}s")
	print("Press CTRL+C to stop.\n")

	last_index: Dict[int, Dict[str, Any]] = {}
	loop_count = 0

	# Reuse a single Market client to avoid repeated update banners and reduce overhead
	async with Market(region=MarketRegion.EU) as market:
		while True:
			loop_count += 1
			start = time.time()
			try:
				result = await market.post_pearl_items()
				items = result.content if (result.success and isinstance(result.content, list)) else []
			except Exception as e:
				print(f"[ERROR] fetch failed: {e}")
				await asyncio.sleep(interval)
				continue

			current = build_index(items)

			# Count with stock
			with_stock = [it for it in items if int(it.get("stock", 0) or 0) > 0]

			# Detect changes
			new_available: List[Tuple[int, Dict[str, Any]]] = []
			stock_increase: List[Tuple[int, int, int, Dict[str, Any]]] = []  # (id, old, new, item)
			sold_out: List[Tuple[int, int, Dict[str, Any]]] = []  # (id, old, item)

			for iid, it in current.items():
				try:
					new_stock = int(it.get("stock", 0) or 0)
				except Exception:
					new_stock = 0
				old_stock = int((last_index.get(iid, {}).get("stock", 0) or 0))

				# Became available
				if old_stock <= 0 and new_stock > 0:
					new_available.append((iid, it))
				# Stock increased
				elif new_stock > old_stock and old_stock > 0:
					stock_increase.append((iid, old_stock, new_stock, it))

			# Sold out detection (only if previously had stock)
			for iid, prev in last_index.items():
				prev_stock = int(prev.get("stock", 0) or 0)
				if prev_stock > 0 and iid in current:
					cur_stock = int(current[iid].get("stock", 0) or 0)
					if cur_stock == 0:
						sold_out.append((iid, prev_stock, prev))

			# Emit alerts (ASCII-only for Windows console safety)
			for iid, it in new_available:
				name = it.get("name", "Unknown")
				stock = int(it.get("stock", 0) or 0)
				price = int(it.get("basePrice", 0) or 0)
				print("\n============================================================")
				print("ALERT: PEARL ITEM AVAILABLE!")
				print("============================================================")
				print(f"Name: {name}")
				print(f"Item ID: {iid}")
				print(f"Stock: {stock}")
				print(f"Price: {price:,}")
				print("============================================================\n")

			for iid, old_s, new_s, it in stock_increase:
				name = it.get("name", "Unknown")
				print(f"STOCK UPDATE: {name} (ID {iid}) {old_s} -> {new_s}")

			for iid, old_s, it in sold_out:
				name = it.get("name", "Unknown")
				print(f"SOLD OUT: {name} (ID {iid}) last stock {old_s}")

			elapsed = time.time() - start
			print(f"[Loop #{loop_count}] items={len(items)} with_stock={len(with_stock)} time={elapsed:.2f}s")

			# Rotate state
			last_index = current
			await asyncio.sleep(interval)


def main() -> None:
	parser = argparse.ArgumentParser(description="BDO Pearl Monitor (bdomarket)")
	parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds (default 2.0)")
	args = parser.parse_args()
	try:
		asyncio.run(monitor_pearl_items(max(0.5, args.interval)))
	except KeyboardInterrupt:
		print("\nStopped.")


if __name__ == "__main__":
	main()
