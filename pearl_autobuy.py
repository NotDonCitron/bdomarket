"""
BDO Pearl Shop Auto-Buy System

Real-time monitoring and automatic purchasing of profitable Pearl Shop items.

Features:
- Real-time pearl item detection (100ms polling with HTTP/2)
- Automatic profit calculation and validation
- Automatic purchasing with safety checks
- Persistent session management (no manual re-login)
- Comprehensive logging and statistics

Usage:
    python pearl_autobuy.py
    python pearl_autobuy.py --dry-run  # Test without buying
    python pearl_autobuy.py --config config/autobuy.yaml
"""
import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import yaml

sys.path.insert(0, str(Path(__file__).parent))

# Ensure Windows console uses UTF-8
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from utils.session_manager import SessionManager, SessionData
from utils.pearl_detector import PearlDetector, DetectionEvent
from utils.autobuy import AutoBuyManager, AutoBuyConfig
from utils.pearl_calculator import PearlValueCalculator
from utils.market_client import MarketClient
from utils.pearl_alerts import PearlAlerter

try:
    from rich.console import Console
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class PearlAutoBuy:
    """
    Main Pearl Auto-Buy application.
    
    Coordinates detection, profit calculation, and automatic purchasing.
    """
    
    def __init__(
        self,
        config: dict,
        dry_run: bool = False,
        manual_login: bool = False
    ):
        """
        Initialize Pearl Auto-Buy system.
        
        Args:
            config: Configuration dict
            dry_run: If True, don't actually make purchases
            manual_login: If True, use browser for manual login
        """
        self.config = config
        self.dry_run = dry_run
        self.manual_login = manual_login
        
        # Extract config
        autobuy_config = config.get('pearl_autobuy', {})
        region = config.get('region', 'eu')
        self.region = region.lower()
        
        self.base_urls = {
            'eu': 'https://eu-trade.naeu.playblackdesert.com',
            'na': 'https://na-trade.naeu.playblackdesert.com',
            'kr': 'https://trade.kr.playblackdesert.com',
            'sa': 'https://sa-trade.tr.playblackdesert.com'
        }
        self.base_url = self.base_urls.get(self.region, self.base_urls['eu'])
        
        # Session manager
        self.session_manager = SessionManager(region=self.region)
        self.session: Optional[SessionData] = None
        
        # Market client for price lookups
        self.market_client = MarketClient(region=self.region)
        self.calculator = PearlValueCalculator(self.market_client)
        
        # Set profit thresholds
        threshold_config = autobuy_config.get('alert_threshold', {})
        self.calculator.set_thresholds(
            min_profit=threshold_config.get('minimum_profit', 100_000_000),
            min_roi=threshold_config.get('minimum_roi', 0.05)
        )
        
        # Auto-buy config
        buy_config = autobuy_config.get('auto_buy', {})
        self.autobuy_config = AutoBuyConfig(
            enabled=buy_config.get('enabled', True) and not dry_run,
            max_price=buy_config.get('max_price', 5_000_000_000),
            min_profit=threshold_config.get('minimum_profit', 100_000_000),
            min_roi=threshold_config.get('minimum_roi', 0.05),
            max_purchases_per_hour=buy_config.get('max_purchases_per_hour', 10),
            cooldown_seconds=buy_config.get('cooldown_seconds', 2.0),
            dry_run=dry_run,
            require_manual_confirmation=buy_config.get('require_confirmation', False)
        )
        
        # Auto-buy manager (initialized after session)
        self.autobuy_manager: Optional[AutoBuyManager] = None
        
        # Detector (initialized after session)
        self.detector: Optional[PearlDetector] = None
        
        # Alerter
        notifications = autobuy_config.get('notifications', {})
        self.alerter = PearlAlerter(
            terminal_enabled=True,
            terminal_beep=notifications.get('terminal_beep', True),
            toast_enabled=notifications.get('windows_toast', True),
            webhook_url=notifications.get('discord_webhook')
        )
        
        # Detection config
        detection_config = autobuy_config.get('detection', {})
        self.poll_interval = detection_config.get('poll_interval', 0.1)
        
        # Statistics
        self.items_detected = 0
        self.items_purchased = 0
        self.items_skipped = 0
        self.start_time = datetime.now()
        
        # Console
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
    
    async def start(self):
        """Start the auto-buy system."""
        self._print_banner()
        
        try:
            # Step 1: Initialize session
            if not await self._initialize_session():
                self._print_error("Failed to initialize session")
                return
            
            # Step 2: Update prices
            await self._update_prices()
            
            # Step 3: Initialize auto-buy manager
            self._initialize_autobuy()
            
            # Step 4: Initialize detector
            self._initialize_detector()
            
            # Step 5: Start detection loop
            await self._run_detection_loop()
            
        except KeyboardInterrupt:
            self._print_info("\n⏹️  Stopped by user")
        except Exception as e:
            self._print_error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self._cleanup()
    
    async def _initialize_session(self) -> bool:
        """Initialize authentication session."""
        self._print_info("Initializing session...")
        
        if self.manual_login:
            self._print_info("Manual login mode - launching browser...")
            try:
                from setup_session import setup_session_interactive
            except ImportError as e:
                self._print_error("Playwright not installed. Run: pip install playwright && playwright install chromium")
                self._print_error(str(e))
                return False
            
            try:
                await setup_session_interactive(self.region)
            except KeyboardInterrupt:
                self._print_error("Manual login aborted by user")
                return False
            except Exception as e:
                self._print_error(f"Manual login failed: {e}")
                return False
        
        # Try to load existing session (either from manual login or stored file)
        self.session = await self.session_manager.load_session()
        
        if self.session:
            age_hours = (datetime.now().timestamp() - self.session.created_at) / 3600
            self._print_info(f"✅ Session loaded (age: {age_hours:.1f}h)")
            return True
        else:
            self._print_error("❌ No valid session found")
            self._print_info("\nTo create a session:")
            self._print_info("1. Open BDO marketplace in browser: https://eu-trade.naeu.playblackdesert.com/")
            self._print_info("2. Login via Steam")
            self._print_info("3. Open DevTools (F12) -> Application -> Cookies")
            self._print_info("4. Copy the cookie string and create config/session.json manually")
            self._print_info("   Or run: python setup_session.py")
            return False
    
    async def _update_prices(self):
        """Update Cron Stone and Valks' Cry prices."""
        self._print_info("Updating material prices...")
        
        success = await self.calculator.update_prices()
        
        if success:
            price_info = self.calculator.get_price_info()
            cron = price_info['cron_price']
            valks = price_info['valks_price']
            
            self._print_info(
                f"📊 Prices: Cron: {self._format_silver(cron)} | "
                f"Valks: {self._format_silver(valks)}"
            )
        else:
            # Use default prices
            self.calculator.cron_price = 3_000_000
            self.calculator.valks_price = 18_000_000
            self._print_info("⚠️  Using default prices (Cron: 3M, Valks: 18M)")
    
    def _initialize_autobuy(self):
        """Initialize the auto-buy manager."""
        session_dict = {
            'cookie': self.session.cookie,
            'user_agent': self.session.user_agent,
            'request_verification_token': self.session.request_verification_token,
            'user_no': self.session.user_no
        }
        
        self.autobuy_manager = AutoBuyManager(
            self.autobuy_config,
            session_dict,
            region=self.config.get('region', 'eu')
        )
        
        # Set callbacks
        self.autobuy_manager.on_purchase_success = self._on_purchase_success
        self.autobuy_manager.on_purchase_failure = self._on_purchase_failure
    
    def _initialize_detector(self):
        """Initialize the pearl detector."""
        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'user-agent': self.session.user_agent,
            'cookie': self.session.cookie,
            'x-requested-with': 'XMLHttpRequest',
                        'origin': self.base_url,
            'referer': f"{self.base_url}/Home/list/55-1",
        }
        
        self.detector = PearlDetector(
            headers=headers,
            token=self.session.request_verification_token,
            interval=self.poll_interval,
            region=self.region
        )
        
        # Set event handlers
        self.detector.on_event = self._on_item_detected
        self.detector.on_error = self._on_detector_error
    
    async def _run_detection_loop(self):
        """Run the detection loop."""
        self._print_info("🚀 Starting detection loop...")
        self._print_info(f"Polling interval: {self.poll_interval}s ({1/self.poll_interval:.1f} checks/sec)")
        
        if self.dry_run:
            self._print_info("⚠️  DRY RUN MODE - No actual purchases will be made")
        
        # Start detector
        await self.detector.start()
    
    async def _on_item_detected(self, event: DetectionEvent):
        """Handle detected pearl item."""
        self.items_detected += 1
        
        item = event.item
        item_name = item.get('name', 'Unknown Item')
        item_id = item.get('mainKey')
        base_price = event.price or item.get('pricePerOne', 0)
        
        # Detect outfit type
        outfit_type = self.calculator.detect_outfit_type(item_name)
        
        # Calculate profit
        result = self.calculator.calculate_value(outfit_type, base_price)
        
        if not result:
            return
        
        # Check if profitable
        if not result.is_profitable:
            self.items_skipped += 1
            return
        
        # Alert
        self._print_info("=" * 70)
        self._print_info(f"🔥 PROFITABLE PEARL ITEM DETECTED!")
        self._print_info(event.format_summary())
        self._print_info(f"Extraction Value: {self._format_silver(result.extraction_value)}")
        self._print_info(f"Profit: {self._format_silver(result.profit)} ({result.roi:.1%} ROI)")
        self._print_info("=" * 70)
        
        # Send alert through normal channels
        await self.alerter.send_alert(item, result)
        
        # Attempt auto-buy
        if self.autobuy_manager:
            attempt = await self.autobuy_manager.try_buy_item(
                item_id=item_id,
                item_name=item_name,
                price=base_price,
                profit=result.profit,
                roi=result.roi
            )
            
            if attempt.error_message:
                self._print_info(f"⚠️  {attempt.error_message}")
    
    async def _on_purchase_success(self, attempt):
        """Handle successful purchase."""
        self.items_purchased += 1
    
    async def _on_purchase_failure(self, attempt):
        """Handle failed purchase."""
        pass
    
    async def _on_detector_error(self, error: Exception):
        """Handle detector errors."""
        import httpx
        if isinstance(error, httpx.HTTPStatusError) and error.response.status_code in (401, 403):
            self._print_error("🚨 AUTHENTICATION ERROR!")
            self._print_error("Session expired or invalid. Please refresh your session.")
            sys.exit(1)
        else:
            self._print_error(f"Detector error: {error}")
    
    async def _cleanup(self):
        """Clean up resources."""
        if self.detector:
            await self.detector.close()
        if self.market_client:
            self.market_client.close()
        
        # Print final statistics
        self._print_statistics()
    
    def _print_statistics(self):
        """Print final statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"Runtime: {self._format_uptime(elapsed)}")
        print(f"Items Detected: {self.items_detected}")
        print(f"Items Purchased: {self.items_purchased}")
        print(f"Items Skipped: {self.items_skipped}")
        
        if self.detector:
            stats = self.detector.get_statistics()
            print(f"Total Loops: {stats['total_loops']}")
            print(f"Total API Calls: {stats['total_requests']}")
            print(f"Loops/Second: {stats['loops_per_second']:.2f}")
        
        if self.autobuy_manager:
            buy_stats = self.autobuy_manager.get_statistics()
            print(f"\nPurchase Attempts: {buy_stats['total_attempts']}")
            print(f"Success Rate: {buy_stats['success_rate']:.1%}")
            print(f"Total Spent: {buy_stats['total_spent']:,} silver")
            print(f"Total Profit: {buy_stats['total_profit']:,} silver")
        
        print("=" * 70)
    
    def _print_banner(self):
        """Print startup banner."""
        region = self.config.get('region', 'EU').upper()
        
        if self.console:
            banner = f"""
[bold cyan]Pearl Auto-Buy v1.0[/bold cyan]
[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]
Region: {region}
Polling: {self.poll_interval}s ({1/self.poll_interval:.1f} checks/sec)
Dry Run: {'ON' if self.dry_run else 'OFF'}

💎 Real-time monitoring & automatic purchasing
🔥 Detection speed: ~{self.poll_interval*1000:.0f}ms
🛒 Auto-buy: {'ENABLED' if self.autobuy_config.enabled else 'DISABLED'}
[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]
"""
            self.console.print(banner)
        else:
            print(f"\n{'='*70}")
            print("Pearl Auto-Buy v1.0")
            print(f"{'='*70}")
            print(f"Region: {region}")
            print(f"Polling: {self.poll_interval}s ({1/self.poll_interval:.1f} checks/sec)")
            print(f"Dry Run: {'ON' if self.dry_run else 'OFF'}")
            print(f"Auto-buy: {'ENABLED' if self.autobuy_config.enabled else 'DISABLED'}")
            print(f"{'='*70}\n")
    
    def _print_info(self, message: str):
        """Print info message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.console:
            self.console.print(f"[dim][{timestamp}][/dim] {message}")
        else:
            print(f"[{timestamp}] {message}")
    
    def _print_error(self, message: str):
        """Print error message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.console:
            self.console.print(f"[dim][{timestamp}][/dim] [red]❌ {message}[/red]")
        else:
            print(f"[{timestamp}] ERROR: {message}")
    
    def _format_silver(self, amount: int) -> str:
        """Format silver amount."""
        if amount >= 1_000_000_000:
            return f"{amount / 1_000_000_000:.2f}B"
        elif amount >= 1_000_000:
            return f"{amount / 1_000_000:.0f}M"
        else:
            return f"{amount:,}"
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("Using default configuration...")
        return get_default_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return get_default_config()


def get_default_config() -> dict:
    """Get default configuration."""
    return {
        'region': 'eu',
        'pearl_autobuy': {
            'enabled': True,
            'detection': {
                'poll_interval': 0.1  # 100ms = 10 checks/sec
            },
            'alert_threshold': {
                'minimum_profit': 100_000_000,  # 100M
                'minimum_roi': 0.05             # 5%
            },
            'auto_buy': {
                'enabled': True,
                'max_price': 5_000_000_000,
                'max_purchases_per_hour': 10,
                'cooldown_seconds': 2.0,
                'require_confirmation': False
            },
            'notifications': {
                'terminal_beep': True,
                'windows_toast': True,
                'discord_webhook': None
            }
        }
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="BDO Pearl Shop Auto-Buy System"
    )
    parser.add_argument(
        '--config',
        default='config/pearl_autobuy.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making actual purchases'
    )
    parser.add_argument(
        '--manual-login',
        action='store_true',
        help='Use browser for manual login'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Create and start application
    app = PearlAutoBuy(
        config=config,
        dry_run=args.dry_run,
        manual_login=args.manual_login
    )
    
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
