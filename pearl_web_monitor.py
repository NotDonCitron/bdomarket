#!/usr/bin/env python3
"""
Playwright-based Pearl Web Monitor

- Launches Chromium and navigates to Pearl Shop
- Intercepts network responses to detect new listings
- Uses PearlValueCalculator for extraction profit/ROI
- Alerts via PearlAlerter (terminal/toast/discord) when profitable

Usage:
  python pearl_web_monitor.py --test               # simulate items
  python pearl_web_monitor.py --dry-run            # no alerts
  python pearl_web_monitor.py --headless           # run headless
"""

import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys
import os

# Ensure Windows console uses UTF-8 to avoid emoji encoding errors from dependencies
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul 2>&1')
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    except Exception:
        pass

from utils.pearl_calculator import PearlValueCalculator
from utils.market_client import MarketClient
from utils.pearl_alerts import PearlAlerter

# Optional: use httpx if we later need REST calls


class PearlWebMonitor:
    def __init__(self, headless: bool = False, dry_run: bool = False, test_mode: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.test_mode = test_mode

        self.market_client = MarketClient()
        self.calculator = PearlValueCalculator(self.market_client)
        self.alerter = PearlAlerter(terminal_enabled=True, terminal_beep=True, toast_enabled=False)

        self.browser = None
        self.context = None
        self.page = None
        
        # Registration detection caches
        self.seen_items = set()
        self.seen_registrations = set()

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        # Force a modern Chrome UA to bypass unsupported browser message
        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            )
        )
        await self._load_cookies_if_available()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.context.close()
        await self.browser.close()
        await self.pw.stop()

    async def _load_cookies_if_available(self):
        # Reuse cookies from config/trader_auth.json if present
        auth_path = Path('config/trader_auth.json')
        if not auth_path.exists():
            return
        try:
            data = json.loads(auth_path.read_text(encoding='utf-8'))
            session_id = data.get('session_id')
            if session_id:
                await self.context.add_cookies([
                    {
                        'name': 'session_id',
                        'value': session_id,
                        'domain': '.bdoverseas.com',
                        'path': '/',
                        'httpOnly': True,
                        'secure': True
                    }
                ])
        except Exception:
            pass

    async def _ensure_prices(self):
        if self.test_mode:
            # Mock prices
            self.calculator.cron_price = 2_500_000
            self.calculator.valks_price = 20_000_000
            self.calculator.last_price_update = datetime.now()
            return
        await self.calculator.update_prices()

    async def run(self):
        print("Pearl Web Monitor starting...")
        await self._ensure_prices()

        if self.test_mode:
            await self._run_test_items()
            return

        # Navigate to Central Market (Pearl category page example)
        target_url = 'https://eu-trade.naeu.playblackdesert.com/Home/list/25-1'
        await self.page.goto(target_url)

        # If redirected to unsupported/login, wait for user to resolve manually
        # and then continue when the list table appears
        try:
            await self.page.wait_for_selector('table', timeout=60000)
        except Exception:
            pass

        # Listen to responses
        self.page.on('response', self._on_response)

        print("Monitoring central market... Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

    async def _run_test_items(self):
        demo_items = [
            { 'id': 40001, 'name': 'Kibelius Outfit Set (PREMIUM)', 'base_price': 1_350_000_000 },
            { 'id': 40002, 'name': 'Classic Outfit Set', 'base_price': 980_000_000 },
            { 'id': 40003, 'name': 'Simple Outfit', 'base_price': 650_000_000 },
            { 'id': 40004, 'name': 'Mount Gear Package', 'base_price': 1_200_000_000 },
        ]
        for item in demo_items:
            await self._process_item(item)
        print("Test mode completed.")

    async def _on_response(self, response):
        try:
            url = response.url.lower()
            # Watch central market endpoints too
            if ('pearlshop' not in url) and ('eu-trade.naeu.playblackdesert.com' not in url):
                return
            if response.request.resource_type not in ('xhr', 'fetch'):
                return
            # Attempt to parse JSON body
            try:
                data = await response.json()
            except Exception:
                text = await response.text()
                try:
                    data = json.loads(text)
                except Exception:
                    return
            # Normalize and extract items
            items = self._extract_items_from_payload(data)
            if not items:
                return

            # Heuristic: treat 'wait'/'register' endpoints as registration feeds
            is_registration_feed = any(k in url for k in ['wait', 'register', 'regist'])

            for item in items:
                # Basic identity fields
                item_id = item.get('id') or 0
                name = item.get('name') or 'Unknown'
                price = int(item.get('base_price') or item.get('price') or 0)
                reg_ts = (
                    item.get('regDate') or item.get('registerTime') or item.get('listed_at') or ''
                )

                # Seen cache for generic listings
                generic_key = f"{item_id}:{price}"
                if generic_key not in self.seen_items:
                    self.seen_items.add(generic_key)

                # Registration detection
                if is_registration_feed:
                    reg_key = f"{item_id}:{price}:{reg_ts}"
                    if reg_key not in self.seen_registrations:
                        self.seen_registrations.add(reg_key)
                        ts = datetime.now().strftime('%H:%M:%S')
                        print(f"[NEW REGISTRATION {ts}] {name} (ID {item_id}) @ {price:,}")

                # Continue normal processing for profitability alerts (pearl items)
                await self._process_item(item)
        except Exception:
            return

    def _extract_items_from_payload(self, data: Any) -> List[Dict[str, Any]]:
        items = []
        if isinstance(data, dict):
            cand = data.get('items') or data.get('data') or []
            if isinstance(cand, list):
                for it in cand:
                    if isinstance(it, dict) and ('name' in it or 'id' in it):
                        items.append({
                            'id': it.get('id') or it.get('itemId') or 0,
                            'name': it.get('name') or it.get('title') or 'Unknown',
                            'base_price': it.get('price') or it.get('base_price') or 0,
                        })
        elif isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and ('name' in it or 'id' in it):
                    items.append({
                        'id': it.get('id') or it.get('itemId') or 0,
                        'name': it.get('name') or it.get('title') or 'Unknown',
                        'base_price': it.get('price') or it.get('base_price') or 0,
                    })
        return items

    async def _process_item(self, item: Dict[str, Any]):
        item_id = item.get('id')
        item_name = item.get('name', f'Item_{item_id}')
        price = int(item.get('base_price') or 0)
        if not price:
            return
        outfit_type = self.calculator.detect_outfit_type(item_name)
        value = self.calculator.calculate_value(outfit_type, price)
        if not value:
            return
        if value.is_profitable:
            if not self.dry_run:
                await self.alerter.send_alert({'id': item_id, 'name': item_name}, value)
            else:
                print(f"[DRY RUN] Would alert: {item_name}")
        else:
            print(f"Item not profitable: {item_name}")


async def main():
    parser = argparse.ArgumentParser(description='Playwright-based Pearl Web Monitor')
    parser.add_argument('--headless', action='store_true', help='Run browser headless')
    parser.add_argument('--dry-run', action='store_true', help='Do not send alerts')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no browser)')
    args = parser.parse_args()

    monitor = PearlWebMonitor(headless=args.headless, dry_run=args.dry_run, test_mode=args.test)

    if args.test:
        await monitor._ensure_prices()
        await monitor._run_test_items()
        return

    async with monitor:
        await monitor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
