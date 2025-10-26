"""
BDO Pearl Monitor - Parallel HTTP/2 Version
Monitors all 8 Pearl categories simultaneously with HTTP/2 Keep-Alive for maximum speed.
"""
import asyncio
import json
import os
import sys
import time
import argparse
from typing import Dict, Any, List, Tuple, Set, Optional

import httpx


URL = "https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketList"

PEARL_ITEM_CATEGORIES: List[Dict[str, Any]] = [
    {"mainCategory": 55, "subCategory": 1, "name": "Männliche Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 2, "name": "Weibliche Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 3, "name": "Männliche Outfits (Einzel)"},
    {"mainCategory": 55, "subCategory": 4, "name": "Weibliche Outfits (Einzel)"},
    {"mainCategory": 55, "subCategory": 5, "name": "Klassen-Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 6, "name": "Funktional (Tiere, Elixiere etc.)"},
    {"mainCategory": 55, "subCategory": 7, "name": "Reittiere (Pferdeausrüstung)"},
    {"mainCategory": 55, "subCategory": 8, "name": "Begleiter (Pets)"},
]


def load_auth_config(config_path: str) -> Dict[str, str]:
    """Load authentication config from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    required = ["cookie", "user_agent", "request_verification_token"]
    for key in required:
        if not data.get(key):
            raise ValueError(f"Missing '{key}' in {config_path}")
    
    return {
        "cookie": data["cookie"],
        "user_agent": data["user_agent"],
        "request_verification_token": data["request_verification_token"],
    }


def build_headers(user_agent: str, cookie: str) -> Dict[str, str]:
    """Build HTTP headers for marketplace requests."""
    return {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": user_agent,
        "cookie": cookie,
        "x-requested-with": "XMLHttpRequest",
        "origin": "https://eu-trade.naeu.playblackdesert.com",
        "referer": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-1",
    }


async def fetch_category(
    client: httpx.AsyncClient,
    token: str,
    category: Dict[str, Any],
    max_retries: int = 2
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Fetch items for a single category with retry logic.
    
    Returns:
        Tuple of (category, list_of_items_with_stock)
    
    Raises:
        httpx.HTTPStatusError: On 401/403 (auth failure)
        Exception: On other unrecoverable errors
    """
    payload = {
        "__RequestVerificationToken": token,
        "mainCategory": category["mainCategory"],
        "subCategory": category["subCategory"],
    }
    
    for attempt in range(max_retries):
        try:
            response = await client.post(URL, data=payload)
            
            # Check for auth errors immediately
            if response.status_code in (401, 403):
                raise httpx.HTTPStatusError(
                    f"Auth failed ({response.status_code})",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract items with stock
            items = []
            if isinstance(data, dict) and isinstance(data.get("marketList"), list):
                for item in data["marketList"]:
                    if isinstance(item, dict):
                        sum_count = int(item.get("sumCount", 0) or 0)
                        if sum_count >= 1:
                            items.append(item)
            
            return category, items
        
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
            else:
                raise Exception(f"Network error after {max_retries} retries: {e}")
        
        except httpx.HTTPStatusError:
            # Auth errors should not be retried
            raise
        
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    return category, []


async def monitor_loop(
    client: httpx.AsyncClient,
    token: str,
    interval: float,
    seen: Set[Tuple[int, str, int]]
) -> None:
    """Main monitoring loop that fetches all categories in parallel."""
    loop_count = 0
    
    while True:
        loop_count += 1
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Fire all 8 category requests in parallel
        tasks = [
            fetch_category(client, token, cat)
            for cat in PEARL_ITEM_CATEGORIES
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        total_found = 0
        new_found = 0
        
        for result in results:
            if isinstance(result, httpx.HTTPStatusError):
                # Auth error - exit immediately
                print("\n" + "=" * 60)
                print("🚨 AUTHENTIFIZIERUNGSFEHLER!")
                print("=" * 60)
                print("Cookie oder __RequestVerificationToken ist abgelaufen.")
                print("Bitte aktualisiere config/trader_auth.json mit frischen Werten.")
                print("=" * 60)
                sys.exit(1)
            
            elif isinstance(result, Exception):
                # Network or other error - log and continue
                print(f"[ERROR] {result}")
                continue
            
            # Successful fetch
            category, items = result
            
            if items:
                for item in items:
                    total_found += 1
                    
                    # Deduplication key: (mainKey, name, subCategory)
                    key = (
                        item.get("mainKey"),
                        item.get("name"),
                        category["subCategory"]
                    )
                    
                    if key not in seen:
                        seen.add(key)
                        new_found += 1
                        
                        # Print alert for new item
                        print("\n" + "=" * 60)
                        print("🚨🚨🚨 NEUER ARTIKEL GEFUNDEN! 🚨🚨🚨")
                        print("=" * 60)
                        print(f"Kategorie: {category['name']}")
                        print(f"Name: {item.get('name', 'Unbekannt')}")
                        print(f"Verfügbarkeit: {item.get('sumCount')}")
                        print(f"Item-ID (mainKey): {item.get('mainKey')}")
                        print(f"Preis: {item.get('pricePerOne', 'N/A')}")
                        print("=" * 60 + "\n")
        
        # Summary line
        elapsed = time.time() - start_time
        if new_found > 0:
            status = f"✨ {new_found} NEU"
        elif total_found > 0:
            status = f"👀 {total_found} bekannt"
        else:
            status = "✓ leer"
        
        print(f"[{timestamp}] Loop #{loop_count} | {elapsed:.2f}s | {status}")
        
        # Wait before next loop
        await asyncio.sleep(interval)


async def run_monitor(config_path: str, interval: float) -> None:
    """Main entry point for the monitor."""
    # Load auth config
    print("Lade Authentifizierungsdaten...")
    auth = load_auth_config(config_path)
    
    # Build headers
    headers = build_headers(auth["user_agent"], auth["cookie"])
    token = auth["request_verification_token"]
    
    # Setup HTTP/2 client with keep-alive
    limits = httpx.Limits(
        max_connections=16,
        max_keepalive_connections=16
    )
    timeout = httpx.Timeout(connect=8.0, read=8.0, write=8.0, pool=8.0)
    
    print(f"Starte Monitor (Intervall: {interval}s, HTTP/2 + Keep-Alive)")
    print("Drücke STRG+C zum Beenden.\n")
    
    seen: Set[Tuple[int, str, int]] = set()
    
    async with httpx.AsyncClient(
        http2=True,
        headers=headers,
        limits=limits,
        timeout=timeout
    ) as client:
        try:
            await monitor_loop(client, token, interval, seen)
        except KeyboardInterrupt:
            print("\n\nMonitor gestoppt.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BDO Pearl Monitor - Parallel HTTP/2 Version"
    )
    parser.add_argument(
        "--config",
        default=os.path.join("config", "trader_auth.json"),
        help="Pfad zur Auth-Konfigurationsdatei (Standard: config/trader_auth.json)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Abfrageintervall in Sekunden (Standard: 0.2)"
    )
    
    args = parser.parse_args()
    
    # Validate interval
    if args.interval < 0.05:
        print("WARNUNG: Intervall < 0.05s kann zu Rate-Limits führen!")
        args.interval = 0.05
    
    # Run async monitor
    try:
        asyncio.run(run_monitor(args.config, args.interval))
    except KeyboardInterrupt:
        print("\nMonitor beendet.")
        sys.exit(0)


if __name__ == "__main__":
    main()


