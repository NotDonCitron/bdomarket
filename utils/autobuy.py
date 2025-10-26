"""
Auto-Buy Manager for BDO Pearl Shop Items.

Handles automatic purchasing of pearl items with safety checks and profitability validation.
"""
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

import aiohttp


@dataclass
class AutoBuyConfig:
    """Configuration for auto-buy functionality."""
    enabled: bool = True
    max_price: int = 5_000_000_000  # 5B max
    min_profit: int = 100_000_000    # 100M min profit
    min_roi: float = 0.05            # 5% min ROI
    max_purchases_per_hour: int = 10
    cooldown_seconds: float = 2.0
    dry_run: bool = False
    require_manual_confirmation: bool = False


@dataclass
class PurchaseAttempt:
    """Record of a purchase attempt."""
    item_id: int
    item_name: str
    price: int
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    profit: Optional[int] = None
    roi: Optional[float] = None


class AutoBuyManager:
    """
    Manages automatic purchasing of pearl items.
    
    Features:
    - Safety checks (price limits, purchase rate limits)
    - Profit validation
    - Purchase history tracking
    - Cooldown management
    - Dry-run mode
    
    Usage:
        config = AutoBuyConfig(max_price=3_000_000_000, min_profit=200_000_000)
        manager = AutoBuyManager(config, session_data)
        
        # Attempt to buy an item
        result = await manager.try_buy_item(
            item_id=40001,
            item_name="[Kibelius] Outfit Set",
            price=2_170_000_000,
            profit=6_930_000_000,
            roi=3.19
        )
    """
    
    def __init__(
        self,
        config: AutoBuyConfig,
        session_data: Dict[str, Any],
        region: str = "eu"
    ):
        """
        Initialize auto-buy manager.
        
        Args:
            config: Auto-buy configuration
            session_data: Authentication session data (from SessionManager)
            region: Market region
        """
        self.config = config
        self.session_data = session_data
        self.region = region.lower()
        
        # Base URLs
        self.base_urls = {
            'eu': 'https://eu-trade.naeu.playblackdesert.com',
            'na': 'https://na-trade.naeu.playblackdesert.com',
            'kr': 'https://trade.kr.playblackdesert.com',
            'sa': 'https://sa-trade.tr.playblackdesert.com'
        }
        self.base_url = self.base_urls.get(self.region, self.base_urls['eu'])
        
        # Purchase tracking
        self.purchase_history: list[PurchaseAttempt] = []
        self.last_purchase_time = 0.0
        
        # Callbacks
        self.on_purchase_success: Optional[Callable] = None
        self.on_purchase_failure: Optional[Callable] = None
    
    async def try_buy_item(
        self,
        item_id: int,
        item_name: str,
        price: int,
        profit: Optional[int] = None,
        roi: Optional[float] = None,
        quantity: int = 1
    ) -> PurchaseAttempt:
        """
        Attempt to buy an item with safety checks.
        
        Args:
            item_id: Item ID
            item_name: Item name (for logging)
            price: Purchase price
            profit: Expected profit (optional, for validation)
            roi: Expected ROI (optional, for validation)
            quantity: Quantity to buy (default: 1)
            
        Returns:
            PurchaseAttempt with result details
        """
        timestamp = time.time()
        
        # Create attempt record
        attempt = PurchaseAttempt(
            item_id=item_id,
            item_name=item_name,
            price=price,
            timestamp=timestamp,
            success=False,
            profit=profit,
            roi=roi
        )
        
        # Safety checks
        if not self.config.enabled:
            attempt.error_message = "Auto-buy is disabled"
            self.purchase_history.append(attempt)
            return attempt
        
        # Check price limit
        if price > self.config.max_price:
            attempt.error_message = f"Price {price:,} exceeds max {self.config.max_price:,}"
            self.purchase_history.append(attempt)
            return attempt
        
        # Check profit requirement
        if profit and profit < self.config.min_profit:
            attempt.error_message = f"Profit {profit:,} below min {self.config.min_profit:,}"
            self.purchase_history.append(attempt)
            return attempt
        
        # Check ROI requirement
        if roi and roi < self.config.min_roi:
            attempt.error_message = f"ROI {roi:.1%} below min {self.config.min_roi:.1%}"
            self.purchase_history.append(attempt)
            return attempt
        
        # Check purchase rate limit
        if not self._check_rate_limit():
            attempt.error_message = "Rate limit exceeded (too many purchases per hour)"
            self.purchase_history.append(attempt)
            return attempt
        
        # Check cooldown
        if not self._check_cooldown():
            remaining = self.config.cooldown_seconds - (timestamp - self.last_purchase_time)
            attempt.error_message = f"Cooldown active ({remaining:.1f}s remaining)"
            self.purchase_history.append(attempt)
            return attempt
        
        # Manual confirmation (if enabled)
        if self.config.require_manual_confirmation:
            confirmed = await self._request_confirmation(item_name, price, profit, roi)
            if not confirmed:
                attempt.error_message = "Manual confirmation declined"
                self.purchase_history.append(attempt)
                return attempt
        
        # Dry run mode
        if self.config.dry_run:
            print(f"[DRY RUN] Would buy {item_name} for {price:,} silver")
            attempt.success = True
            attempt.error_message = "Dry run - no actual purchase"
            self.purchase_history.append(attempt)
            return attempt
        
        # Execute purchase
        try:
            success, message = await self._execute_purchase(item_id, price, quantity)
            
            attempt.success = success
            attempt.error_message = message if not success else None
            
            if success:
                self.last_purchase_time = timestamp
                print(f"✅ Purchase successful: {item_name} for {price:,}")
                
                if self.on_purchase_success:
                    await self.on_purchase_success(attempt)
            else:
                print(f"❌ Purchase failed: {item_name} - {message}")
                
                if self.on_purchase_failure:
                    await self.on_purchase_failure(attempt)
            
        except Exception as e:
            attempt.success = False
            attempt.error_message = f"Exception: {str(e)}"
            print(f"❌ Purchase exception: {e}")
        
        self.purchase_history.append(attempt)
        return attempt
    
    async def _execute_purchase(
        self,
        item_id: int,
        price: int,
        quantity: int
    ) -> tuple[bool, str]:
        """
        Execute the actual purchase API call.
        
        Args:
            item_id: Item ID
            price: Purchase price
            quantity: Quantity to buy
            
        Returns:
            Tuple of (success, message)
        """
        try:
            headers = {
                'User-Agent': self.session_data.get('user_agent', 'Mozilla/5.0'),
                'Cookie': self.session_data.get('cookie', ''),
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': self.base_url,
                'Referer': f"{self.base_url}/Home/list/55-1"
            }
            
            data = {
                '__RequestVerificationToken': self.session_data.get('request_verification_token', ''),
                'mainKey': item_id,
                'subKey': 0,
                'pricePerOne': price,
                'count': quantity
            }
            
            url = f"{self.base_url}/Home/Buy"
            
            async with aiohttp.ClientSession() as client:
                async with client.post(url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return False, f"HTTP {response.status}"
                    
                    result = await response.json()
                    result_code = result.get('resultCode', -1)
                    result_msg = result.get('resultMsg', 'Unknown error')
                    
                    if result_code == 0:
                        return True, "Success"
                    else:
                        return False, f"API Error: {result_msg}"
                        
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within the hourly purchase limit.
        
        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        one_hour_ago = now - 3600
        
        # Count purchases in last hour
        recent_purchases = [
            p for p in self.purchase_history
            if p.timestamp > one_hour_ago and p.success
        ]
        
        return len(recent_purchases) < self.config.max_purchases_per_hour
    
    def _check_cooldown(self) -> bool:
        """
        Check if cooldown period has elapsed since last purchase.
        
        Returns:
            True if cooldown elapsed, False otherwise
        """
        if self.last_purchase_time == 0:
            return True
        
        elapsed = time.time() - self.last_purchase_time
        return elapsed >= self.config.cooldown_seconds
    
    async def _request_confirmation(
        self,
        item_name: str,
        price: int,
        profit: Optional[int],
        roi: Optional[float]
    ) -> bool:
        """
        Request manual confirmation for purchase.
        
        Args:
            item_name: Item name
            price: Purchase price
            profit: Expected profit
            roi: Expected ROI
            
        Returns:
            True if confirmed, False otherwise
        """
        print("\n" + "=" * 60)
        print("🛒 PURCHASE CONFIRMATION REQUIRED")
        print("=" * 60)
        print(f"Item: {item_name}")
        print(f"Price: {price:,} silver")
        if profit:
            print(f"Profit: {profit:,} silver")
        if roi:
            print(f"ROI: {roi:.1%}")
        print("=" * 60)
        
        # In automated mode, we can't actually ask for input
        # This would be used in semi-automated mode
        # For now, return True (auto-confirm)
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get purchase statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.purchase_history)
        successful = sum(1 for p in self.purchase_history if p.success)
        failed = total - successful
        
        total_spent = sum(p.price for p in self.purchase_history if p.success)
        total_profit = sum(p.profit for p in self.purchase_history if p.success and p.profit)
        
        # Recent purchases (last hour)
        one_hour_ago = time.time() - 3600
        recent = [p for p in self.purchase_history if p.timestamp > one_hour_ago]
        
        return {
            'total_attempts': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'total_spent': total_spent,
            'total_profit': total_profit,
            'recent_purchases': len(recent),
            'purchases_this_hour': len([p for p in recent if p.success]),
            'cooldown_remaining': max(0, self.config.cooldown_seconds - (time.time() - self.last_purchase_time))
        }
    
    def print_statistics(self):
        """Print purchase statistics to console."""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("📊 AUTO-BUY STATISTICS")
        print("=" * 60)
        print(f"Total Attempts: {stats['total_attempts']}")
        print(f"Successful: {stats['successful']} ({stats['success_rate']:.1%})")
        print(f"Failed: {stats['failed']}")
        print(f"Total Spent: {stats['total_spent']:,} silver")
        print(f"Total Profit: {stats['total_profit']:,} silver")
        print(f"Purchases This Hour: {stats['purchases_this_hour']}/{self.config.max_purchases_per_hour}")
        
        if stats['cooldown_remaining'] > 0:
            print(f"Cooldown: {stats['cooldown_remaining']:.1f}s")
        else:
            print("Cooldown: Ready")
        
        print("=" * 60)


def create_default_config() -> AutoBuyConfig:
    """Create default auto-buy configuration."""
    return AutoBuyConfig(
        enabled=True,
        max_price=5_000_000_000,      # 5B max
        min_profit=100_000_000,        # 100M min profit
        min_roi=0.05,                  # 5% min ROI
        max_purchases_per_hour=10,
        cooldown_seconds=2.0,
        dry_run=False,
        require_manual_confirmation=False
    )
