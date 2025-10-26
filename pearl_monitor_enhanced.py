"""
BDO Pearl Monitor - ENHANCED VERSION
Combines Wait List monitoring + Differential Detection for maximum coverage.
"""
import asyncio
import json
import os
import sys
import time
import argparse
from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field

import httpx


URL_MARKET_LIST = "https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketList"
URL_WAIT_LIST = "https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketWaitList"

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


@dataclass
class MarketState:
    """Tracks market state for differential detection."""
    category_items: Dict[int, Dict[int, Dict[str, Any]]] = field(default_factory=dict)
    wait_list_items: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    def update_category(self, cat_id: int, items: List[Dict[str, Any]]) -> Tuple[Set[int], Set[int], Dict[int, Tuple[int, int]]]:
        """
        Update category state and return changes.
        
        Returns:
            (added_keys, removed_keys, stock_changes)
            stock_changes: {mainKey: (old_stock, new_stock)}
        """
        old_items = self.category_items.get(cat_id, {})
        old_keys = set(old_items.keys())
        
        new_items = {item['mainKey']: item for item in items}
        new_keys = set(new_items.keys())
        
        added = new_keys - old_keys
        removed = old_keys - new_keys
        
        # Check stock changes for existing items
        stock_changes = {}
        for key in old_keys & new_keys:
            old_stock = old_items[key].get('sumCount', 0)
            new_stock = new_items[key].get('sumCount', 0)
            if old_stock != new_stock:
                stock_changes[key] = (old_stock, new_stock)
        
        self.category_items[cat_id] = new_items
        return added, removed, stock_changes
    
    def update_wait_list(self, items: List[Dict[str, Any]]) -> Set[int]:
        """
        Update wait list state and return new items.
        
        Returns:
            Set of new mainKeys
        """
        old_keys = set(self.wait_list_items.keys())
        new_items = {item['mainKey']: item for item in items}
        new_keys = set(new_items.keys())
        
        added = new_keys - old_keys
        self.wait_list_items = new_items
        return added


def load_auth_config(config_path: str) -> Dict[str, str]:
    """Load authentication config from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    required = ["cookie", "user_agent", "request_verification_token"]
    for key in required:
        if not data.get(key):
            raise ValueError(f"Missing '{key}' in {config_path}")
    
    return data


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


async def fetch_wait_list(
    client: httpx.AsyncClient,
    token: str,
    max_retries: int = 2
) -> List[Dict[str, Any]]:
    """
    Fetch wait list and filter for Pearl items only.
    
    Returns:
        List of Pearl items from wait list
    """
    payload = {"__RequestVerificationToken": token}
    
    for attempt in range(max_retries):
        try:
            response = await client.post(URL_WAIT_LIST, data=payload)
            
            if response.status_code in (401, 403):
                raise httpx.HTTPStatusError(
                    f"Auth failed ({response.status_code})",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Filter for Pearl items (mainCategory == 55)
            pearl_items = []
            if isinstance(data, dict) and isinstance(data.get("waitList"), list):
                for item in data["waitList"]:
                    if isinstance(item, dict) and item.get("mainCategory") == 55:
                        pearl_items.append(item)
            
            return pearl_items
        
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
            else:
                raise Exception(f"Wait list fetch error after {max_retries} retries: {e}")
        
        except httpx.HTTPStatusError:
            raise
        
        except Exception as e:
            raise Exception(f"Wait list unexpected error: {e}")
    
    return []


async def fetch_category(
    client: httpx.AsyncClient,
    token: str,
    category: Dict[str, Any],
    max_retries: int = 2
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Fetch items for a single market category."""
    payload = {
        "__RequestVerificationToken": token,
        "mainCategory": category["mainCategory"],
        "subCategory": category["subCategory"],
    }
    
    for attempt in range(max_retries):
        try:
            response = await client.post(URL_MARKET_LIST, data=payload)
            
            if response.status_code in (401, 403):
                raise httpx.HTTPStatusError(
                    f"Auth failed ({response.status_code})",
                    request=response.request,
                    response=response
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract ALL items (not just those with stock)
            items = []
            if isinstance(data, dict) and isinstance(data.get("marketList"), list):
                items = [item for item in data["marketList"] if isinstance(item, dict)]
            
            return category, items
        
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
                continue
            else:
                raise Exception(f"Category fetch error after {max_retries} retries: {e}")
        
        except httpx.HTTPStatusError:
            raise
        
        except Exception as e:
            raise Exception(f"Category unexpected error: {e}")
    
    return category, []


async def monitor_loop_enhanced(
    client: httpx.AsyncClient,
    token: str,
    interval: float
) -> None:
    """Enhanced monitoring loop with Wait List + Differential Detection."""
    state = MarketState()
    loop_count = 0
    
    print("=" * 70)
    print("🔍 ENHANCED MONITORING AKTIV")
    print("=" * 70)
    print("Features:")
    print("  - Wait List: Erkennt Items die GERADE gelistet werden")
    print("  - Differential: Erkennt neue Items in Kategorien")
    print("  - Stock Changes: Zeigt Verfügbarkeits-Änderungen")
    print("=" * 70)
    print()
    
    while True:
        loop_count += 1
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Parallel: Wait List + All Pearl Categories
        tasks = [
            fetch_wait_list(client, token),
            *[fetch_category(client, token, cat) for cat in PEARL_ITEM_CATEGORIES]
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for auth errors
        for result in results:
            if isinstance(result, httpx.HTTPStatusError):
                print("\n" + "=" * 70)
                print("🚨 AUTHENTIFIZIERUNGSFEHLER!")
                print("=" * 70)
                print("Cookie oder __RequestVerificationToken ist abgelaufen.")
                print("Bitte aktualisiere config/trader_auth.json")
                print("=" * 70)
                sys.exit(1)
        
        # Process Wait List
        wait_items = results[0] if not isinstance(results[0], Exception) else []
        new_wait_keys = state.update_wait_list(wait_items)
        
        for key in new_wait_keys:
            item = state.wait_list_items[key]
            print("\n" + "=" * 70)
            print("🟡 NEUES PEARL ITEM wird registriert!")
            print("=" * 70)
            print(f"Name: {item.get('name', 'Unbekannt')}")
            print(f"Kategorie: {item.get('mainCategory')}-{item.get('subCategory')}")
            print(f"Item-ID: {item.get('mainKey')}")
            print(f"Preis: {item.get('pricePerOne', 'N/A')}")
            print(f"Status: Wartet auf Käufer")
            print("=" * 70)
        
        # Process Categories
        total_new = 0
        total_stock_changes = 0
        
        for i, result in enumerate(results[1:], 0):
            if isinstance(result, Exception):
                continue
            
            category, items = result
            cat_id = category["subCategory"]
            
            added, removed, stock_changes = state.update_category(cat_id, items)
            
            # New items in category
            for key in added:
                item_data = state.category_items[cat_id][key]
                sum_count = item_data.get('sumCount', 0)
                
                if sum_count > 0:
                    total_new += 1
                    print("\n" + "=" * 70)
                    print("🟢 PEARL ITEM VERFÜGBAR!")
                    print("=" * 70)
                    print(f"Kategorie: {category['name']}")
                    print(f"Name: {item_data.get('name', 'Unbekannt')}")
                    print(f"Verfügbarkeit: {sum_count}")
                    print(f"Item-ID: {item_data.get('mainKey')}")
                    print(f"Preis: {item_data.get('pricePerOne', 'N/A')}")
                    print("=" * 70)
            
            # Stock changes
            for key, (old_stock, new_stock) in stock_changes.items():
                if old_stock == 0 and new_stock > 0:
                    # Item became available
                    total_new += 1
                    item_data = state.category_items[cat_id][key]
                    print("\n" + "=" * 70)
                    print("🟢 PEARL ITEM WIEDER VERFÜGBAR!")
                    print("=" * 70)
                    print(f"Kategorie: {category['name']}")
                    print(f"Name: {item_data.get('name', 'Unbekannt')}")
                    print(f"Stock: {old_stock} → {new_stock}")
                    print(f"Item-ID: {item_data.get('mainKey')}")
                    print("=" * 70)
                elif new_stock > old_stock:
                    # More stock added
                    total_stock_changes += 1
        
        # Summary
        elapsed = time.time() - start_time
        
        if new_wait_keys:
            status = f"🟡 {len(new_wait_keys)} in Wait List"
        elif total_new > 0:
            status = f"🟢 {total_new} verfügbar"
        elif total_stock_changes > 0:
            status = f"📊 {total_stock_changes} Stock-Updates"
        else:
            status = "✓ keine Änderungen"
        
        print(f"[{timestamp}] Loop #{loop_count} | {elapsed:.2f}s | {status}")
        
        await asyncio.sleep(interval)


async def run_monitor(config_path: str, interval: float) -> None:
    """Main entry point for enhanced monitor."""
    print("Lade Authentifizierungsdaten...")
    auth = load_auth_config(config_path)
    
    headers = build_headers(auth["user_agent"], auth["cookie"])
    token = auth["request_verification_token"]
    
    limits = httpx.Limits(
        max_connections=16,
        max_keepalive_connections=16
    )
    timeout = httpx.Timeout(connect=8.0, read=8.0, write=8.0, pool=8.0)
    
    print(f"Starte Enhanced Monitor (Intervall: {interval}s, HTTP/2 + Keep-Alive)")
    print("Drücke STRG+C zum Beenden.\n")
    
    async with httpx.AsyncClient(
        http2=True,
        headers=headers,
        limits=limits,
        timeout=timeout
    ) as client:
        try:
            await monitor_loop_enhanced(client, token, interval)
        except KeyboardInterrupt:
            print("\n\nMonitor gestoppt.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BDO Pearl Monitor - ENHANCED (Wait List + Differential Detection)"
    )
    parser.add_argument(
        "--config",
        default=os.path.join("config", "trader_auth.json"),
        help="Pfad zur Auth-Konfigurationsdatei"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Abfrageintervall in Sekunden (Standard: 0.5)"
    )
    
    args = parser.parse_args()
    
    if args.interval < 0.05:
        print("WARNUNG: Intervall < 0.05s kann zu Rate-Limits führen!")
        args.interval = 0.05
    
    try:
        asyncio.run(run_monitor(args.config, args.interval))
    except KeyboardInterrupt:
        print("\nMonitor beendet.")
        sys.exit(0)


if __name__ == "__main__":
    main()

