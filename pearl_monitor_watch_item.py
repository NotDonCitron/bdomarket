import asyncio
import time
import argparse
import os
from typing import Dict, Any, List

# Fix Windows console encoding issue - set BEFORE importing bdomarket
if os.name == 'nt':
	os.environ['PYTHONIOENCODING'] = 'utf-8'

from bdomarket import Market
from bdomarket.identifiers import MarketRegion


async def fetch_item(item_id: int) -> List[Dict[str, Any]]:
	async with Market(region=MarketRegion.EU) as market:
		# post_world_market_search_list accepts id string(s)
		result = await market.post_world_market_search_list(str(item_id))
		if not result.success:
			return []
		content = result.content
		if isinstance(content, list):
			return content
		elif isinstance(content, dict):
			return [content]
		return []


async def watch_item(item_id: int, interval: float) -> None:
	print("=== BDO Pearl Single-Item Watcher ===")
	print(f"Item ID: {item_id}")
	print(f"Interval: {interval:.2f}s")
	print("Press CTRL+C to stop.\n")

	last_stock = None
	loop_count = 0

	while True:
		loop_count += 1
		start = time.time()
		try:
			items = await fetch_item(item_id)
		except Exception as e:
			print(f"[ERROR] fetch failed: {e}")
			await asyncio.sleep(interval)
			continue

		if items:
			item = items[0]
			name = item.get("name", "Unknown")
			stock = int(item.get("stock", 0) or 0)
			price = int(item.get("basePrice", 0) or 0)

			if last_stock is None:
				print(f"Initial: {name} stock={stock} price={price:,}")
			elif stock > 0 and (last_stock or 0) <= 0:
				print("\n============================================================")
				print("ALERT: TARGET ITEM AVAILABLE!")
				print("============================================================")
				print(f"Name: {name}")
				print(f"Item ID: {item_id}")
				print(f"Stock: {stock}")
				print(f"Price: {price:,}")
				print("============================================================\n")
			elif last_stock is not None and stock != last_stock:
				print(f"Stock update: {name} {last_stock} -> {stock}")

			last_stock = stock
		else:
			print("No data for item (maybe invalid ID)")

		elapsed = time.time() - start
		print(f"[Loop #{loop_count}] time={elapsed:.2f}s")
		await asyncio.sleep(interval)


def main() -> None:
	parser = argparse.ArgumentParser(description="BDO Pearl Single-Item Watcher")
	parser.add_argument("item_id", type=int, help="BDO item ID to watch")
	parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds (default 2.0)")
	args = parser.parse_args()
	try:
		asyncio.run(watch_item(args.item_id, max(0.5, args.interval)))
	except KeyboardInterrupt:
		print("\nStopped.")


if __name__ == "__main__":
	main()
