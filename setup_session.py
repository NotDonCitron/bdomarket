"""
Interactive Session Setup Tool for BDO Pearl Auto-Buy.

This script helps you set up authentication by opening a browser
and extracting the session after you login via Steam.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.session_manager import SessionManager

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed!")
    print("Install with: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)


async def setup_session_interactive(region: str = 'eu'):
    """
    Interactive session setup using browser.
    
    Opens a browser, waits for user to login, then extracts session.
    """
    print("=" * 70)
    print("🔐 BDO PEARL AUTO-BUY - SESSION SETUP")
    print("=" * 70)
    print()
    print("This tool will:")
    print("  1. Open a browser")
    print("  2. Navigate to BDO marketplace")
    print("  3. Wait for you to login via Steam")
    print("  4. Extract and save your session")
    print()
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        # Launch browser
        print("Opening browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        # Navigate to marketplace
        region_urls = {
            'eu': 'https://eu-trade.naeu.playblackdesert.com/',
            'na': 'https://na-trade.naeu.playblackdesert.com/',
            'kr': 'https://trade.kr.playblackdesert.com/',
            'sa': 'https://sa-trade.tr.playblackdesert.com/'
        }
        
        url = region_urls.get(region.lower(), region_urls['eu'])
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until='domcontentloaded')
        
        print()
        print("=" * 70)
        print("⚠️  ACTION REQUIRED")
        print("=" * 70)
        print("1. Login via Steam in the browser")
        print("2. Wait until you're fully logged in")
        print("3. Navigate to any pearl category to verify login")
        print("4. Press ENTER in this terminal when ready")
        print("=" * 70)
        print()
        
        input("Press ENTER when you've logged in: ")
        
        # Extract session
        print("\nExtracting session data...")
        session_manager = SessionManager(region=region)
        session = await session_manager.extract_session_from_browser(page)
        
        if session:
            print("✅ Session extracted successfully!")
            print(f"   Session file: {session_manager.session_file}")
            print()
            print("You can now run the auto-buy system:")
            print("  python pearl_autobuy.py")
            print()
            print("Or test in dry-run mode:")
            print("  python pearl_autobuy.py --dry-run")
        else:
            print("❌ Failed to extract session")
            print("Please make sure you're logged in and try again")
        
        await browser.close()


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup authentication session for BDO Pearl Auto-Buy"
    )
    parser.add_argument(
        '--region',
        default='eu',
        choices=['eu', 'na', 'kr', 'sa'],
        help='Market region'
    )
    
    args = parser.parse_args()
    
    asyncio.run(setup_session_interactive(args.region))


if __name__ == "__main__":
    main()
