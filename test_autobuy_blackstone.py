#!/usr/bin/env python3
"""
Auto-Buy Verification Test

Monitors a high-availability item (Black Stone, ID 16001) and places a tiny
buy order (qty=1) when stock is detected to verify trading API calls work.

Safety:
- Dry-run by default (no transaction) unless --confirm passed
- Enforces price cap and quantity limits
- Optional --cancel to cancel created order immediately (if order number returned)
"""
import asyncio
import time
import argparse
import os
import sys
import io
from typing import Optional, Tuple

# Fix Windows console encoding issue - set BEFORE importing bdomarket
if os.name == 'nt':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from bdomarket import Market
from bdomarket.identifiers import MarketRegion

# Only import trading utils when needed to avoid credential requirement on dry-run
try:
	from utils.market_trader import MarketTrader, load_credentials
except Exception:  # Fallback for dry-run environments
	MarketTrader = None
	def load_credentials():
		return None

# Windows console safety
if os.name == 'nt':
	os.environ['PYTHONIOENCODING'] = 'utf-8'


async def fetch_item_info(market: Market, item_id: int) -> Tuple[str, int, int]:
	"""Return (name, stock, base_price) for given item id using multiple endpoints.
	Tries in order: get_item → get_world_market_search_list → post_world_market_search_list.
	"""
	# 1) get_item(ids=[...]) - NOTE: Returns basic info only, no stock/price
	try:
		res = await market.get_item(ids=[str(item_id)])
		if res.success and res.content:
			it = res.content[0] if isinstance(res.content, list) else res.content
			name = it.get('name', 'Unknown')
			stock = int(it.get('stock', 0) or 0)
			base = int(it.get('basePrice', 0) or 0)
			# Don't return early if stock/basePrice are missing - continue to next method
			if name != 'Unknown' and stock > 0 and base > 0:
				return name, stock, base
	except Exception:
		pass
	# 2) get_world_market_search_list(ids=[...])
	try:
		res = await market.get_world_market_search_list(ids=[str(item_id)])
		if res.success and res.content:
			it = res.content[0] if isinstance(res.content, list) else res.content
			name = it.get('name', 'Unknown')
			# Note: bdomarket returns 'currentStock' not 'stock'
			stock = int(it.get('currentStock', it.get('stock', 0)) or 0)
			base = int(it.get('basePrice', 0) or 0)
			if name != 'Unknown':
				return name, stock, base
	except Exception:
		pass
	# 3) post_world_market_search_list("id") — fallback
	try:
		res = await market.post_world_market_search_list(str(item_id))
		if res.success and res.content:
			it = res.content[0] if isinstance(res.content, list) else res.content
			name = it.get('name', 'Unknown')
			stock = int(it.get('stock', 0) or 0)
			base = int(it.get('basePrice', 0) or 0)
			return name, stock, base
	except Exception:
		pass
	# Not found
	return ("Unknown", 0, 0)


async def monitor_and_buy(
	item_id: int,
	interval: float,
	price_cap: int,
	quantity: int,
	sid: int,
	confirm: bool,
	timeout: float,
	cancel_after: bool,
) -> None:
	print("=" * 70)
	print("AUTO-BUY VERIFICATION TEST")
	print("=" * 70)
	print(f"Item ID: {item_id} | Qty: {quantity} | Interval: {interval:.2f}s")
	print(f"Price Cap: {price_cap:,} | SID: {sid} | Confirm: {confirm}")
	print(f"Timeout: {int(timeout)}s | Cancel After: {cancel_after}")
	print("=" * 70 + "\n")

	async with Market(region=MarketRegion.EU) as market:
		name, stock, base = await fetch_item_info(market, item_id)
		print(f"Resolved item: {name} | Stock={stock} | BasePrice={base:,}")
		if price_cap <= 0:
			price_cap = int(base * 1.10) if base > 0 else 200_000
			print(f"Auto price cap set to {price_cap:,}")
		print()

		start = time.time()
		last_stock = None

		# Only initialize trader/credentials when actually confirming a buy
		trader = None
		if confirm:
			creds = load_credentials()
			if not creds or MarketTrader is None:
				print("ERROR: No trading credentials. Run 'python trader.py auth' first.")
				return
			trader_cm = MarketTrader(creds)
			trader = await trader_cm.__aenter__()  # manual to control scope
			print("Trading client ready.\n")
		else:
			print("Dry-run mode: credentials not required.\n")

		try:
			while True:
				if time.time() - start > timeout:
					print("Timeout reached. Test finished (no buy).")
					return

				# Check current item state
				name, stock, base = await fetch_item_info(market, item_id)
				print(f"Check: {name} | stock={stock} | base={base:,}")

				# Trigger condition: any stock > 0
				if stock > 0:
					print("\n" + "=" * 70)
					print("ALERT: STOCK AVAILABLE — Attempting to BUY")
					print("=" * 70)
					print(f"Item: {name} (ID {item_id})")
					print(f"Stock: {stock}")
					print(f"Using price cap: {price_cap:,}")
					print(f"Quantity: {quantity}")

					if not confirm:
						print("\nDRY-RUN: No buy executed. Use --confirm to perform a live buy.")
						return

					# Execute live buy
					buy_t0 = time.time()
					result = await trader.buy_item(item_id=item_id, sid=sid, price=price_cap, quantity=quantity)
					buy_ms = (time.time() - buy_t0) * 1000

					print("\nBuy result:")
					print(f"  success = {result.success}")
					print(f"  message = {result.message}")
					print(f"  details = {result.details}")
					print(f"  latency = {buy_ms:.1f} ms\n")

					# Optional cleanup (order cancel)
					if cancel_after and result.success:
						order_no = 0
						try:
							order_no = int(result.details.get('orderNo', 0))
						except Exception:
							order_no = 0
						if order_no:
							print(f"Attempting to cancel order #{order_no}...")
							cancel_res = await trader.cancel_listing(item_id=item_id, sid=sid, order_no=order_no)
							print(f"Cancel result: success={cancel_res.success} message={cancel_res.message}")
						else:
							print("No order number returned; skipping cancel.")

					print("Test finished.")
					return

				last_stock = stock
				await asyncio.sleep(interval)
		finally:
			if trader is not None:
				await trader.__aexit__(None, None, None)


def main() -> None:
	ap = argparse.ArgumentParser(description="Auto-Buy Verification Test (Black Stone 16001)")
	ap.add_argument("--item-id", type=int, default=16001, help="Item ID (default 16001 Black Stone)")
	ap.add_argument("--interval", type=float, default=1.0, help="Polling interval seconds (default 1.0)")
	ap.add_argument("--price-cap", type=int, default=0, help="Max price per item; 0 to auto-set to base*1.10")
	ap.add_argument("--quantity", type=int, default=1, help="Quantity to buy (default 1)")
	ap.add_argument("--sid", type=int, default=0, help="Sub-item ID (enhancement level)")
	ap.add_argument("--timeout", type=float, default=180.0, help="Timeout seconds (default 180)")
	ap.add_argument("--confirm", action="store_true", help="Execute live buy (default: dry-run)")
	ap.add_argument("--cancel", action="store_true", help="Cancel created order if possible")
	args = ap.parse_args()

	# Guardrails
	if args.quantity <= 0 or args.quantity > 10:
		print("ERROR: Quantity must be between 1 and 10 for safety.")
		return

	asyncio.run(monitor_and_buy(
		item_id=args.item_id,
		interval=max(0.3, args.interval),
		price_cap=args.price_cap,
		quantity=args.quantity,
		sid=args.sid,
		confirm=args.confirm,
		timeout=args.timeout,
		cancel_after=args.cancel,
	))


if __name__ == "__main__":
	main()
