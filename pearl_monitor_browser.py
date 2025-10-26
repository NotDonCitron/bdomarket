"""
BDO Pearl Monitor - Browser-based Live Detection
Uses Playwright to keep all Pearl category pages open and monitors DOM changes in real-time.
"""
import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Pearl categories to monitor
PEARL_CATEGORIES = [
    {"id": "55-1", "name": "Männliche Outfits (Set)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-1"},
    {"id": "55-2", "name": "Weibliche Outfits (Set)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-2"},
    {"id": "55-3", "name": "Männliche Outfits (Einzel)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-3"},
    {"id": "55-4", "name": "Weibliche Outfits (Einzel)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-4"},
    {"id": "55-5", "name": "Klassen-Outfits (Set)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-5"},
    {"id": "55-6", "name": "Funktional (Tiere, Elixiere etc.)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-6"},
    {"id": "55-7", "name": "Reittiere (Pferdeausrüstung)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-7"},
    {"id": "55-8", "name": "Begleiter (Pets)", "url": "https://eu-trade.naeu.playblackdesert.com/Home/list/55-8"},
]


def load_auth_config(config_path: str = "config/trader_auth.json") -> Dict[str, str]:
    """Load authentication config from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    required = ["cookie", "user_agent"]
    for key in required:
        if not data.get(key):
            raise ValueError(f"Missing '{key}' in {config_path}")
    
    return data


def parse_cookie_string(cookie_str: str) -> List[Dict[str, Any]]:
    """Convert cookie string to Playwright cookie format."""
    cookies = []
    for item in cookie_str.split("; "):
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({
                "name": name,
                "value": value,
                "domain": ".playblackdesert.com",
                "path": "/"
            })
    return cookies


async def setup_page_monitor(page: Page, category: Dict[str, str]) -> None:
    """
    Setup DOM mutation observer on a Pearl category page.
    This JavaScript runs in the browser and detects when items appear/change.
    """
    
    observer_script = """
    (category_name) => {
        // Track seen items to avoid duplicate alerts
        window.__seenItems = window.__seenItems || new Set();
        window.__lastItemCount = window.__lastItemCount || 0;
        
        // Function to check for items with stock
        function checkItems() {
            const items = document.querySelectorAll('.item_list_wrapper .item_list');
            let foundNew = false;
            let currentCount = 0;
            
            items.forEach(itemEl => {
                const nameEl = itemEl.querySelector('.item_name');
                const stockEl = itemEl.querySelector('.item_stock, .item_count');
                
                if (nameEl && stockEl) {
                    const name = nameEl.textContent.trim();
                    const stockText = stockEl.textContent.trim();
                    const stock = parseInt(stockText.replace(/[^0-9]/g, '')) || 0;
                    
                    if (stock > 0) {
                        currentCount++;
                        const itemKey = `${name}_${stock}`;
                        
                        if (!window.__seenItems.has(name)) {
                            window.__seenItems.add(name);
                            foundNew = true;
                            
                            // Create alert element
                            const alert = document.createElement('div');
                            alert.style.cssText = `
                                position: fixed;
                                top: 20px;
                                right: 20px;
                                background: #ff4444;
                                color: white;
                                padding: 20px;
                                border-radius: 8px;
                                font-size: 16px;
                                font-weight: bold;
                                z-index: 99999;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                                animation: slideIn 0.3s ease-out;
                            `;
                            alert.innerHTML = `
                                <div style="font-size: 24px; margin-bottom: 10px;">🚨 PEARL ITEM GEFUNDEN!</div>
                                <div><strong>${name}</strong></div>
                                <div>Verfügbar: ${stock}</div>
                                <div style="margin-top: 10px; font-size: 12px;">Kategorie: ${category_name}</div>
                            `;
                            document.body.appendChild(alert);
                            
                            // Remove after 10 seconds
                            setTimeout(() => alert.remove(), 10000);
                            
                            // Log to console
                            console.log('🚨🚨🚨 PEARL ITEM FOUND 🚨🚨🚨');
                            console.log('Category:', category_name);
                            console.log('Name:', name);
                            console.log('Stock:', stock);
                            console.log('Time:', new Date().toLocaleTimeString());
                        }
                    }
                }
            });
            
            // Detect if item count changed
            if (currentCount !== window.__lastItemCount) {
                console.log(`[${category_name}] Items with stock: ${currentCount} (was: ${window.__lastItemCount})`);
                window.__lastItemCount = currentCount;
            }
            
            return foundNew;
        }
        
        // Initial check
        checkItems();
        
        // Setup MutationObserver for DOM changes
        const observer = new MutationObserver((mutations) => {
            let shouldCheck = false;
            
            for (const mutation of mutations) {
                if (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0) {
                    shouldCheck = true;
                    break;
                }
            }
            
            if (shouldCheck) {
                console.log(`[${category_name}] DOM changed, checking items...`);
                checkItems();
            }
        });
        
        // Observe the main container
        const container = document.querySelector('.item_list_wrapper, #itemListArea, .market_list');
        if (container) {
            observer.observe(container, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class', 'style']
            });
            console.log(`[${category_name}] ✅ MutationObserver active`);
        } else {
            console.warn(`[${category_name}] ⚠️  Container not found, will retry...`);
            // Retry after page loads
            setTimeout(() => {
                const retryContainer = document.querySelector('.item_list_wrapper, #itemListArea, .market_list');
                if (retryContainer) {
                    observer.observe(retryContainer, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['class', 'style']
                    });
                    console.log(`[${category_name}] ✅ MutationObserver active (retry)`);
                }
            }, 2000);
        }
        
        // Also poll every 5 seconds as backup
        setInterval(() => {
            checkItems();
        }, 5000);
        
        // Mark as initialized
        window.__monitorInitialized = true;
        console.log(`[${category_name}] 🔍 Live monitoring started`);
    }
    """
    
    await page.evaluate(observer_script, category["name"])


async def setup_browser_monitoring(
    context: BrowserContext,
    categories: List[Dict[str, str]]
) -> List[Page]:
    """
    Open all Pearl category pages and setup monitoring on each.
    
    Returns:
        List of Page objects
    """
    pages = []
    
    for i, category in enumerate(categories):
        print(f"Opening {category['name']}...")
        
        # Create new page
        page = await context.new_page()
        
        # Navigate to category
        await page.goto(category["url"], wait_until="networkidle", timeout=30000)
        
        # Wait for page to load
        await asyncio.sleep(2)
        
        # Setup mutation observer
        await setup_page_monitor(page, category)
        
        # Listen to console messages from the page
        page.on("console", lambda msg, cat=category: 
            print(f"[{cat['name']}] {msg.text()}") if "PEARL" in msg.text() or "Items with stock" in msg.text() else None
        )
        
        pages.append(page)
        
        print(f"  ✅ {category['name']} monitoring active")
    
    return pages


async def run_browser_monitor(config_path: str = "config/trader_auth.json", headless: bool = False, manual_login: bool = False) -> None:
    """
    Main entry point for browser-based monitoring.
    
    Args:
        config_path: Path to auth config file (nur für manual_login=False)
        headless: Run browser in headless mode (True) or visible (False)
        manual_login: If True, öffnet Browser und wartet auf manuelle Steam-Login
    """
    print("=" * 70)
    print("🌐 BDO PEARL MONITOR - BROWSER MODE")
    print("=" * 70)
    print("Features:")
    print("  - Alle 8 Pearl-Kategorien als Tabs offen")
    print("  - Live DOM-Änderungs-Erkennung (MutationObserver)")
    print("  - Backup: 5s Polling pro Tab")
    print("  - Sofortige Alerts bei neuen Items")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        # Launch browser
        print("Starte Browser...")
        browser = await p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Create context
        if manual_login:
            # Manual login mode - kein Cookie, User muss einloggen
            print("\n" + "=" * 70)
            print("⚠️  MANUAL LOGIN MODE")
            print("=" * 70)
            print("1. Browser öffnet sich")
            print("2. Logge dich über Steam ein")
            print("3. Navigiere zu einer beliebigen Pearl-Kategorie")
            print("4. Drücke ENTER hier im Terminal wenn du eingeloggt bist")
            print("=" * 70)
            print()
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            
            # Open login page
            login_page = await context.new_page()
            await login_page.goto("https://eu-trade.naeu.playblackdesert.com/", wait_until="domcontentloaded")
            
            # Wait for user to login
            input("Drücke ENTER nachdem du eingeloggt bist: ")
            
            # Close login page
            await login_page.close()
            
        else:
            # Cookie-based auth
            auth = load_auth_config(config_path)
            cookies = parse_cookie_string(auth["cookie"])
            
            context = await browser.new_context(
                user_agent=auth["user_agent"],
                viewport={"width": 1280, "height": 720}
            )
            await context.add_cookies(cookies)
        
        # Setup monitoring on all pages
        pages = await setup_browser_monitoring(context, PEARL_CATEGORIES)
        
        print()
        print("=" * 70)
        print("✅ MONITORING AKTIV!")
        print("=" * 70)
        print(f"Tabs offen: {len(pages)}")
        print("Drücke STRG+C zum Beenden")
        print()
        print("Warte auf Pearl Items...")
        print("=" * 70)
        print()
        
        try:
            # Keep browser open and monitor
            while True:
                await asyncio.sleep(10)
                
                # Periodically log status
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 🔍 Monitoring läuft... ({len(pages)} Tabs aktiv)")
        
        except KeyboardInterrupt:
            print("\n\nMonitoring gestoppt.")
        
        finally:
            await browser.close()


async def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="BDO Pearl Monitor - Browser Mode (Live DOM Detection)"
    )
    parser.add_argument(
        "--config",
        default="config/trader_auth.json",
        help="Pfad zur Auth-Konfigurationsdatei"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Browser im Hintergrund laufen lassen (kein Fenster)"
    )
    parser.add_argument(
        "--manual-login",
        action="store_true",
        help="Browser öffnen und auf manuelle Steam-Login warten"
    )
    
    args = parser.parse_args()
    
    await run_browser_monitor(args.config, args.headless, args.manual_login)


if __name__ == "__main__":
    asyncio.run(main())

