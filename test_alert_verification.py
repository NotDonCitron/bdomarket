#!/usr/bin/env python3
"""
Alert Logic Verification Test
Testet ob die Alert-Logik funktioniert, ohne echte Käufe.
Nutzt Hot List (ändert sich ständig) statt Pearl Items (selten).
"""
import asyncio
import time
import os
from bdomarket import Market
from bdomarket.identifiers import MarketRegion

# Fix Windows console encoding
if os.name == 'nt':
	os.environ['PYTHONIOENCODING'] = 'utf-8'


async def verify_alert_logic() -> None:
	"""Verifiziert dass neue Items erkannt werden."""
	print("=" * 70)
	print("ALERT LOGIC VERIFICATION TEST")
	print("=" * 70)
	print("Testet ob der Monitor neue Items erkennt")
	print("Nutzt Hot List (ändert sich oft) statt Pearl Items (selten)")
	print("Duration: ~1 Minute (20 loops)")
	print("=" * 70)
	print()
	
	last_items = {}
	loop_count = 0
	alerts_triggered = 0
	stock_updates = 0
	sold_out_events = 0
	
	async with Market(region=MarketRegion.EU) as market:
		print("Market client initialized\n")
		print("Starting monitoring...\n")
		
		for loop_count in range(1, 21):  # 20 loops ≈ 1 minute
			start_time = time.time()
			
			try:
				result = await market.post_world_market_hot_list()
				if not result.success:
					print(f"[Loop {loop_count}] API call failed")
					await asyncio.sleep(3)
					continue
				
				items = result.content if isinstance(result.content, list) else []
				current_items = {item.get("id"): item for item in items if item.get("id")}
				
				# Alert detection logic (identical to pearl monitor semantics)
				new_available = []
				stock_increased = []
				sold_out = []
				
				for item_id, item in current_items.items():
					try:
						new_stock = int(item.get("stock", 0) or 0)
					except Exception:
						new_stock = 0
					old_item = last_items.get(item_id, {})
					old_stock = int(old_item.get("stock", 0) or 0)
					
					if old_stock <= 0 and new_stock > 0:
						new_available.append((item_id, item, old_stock, new_stock))
					elif new_stock > old_stock and old_stock > 0:
						stock_increased.append((item_id, item, old_stock, new_stock))
					elif old_stock > 0 and new_stock == 0:
						sold_out.append((item_id, item, old_stock))
				
				for item_id, item, old_s, new_s in new_available:
					name = item.get("name", "Unknown")
					price = int(item.get("basePrice", 0) or 0)
					print("\n" + "=" * 70)
					print("ALERT: NEW ITEM AVAILABLE!")
					print("=" * 70)
					print(f"Name: {name}")
					print(f"Item ID: {item_id}")
					print(f"Stock Change: {old_s} -> {new_s}")
					print(f"Price: {price:,}")
					print(f"Time: {time.strftime('%H:%M:%S')}")
					print("=" * 70 + "\n")
					alerts_triggered += 1
				
				for item_id, item, old_s, new_s in stock_increased:
					name = item.get("name", "Unknown")
					print(f"  [STOCK UP] {name}: {old_s} -> {new_s}")
					stock_updates += 1
				
				for item_id, item, old_s in sold_out:
					name = item.get("name", "Unknown")
					print(f"  [SOLD OUT] {name} (had {old_s})")
					sold_out_events += 1
				
				elapsed = time.time() - start_time
				if not (new_available or stock_increased or sold_out):
					print(f"[Loop {loop_count}] Items: {len(current_items)}, No changes (time={elapsed:.2f}s)")
				
				last_items = current_items
			except Exception as e:
				print(f"[Loop {loop_count}] ERROR: {e}")
			
			await asyncio.sleep(3)
	
	print("\n" + "=" * 70)
	print("TEST COMPLETE")
	print("=" * 70)
	print(f"Total Loops: {loop_count}")
	print(f"Alerts Triggered: {alerts_triggered}")
	print(f"Stock Updates: {stock_updates}")
	print(f"Sold Out Events: {sold_out_events}")
	print("=" * 70)
	
	if alerts_triggered > 0:
		print("\nVERIFICATION: PASS")
		print("Die Alert-Logik funktioniert!")
	else:
		print("\nVERIFICATION: INCONCLUSIVE")
		print("Keine Alerts - Hot List war zu stabil. Länger laufen lassen.")
	print()


def main() -> None:
	print("\nDieser Test verifiziert die Alert-Logik ohne echte Käufe.")
	print("Hot List Items ändern sich oft, perfekt zum Testen.\n")
	asyncio.run(verify_alert_logic())


if __name__ == "__main__":
	main()
