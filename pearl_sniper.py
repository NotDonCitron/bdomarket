"""
Pearl Item Sniper - Speed-optimized monitoring tool for BDO Pearl Items.

Monitors the marketplace for Pearl Item listings and calculates extraction
profitability (Cron Stones + Valks' Cry) with NO TAX on extraction.

Features:
- 1-2 second detection speed
- Accurate profit calculations (NO marketplace tax)
- Multi-channel alerts (Terminal, Toast, Discord)
- Adaptive polling (1s during peak hours, 2s normal)
- 24/7 operation with error recovery

Usage:
    # Basic usage
    python pearl_sniper.py
    
    # Test mode with mock data
    python pearl_sniper.py --test
    
    # Dry run (no alerts)
    python pearl_sniper.py --dry-run
    
    # Custom config
    python pearl_sniper.py --config config/pearl_sniper.yaml
"""
import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import yaml

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

# Ensure Windows console uses UTF-8 to avoid emoji encoding errors
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from utils.market_client import MarketClient
from utils.pearl_calculator import PearlValueCalculator
from utils.smart_poller import SmartPoller
from utils.pearl_alerts import PearlAlerter
from utils.market_intelligence import MarketIntelligence

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class PearlSniper:
    """
    Main Pearl Item Sniper application.
    
    Monitors marketplace for pearl items and alerts on profitable opportunities.
    """
    
    def __init__(self, config: dict, test_mode: bool = False, dry_run: bool = False):
        """
        Initialize Pearl Sniper.
        
        Args:
            config: Configuration dict
            test_mode: Use mock data for testing
            dry_run: Run without sending alerts
        """
        self.config = config
        self.test_mode = test_mode
        self.dry_run = dry_run
        
        # Extract config
        sniper_config = config.get('pearl_sniper', {})
        region = config.get('region', 'eu')
        
        # Initialize components
        self.market_client = MarketClient(region=region)
        self.calculator = PearlValueCalculator(self.market_client)
        
        # Set thresholds
        alert_threshold = sniper_config.get('alert_threshold', {})
        self.calculator.set_thresholds(
            min_profit=alert_threshold.get('minimum_profit', 100_000_000),
            min_roi=alert_threshold.get('minimum_roi', 0.05)
        )
        
        # Poller setup
        prime_time_config = sniper_config.get('prime_time', {})
        self.poller = SmartPoller(
            base_interval=sniper_config.get('poll_interval', 2),
            peak_interval=1.0,
            activity_interval=1.5,
            peak_hours_enabled=sniper_config.get('peak_hours_boost', True),
            prime_time_enabled=prime_time_config.get('enabled', True)
        )
        
        # Alerter setup
        notifications = sniper_config.get('notifications', {})
        self.alerter = PearlAlerter(
            terminal_enabled=True,
            terminal_beep=notifications.get('terminal_beep', True),
            toast_enabled=notifications.get('windows_toast', True),
            webhook_url=notifications.get('discord_webhook')
        )
        
        # Runtime settings
        self.restart_on_error = sniper_config.get('restart_on_error', True)
        self.healthcheck_interval = sniper_config.get('healthcheck_interval', 300)
        
        # Market Intelligence (optional, config-controlled)
        intel_config = sniper_config.get('market_intelligence', {})
        if intel_config.get('enabled', False) and not test_mode:
            self.market_intel = MarketIntelligence(self.market_client)
            self.intel_update_interval = intel_config.get('update_interval', 300)
            self.intel_display_stats = intel_config.get('display_stats', True)
            self.last_intel_update = datetime.now()
        else:
            self.market_intel = None
        
        # Prime time notifications
        self.prime_notify = prime_time_config.get('notify_transitions', True)
        self.in_prime_time = False
        
        # State
        self.running = False
        self.last_healthcheck = datetime.now()
        self.items_checked = 0
        self.start_time = datetime.now()
        
        # Console
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
    
    async def start(self):
        """Start the sniper."""
        self.running = True
        self.start_time = datetime.now()
        
        self._print_banner()
        
        try:
            await self._run_monitoring_loop()
        except KeyboardInterrupt:
            self._print_info("\n⏹️  Stopped by user")
        except Exception as e:
            self._print_error(f"Fatal error: {e}")
            if self.restart_on_error:
                self._print_info("Restarting in 5 seconds...")
                await asyncio.sleep(5)
                await self.start()
        finally:
            self.market_client.close()
    
    async def _run_monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Update prices periodically
                await self._update_prices()
                
                # Update market intelligence periodically
                if self.market_intel:
                    await self._update_market_intelligence()
                
                # Check prime time transitions
                if self.prime_notify:
                    await self._check_prime_time_status()
                
                # Fetch pearl items
                pearl_items = await self._fetch_pearl_items()
                
                # Check each item
                for item in pearl_items:
                    self.items_checked += 1
                    await self._check_item(item)
                
                # Healthcheck
                await self._healthcheck()
                
                # Adaptive sleep
                interval = self.poller.get_interval()
                await asyncio.sleep(interval)
                
            except Exception as e:
                self._print_error(f"Loop error: {e}")
                await asyncio.sleep(5)  # Cooldown on error
    
    async def _update_prices(self):
        """Update Cron Stone and Valks' Cry prices."""
        # In test mode, use mock prices to avoid live API calls
        if self.test_mode:
            self.calculator.cron_price = 2_500_000  # 2.5M (marketplace, NPC=3M)
            self.calculator.valks_price = 20_000_000  # 20M (marketplace)
            self.calculator.last_price_update = datetime.now()
            
            # Log mock prices once
            if not hasattr(self, '_mock_prices_logged'):
                self._print_info(
                    f"📊 Mock Prices: Cron: {self._format_silver(self.calculator.cron_price)} | "
                    f"Valks: {self._format_silver(self.calculator.valks_price)}"
                )
                self._mock_prices_logged = True
            return
        
        # Normal mode - fetch real prices
        success = await self.calculator.update_prices()
        
        if success:
            price_info = self.calculator.get_price_info()
            cron = price_info['cron_price']
            valks = price_info['valks_price']
            
            # Log price update (first time or every 5 minutes)
            if not hasattr(self, '_last_price_log') or \
               (datetime.now() - self._last_price_log).total_seconds() > 300:
                self._print_info(
                    f"📊 Prices updated: Cron: {self._format_silver(cron)} | "
                    f"Valks: {self._format_silver(valks)}"
                )
                self._last_price_log = datetime.now()
    
    async def _fetch_pearl_items(self) -> List[Dict]:
        """
        Fetch pearl items from marketplace.
        
        Returns:
            List of pearl item dicts
        """
        if self.test_mode:
            return self._get_mock_items()
        
        try:
            # Get market list and filter for pearl items
            market_list = await self.market_client.get_market_list()
            
            # Pearl items typically have IDs in range 40000-49999
            # We'll filter based on category or ID range
            pearl_items = []
            for item in market_list:
                item_id = item.get('id', 0)
                
                # Pearl item ID range (approximate)
                if 40000 <= item_id < 50000:
                    # Only include items with stock (listed)
                    if item.get('stock', 0) > 0:
                        pearl_items.append(item)
            
            return pearl_items
            
        except Exception as e:
            self._print_error(f"Error fetching pearl items: {e}")
            return []
    
    async def _check_item(self, item: Dict):
        """
        Check if pearl item is profitable.
        
        Args:
            item: Pearl item dict from market API
        """
        try:
            item_id = item.get('id')
            item_name = item.get('name', f'Item_{item_id}')
            base_price = item.get('base_price', 0)
            
            if not base_price:
                return
            
            # Detect outfit type
            outfit_type = self.calculator.detect_outfit_type(item_name)
            
            # Calculate value
            result = self.calculator.calculate_value(outfit_type, base_price)
            
            if not result:
                return
            
            # Alert if profitable
            if result.is_profitable:
                self.poller.record_activity()  # Boost polling
                
                if not self.dry_run:
                    await self.alerter.send_alert(item, result)
                else:
                    self._print_info(f"[DRY RUN] Would alert for {item_name}")
                    
        except Exception as e:
            self._print_error(f"Error checking item {item.get('id')}: {e}")
    
    async def _update_market_intelligence(self):
        """Update market intelligence stats periodically."""
        now = datetime.now()
        elapsed = (now - self.last_intel_update).total_seconds()
        
        if elapsed >= self.intel_update_interval:
            success = await self.market_intel.update_statistics()
            if success:
                self.last_intel_update = now
    
    async def _check_prime_time_status(self):
        """Notify when entering/exiting prime time."""
        is_prime = self.poller._is_prime_time()
        
        if is_prime and not self.in_prime_time:
            self._print_info("🔥 PRIME TIME STARTED - Optimal listing window! Switching to 1s polling")
            self.in_prime_time = True
        elif not is_prime and self.in_prime_time:
            self._print_info("⏰ Prime time ended - Back to normal polling")
            self.in_prime_time = False
    
    def _display_market_intelligence(self):
        """Show market intelligence stats."""
        if not self.market_intel or not self.intel_display_stats:
            return
        
        popular = self.market_intel.get_popular_items(limit=5)
        if not popular:
            return
        
        self._print_info("📊 Popular Pearl Items (24h):")
        for item in popular:
            self._print_info(
                f"  • {item['name']}: {item['sales_count']} sales "
                f"(avg: {self._format_silver(item['avg_price'])})"
            )
    
    async def _healthcheck(self):
        """Periodic healthcheck and status update."""
        now = datetime.now()
        elapsed = (now - self.last_healthcheck).total_seconds()
        
        if elapsed >= self.healthcheck_interval:
            self.last_healthcheck = now
            
            # Get stats
            poller_stats = self.poller.get_stats()
            alerter_stats = self.alerter.get_stats()
            
            uptime = (now - self.start_time).total_seconds()
            uptime_str = self._format_uptime(uptime)
            
            # Print status
            status_parts = [
                f"Items checked: {self.items_checked}",
                f"Alerts: {alerter_stats['total_alerts']}",
                f"Uptime: {uptime_str}",
                f"Interval: {poller_stats['current_interval']:.1f}s"
            ]
            
            # Add prime time indicator
            if poller_stats['is_prime_time']:
                status_parts.append("🔥 PRIME TIME")
            elif poller_stats['is_peak_hours']:
                status_parts.append("⚡ Peak Hours")
            
            self._print_info(f"💎 Status: {' | '.join(status_parts)}")
            
            # Display market intelligence if enabled
            self._display_market_intelligence()
    
    def _get_mock_items(self) -> List[Dict]:
        """Get mock pearl items for testing."""
        return [
            {
                'id': 40001,
                'name': '[Kibelius] Outfit Set',
                'base_price': 1_350_000_000,
                'stock': 1
            },
            {
                'id': 40002,
                'name': '[Karlstein] Classic Outfit',
                'base_price': 1_800_000_000,
                'stock': 1
            },
            {
                'id': 40003,
                'name': 'Simple Desert Outfit',
                'base_price': 900_000_000,
                'stock': 1
            },
            {
                'id': 40004,
                'name': 'Dream Horse Gear Set',
                'base_price': 2_000_000_000,
                'stock': 1
            }
        ]
    
    def _print_banner(self):
        """Print startup banner."""
        region = self.config.get('region', 'EU').upper()
        interval = self.poller.base_interval
        
        if self.console:
            banner = f"""
[bold cyan]Pearl Sniper v1.0[/bold cyan]
[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]
Region: {region} | Base Interval: {interval}s
Peak Hours Boost: {'ON' if self.poller.peak_hours_enabled else 'OFF'}
Test Mode: {'ON' if self.test_mode else 'OFF'}
Dry Run: {'ON' if self.dry_run else 'OFF'}

💎 Monitoring marketplace for Pearl Items...
🔔 Alerts: Terminal{'+ Toast' if self.alerter.toast_enabled else ''}{'+ Discord' if self.alerter.webhook_url else ''}
[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]
"""
            self.console.print(banner)
        else:
            print(f"\nPearl Sniper v1.0 | Region: {region} | Polling: {interval}s")
            print("💎 Monitoring marketplace for Pearl Items...")
            print()
    
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
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dict
    """
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
        'pearl_sniper': {
            'enabled': True,
            'poll_interval': 2,
            'peak_hours_boost': True,
            'alert_threshold': {
                'minimum_profit': 100_000_000,
                'minimum_roi': 0.05
            },
            'notifications': {
                'terminal_beep': True,
                'windows_toast': True,
                'discord_webhook': None
            },
            'restart_on_error': True,
            'healthcheck_interval': 300
        }
    }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='BDO Pearl Item Sniper - Monitor marketplace for profitable pearl items'
    )
    parser.add_argument(
        '--config',
        default='config/pearl_sniper.yaml',
        help='Path to config file (default: config/pearl_sniper.yaml)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode with mock data'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no alerts sent)'
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Create and start sniper
    sniper = PearlSniper(
        config=config,
        test_mode=args.test,
        dry_run=args.dry_run
    )
    
    await sniper.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        sys.exit(0)

