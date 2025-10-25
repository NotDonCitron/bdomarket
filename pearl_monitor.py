#!/usr/bin/env python3
"""
Pearl Shop Monitor - Chrome MCP-based Web Traffic Monitor
Monitors Black Desert Online Pearl shop for new item listings and alerts on profitable opportunities.
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from utils.pearl_monitor import PearlShopMonitor
from utils.pearl_calculator import PearlItem

async def main():
    """Main entry point for Pearl shop monitor"""
    parser = argparse.ArgumentParser(description="Monitor BDO Pearl shop for new listings")
    parser.add_argument("--config", default="config/pearl_monitor.yaml", 
                       help="Path to configuration file")
    parser.add_argument("--test", action="store_true", 
                       help="Run in test mode with mock data")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without actual alerts")
    parser.add_argument("--headless", action="store_true", 
                       help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    print("🚀 Starting BDO Pearl Shop Monitor")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.test:
        print("🧪 Running in TEST mode")
        await run_test_mode()
        return
    
    try:
        # Initialize monitor
        monitor = PearlShopMonitor(args.config)
        
        # Override headless setting if command line arg provided
        if args.headless:
            monitor.config.set("pearl_monitor.headless", True)
        
        # Add custom alert callback for Discord/webhook (if configured)
        if not args.dry_run:
            monitor.add_alert_callback(lambda item: discord_webhook_alert(item, monitor.config))
        
        async with monitor:
            # Authenticate
            if not await monitor.authenticate():
                print("❌ Authentication failed. Exiting...")
                return
            
            # Start monitoring
            await monitor.start_monitoring()
            
    except KeyboardInterrupt:
        print("\n⏹️  Monitor stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

async def run_test_mode():
    """Run test mode with mock Pearl items"""
    from utils.pearl_calculator import PearlCalculator
    
    print("🧪 Testing Pearl extraction calculations...")
    
    test_items = [
        PearlItem("1", "Kibelius Outfit Set (PREMIUM)", "outfit", 1_350_000_000, datetime.now()),
        PearlItem("2", "Classic Outfit Set", "outfit", 980_000_000, datetime.now()),
        PearlItem("3", "Mount Gear Package", "mount", 1_200_000_000, datetime.now()),
    ]
    
    for item in test_items:
        calculated_item = PearlCalculator.calculate_profit_metrics(item)
        
        print(f"\n💎 {calculated_item.name}")
        print(f"   Listed: {calculated_item.price:,} Pearl")
        print(f"   Extraction: {calculated_item.extraction_value:,}")
        print(f"   Profit: {calculated_item.profit_margin:+,.0f} ({calculated_item.roi:+.1%} ROI)")
        
        if calculated_item.profit_margin > 100_000_000 and calculated_item.roi > 0.05:
            print("   ✅ PROFITABLE OPPORTUNITY!")
        else:
            print("   ❌ Not profitable enough")

async def discord_webhook_alert(item: PearlItem, config):
    """Send alert to Discord webhook if configured"""
    webhook_url = config.get("pearl_monitor.notifications.discord_webhook")
    
    if not webhook_url:
        return
    
    try:
        import aiohttp
        
        embed = {
            "title": "💎 PEARL SHOP ALERT",
            "description": f"**{item.name}**",
            "color": 0x00ff00,
            "fields": [
                {
                    "name": "🏷️ Listed Price",
                    "value": f"{item.price:,} Pearl",
                    "inline": True
                },
                {
                    "name": "⚡ Extraction Value",
                    "value": f"{item.extraction_value:,} Pearl",
                    "inline": True
                },
                {
                    "name": "💰 Profit",
                    "value": f"{item.profit_margin:+,.0f} ({item.roi:+.1%} ROI)",
                    "inline": True
                },
                {
                    "name": "⏰ Listed At",
                    "value": item.listed_time.strftime('%H:%M:%S'),
                    "inline": True
                }
            ],
            "footer": {
                "text": "BDO Pearl Shop Monitor"
            }
        }
        
        payload = {"embeds": [embed]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    print("📱 Discord alert sent successfully")
                else:
                    print(f"⚠️ Failed to send Discord alert: {response.status}")
                    
    except ImportError:
        print("⚠️ aiohttp not available for Discord notifications")
    except Exception as e:
        print(f"⚠️ Discord webhook error: {e}")

if __name__ == "__main__":
    asyncio.run(main())