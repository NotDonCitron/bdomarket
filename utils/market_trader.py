"""
Market Trader - Authenticated trading actions for BDO Central Market.

This module implements authenticated trading operations (buy, sell, cancel, collect)
by directly calling the BDO Central Market API, similar to kookehs/bdo-marketplace.

⚠️  IMPORTANT: Requires authentication credentials from market.blackdesertonline.com
"""
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json


@dataclass
class TradeCredentials:
    """Authentication credentials for Central Market API."""
    session_id: str  # Cookie: __RequestVerificationToken
    user_no: str     # Cookie: userNo
    region: str = 'eu'  # eu, na, kr, sa
    
    def to_cookies(self) -> Dict[str, str]:
        """Convert credentials to cookie dict."""
        cookies = {
            '__RequestVerificationToken': self.session_id
        }
        # TradeAuth_Session_EU is the actual session cookie (stored in user_no field)
        if self.user_no:
            cookies['TradeAuth_Session_EU'] = self.user_no
        return cookies


@dataclass
class TradeResult:
    """Result of a trading operation."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MarketTrader:
    """
    Authenticated trading client for BDO Central Market.
    
    Features:
    - Buy items from marketplace
    - Sell items to marketplace
    - Cancel pending listings
    - Collect silver from completed sales
    - View user inventory
    - View user bid listings
    
    Usage:
        creds = TradeCredentials(
            session_id="your_session_token",
            user_no="your_user_number",
            region='eu'
        )
        
        async with MarketTrader(creds) as trader:
            # Buy item
            result = await trader.buy_item(16001, price=180000, quantity=100)
            
            # Check inventory
            inventory = await trader.get_inventory()
    
    ⚠️  To get credentials:
        1. Log into https://market.blackdesertonline.com/ in browser
        2. Open DevTools (F12) -> Network tab
        3. Make any action (search, etc.)
        4. Check request cookies for '__RequestVerificationToken' and 'userNo'
    """
    
    BASE_URLS = {
        'eu': 'https://eu-trade.naeu.playblackdesert.com',
        'na': 'https://na-trade.naeu.playblackdesert.com',
        'kr': 'https://trade.kr.playblackdesert.com',
        'sa': 'https://sa-trade.tr.playblackdesert.com'
    }
    
    def __init__(self, credentials: TradeCredentials):
        """
        Initialize market trader.
        
        Args:
            credentials: Authentication credentials
        """
        self.credentials = credentials
        self.base_url = self.BASE_URLS.get(credentials.region.lower(), self.BASE_URLS['eu'])
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            },
            cookies=self.credentials.to_cookies()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the trader session."""
        if self.session:
            await self.session.close()
    
    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated POST request to API.
        
        Args:
            endpoint: API endpoint (e.g., '/Home/Buy')
            data: Request payload
            
        Returns:
            Response JSON
        """
        if not self.session:
            raise RuntimeError("Trader not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        # The API uses form-encoded data, not JSON
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        try:
            async with self.session.post(url, data=data, headers=headers) as response:
                if response.status != 200:
                    return {
                        'resultCode': -1,
                        'resultMsg': f'HTTP {response.status}: {await response.text()}'
                    }
                return await response.json()
        except Exception as e:
            return {
                'resultCode': -1,
                'resultMsg': f'Request failed: {str(e)}'
            }
    
    async def buy_item(
        self,
        item_id: int,
        sid: int = 0,
        price: int = 0,
        quantity: int = 1
    ) -> TradeResult:
        """
        Place buy order for an item.
        
        Args:
            item_id: Item ID
            sid: Sub-item ID (enhancement level, etc.)
            price: Buy price (0 = current lowest ask)
            quantity: Quantity to buy
            
        Returns:
            TradeResult indicating success/failure
            
        Example:
            >>> result = await trader.buy_item(16001, price=180000, quantity=100)
            >>> if result.success:
            >>>     print(f"Order placed: {result.message}")
        
        Note:
            - Requires sufficient silver in warehouse
            - Order enters 1-90 second registration queue
            - Not guaranteed to execute even if stock available
        """
        data = {
            '__RequestVerificationToken': self.credentials.session_id,
            'mainKey': item_id,
            'subKey': sid,
            'pricePerOne': price,
            'count': quantity
        }
        
        response = await self._post('/Home/Buy', data)
        
        success = response.get('resultCode') == 0
        message = response.get('resultMsg', 'Unknown error')
        
        return TradeResult(
            success=success,
            message=message,
            details=response
        )
    
    async def sell_item(
        self,
        item_id: int,
        sid: int = 0,
        price: int = 0,
        quantity: int = 1
    ) -> TradeResult:
        """
        Place sell order for an item.
        
        Args:
            item_id: Item ID
            sid: Sub-item ID (enhancement level, etc.)
            price: Sell price (0 = current highest bid)
            quantity: Quantity to sell
            
        Returns:
            TradeResult indicating success/failure
            
        Example:
            >>> result = await trader.sell_item(16001, price=250000, quantity=50)
            >>> if result.success:
            >>>     print(f"Listed for sale: {result.message}")
        
        Note:
            - Item must be in your inventory/warehouse
            - 34.5% tax applied (before Value Pack/Familia discounts)
            - Order enters registration queue
        """
        data = {
            '__RequestVerificationToken': self.credentials.session_id,
            'mainKey': item_id,
            'subKey': sid,
            'pricePerOne': price,
            'count': quantity
        }
        
        response = await self._post('/Home/Sell', data)
        
        success = response.get('resultCode') == 0
        message = response.get('resultMsg', 'Unknown error')
        
        return TradeResult(
            success=success,
            message=message,
            details=response
        )
    
    async def cancel_listing(
        self,
        item_id: int,
        sid: int = 0,
        order_no: int = 0
    ) -> TradeResult:
        """
        Cancel a pending sell listing.
        
        Args:
            item_id: Item ID
            sid: Sub-item ID
            order_no: Order number (from get_bid_listings)
            
        Returns:
            TradeResult indicating success/failure
            
        Example:
            >>> listings = await trader.get_bid_listings()
            >>> result = await trader.cancel_listing(
            >>>     item_id=listings[0]['mainKey'],
            >>>     order_no=listings[0]['orderNo']
            >>> )
        
        Note:
            - Can only cancel listings not yet matched
            - Item returns to your inventory/warehouse
        """
        data = {
            'mainKey': item_id,
            'subKey': sid,
            'orderNo': order_no
        }
        
        response = await self._post('/Home/CancelSell', data)
        
        success = response.get('resultCode') == 0
        message = response.get('resultMsg', 'Unknown error')
        
        return TradeResult(
            success=success,
            message=message,
            details=response
        )
    
    async def collect_funds(self) -> TradeResult:
        """
        Collect silver from completed sales.
        
        Returns:
            TradeResult with collected amount
            
        Example:
            >>> result = await trader.collect_funds()
            >>> if result.success:
            >>>     print(f"Collected: {result.details.get('totalSilver', 0):,} silver")
        
        Note:
            - Collects all pending proceeds
            - Silver deposited to warehouse
            - Already taxed (34.5% deducted at sale time)
        """
        response = await self._post('/Home/CollectFunds', {})
        
        success = response.get('resultCode') == 0
        message = response.get('resultMsg', 'Unknown error')
        
        return TradeResult(
            success=success,
            message=message,
            details=response
        )
    
    async def get_inventory(self) -> List[Dict[str, Any]]:
        """
        Get user's Central Market inventory.
        
        Returns:
            List of items in market warehouse
            
        Example:
            >>> inventory = await trader.get_inventory()
            >>> for item in inventory:
            >>>     print(f"{item['name']}: {item['count']} units")
        
        Note:
            - Shows items in Central Market warehouse only
            - Does not include game inventory or storage
        """
        response = await self._post('/Home/GetInventory', {})
        
        if response.get('resultCode') == 0:
            return response.get('inventory', [])
        return []
    
    async def get_bid_listings(self) -> List[Dict[str, Any]]:
        """
        Get user's active bid/sell listings.
        
        Returns:
            List of pending orders
            
        Example:
            >>> listings = await trader.get_bid_listings()
            >>> for listing in listings:
            >>>     print(f"{listing['name']}: {listing['count']} @ {listing['price']:,}")
        
        Note:
            - Shows both buy and sell orders
            - Includes order numbers for cancellation
        """
        response = await self._post('/Home/GetBidList', {})
        
        if response.get('resultCode') == 0:
            return response.get('bidList', [])
        return []
    
    async def get_funds_available(self) -> int:
        """
        Get available silver for trading.
        
        Returns:
            Amount of silver in Central Market warehouse
            
        Example:
            >>> silver = await trader.get_funds_available()
            >>> print(f"Available: {silver:,} silver")
        """
        response = await self._post('/Home/GetFunds', {})
        
        if response.get('resultCode') == 0:
            return response.get('funds', 0)
        return 0


# ========================================
# Credential Management
# ========================================

def load_credentials(config_file: str = 'config/trader_auth.json') -> Optional[TradeCredentials]:
    """
    Load trading credentials from config file.
    
    Args:
        config_file: Path to credentials JSON file
        
    Returns:
        TradeCredentials or None if not found
        
    Example:
        >>> creds = load_credentials()
        >>> if creds:
        >>>     async with MarketTrader(creds) as trader:
        >>>         await trader.buy_item(16001, price=180000)
    
    Config file format (config/trader_auth.json):
    {
        "region": "eu",
        "session_id": "your__RequestVerificationToken",
        "user_no": "your_userNo"
    }
    """
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return TradeCredentials(
                session_id=data['session_id'],
                user_no=data['user_no'],
                region=data.get('region', 'eu')
            )
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"Error loading credentials: {e}")
        return None


def save_credentials(credentials: TradeCredentials, config_file: str = 'config/trader_auth.json'):
    """
    Save trading credentials to config file.
    
    Args:
        credentials: Credentials to save
        config_file: Path to save to
        
    Example:
        >>> creds = TradeCredentials(
        >>>     session_id="abc123",
        >>>     user_no="12345",
        >>>     region="eu"
        >>> )
        >>> save_credentials(creds)
    """
    try:
        data = {
            'region': credentials.region,
            'session_id': credentials.session_id,
            'user_no': credentials.user_no
        }
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Credentials saved to {config_file}")
    except Exception as e:
        print(f"Error saving credentials: {e}")



