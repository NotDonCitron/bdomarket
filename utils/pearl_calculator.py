"""
Pearl Value Calculator - Calculate extraction value and profitability.

Pearl items can be extracted at the Blacksmith for Cron Stones and Valks' Cry.
The extraction profit has NO TAX (unlike marketplace resale).

Key Facts:
- Premium Outfits (7 parts): 993 Cron Stones + 331 Valks' Cry
- Classic Outfits (6 parts): 801 Cron Stones + 267 Valks' Cry
- Simple Outfits (4 parts): 543 Cron Stones + 181 Valks' Cry
- Mount Gear: ~900 Cron Stones + ~300 Valks' Cry (varies)

NO TAX on extraction! Pure profit calculation.
"""
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio


@dataclass
class OutfitExtractionData:
    """Extraction data for outfit types."""
    cron_stones: int
    valks_cry: int
    parts: int
    

@dataclass
class PearlValueResult:
    """Result of pearl item value calculation."""
    outfit_type: str
    extraction_value: int
    market_price: int
    profit: int
    roi: float
    is_profitable: bool
    cron_price: int
    valks_price: int
    cron_stones: int
    valks_cry: int
    

class PearlValueCalculator:
    """
    Calculate extraction value and profitability for Pearl Items.
    
    Usage:
        calculator = PearlValueCalculator(market_client)
        await calculator.update_prices()
        result = calculator.calculate_value("premium", 2_170_000_000)
        if result.is_profitable:
            print(f"Profit: {result.profit:,} silver ({result.roi:.1%} ROI)")
    """
    
    # Outfit extraction rates (as of Oct 2025)
    OUTFIT_TYPES = {
        "premium": OutfitExtractionData(
            cron_stones=993,
            valks_cry=331,
            parts=7
        ),
        "classic": OutfitExtractionData(
            cron_stones=801,
            valks_cry=267,
            parts=6
        ),
        "simple": OutfitExtractionData(
            cron_stones=543,
            valks_cry=181,
            parts=4
        ),
        "mount": OutfitExtractionData(
            cron_stones=900,
            valks_cry=300,
            parts=1  # Variable
        ),
    }
    
    # Item IDs for extraction materials
    CRON_STONE_ID = 16004
    VALKS_CRY_ID = 16003
    
    # Price cache settings
    PRICE_CACHE_DURATION = 300  # 5 minutes
    
    def __init__(self, market_client):
        """
        Initialize calculator.
        
        Args:
            market_client: MarketClient instance for price fetching
        """
        self.market_client = market_client
        
        # Price cache
        self.cron_price: Optional[int] = None
        self.valks_price: Optional[int] = None
        self.last_price_update: Optional[datetime] = None
        
        # Minimum thresholds (configurable)
        self.min_profit = 100_000_000  # 100M default
        self.min_roi = 0.05  # 5% default
    
    def set_thresholds(self, min_profit: int = None, min_roi: float = None):
        """
        Set profitability thresholds.
        
        Args:
            min_profit: Minimum profit in silver (default: 100M)
            min_roi: Minimum ROI as decimal (default: 0.05 = 5%)
        """
        if min_profit is not None:
            self.min_profit = min_profit
        if min_roi is not None:
            self.min_roi = min_roi
    
    async def update_prices(self, force: bool = False) -> bool:
        """
        Fetch live Cron Stone and Valks' Cry prices from market.
        
        Args:
            force: Force update even if cache is valid
            
        Returns:
            True if prices updated successfully, False otherwise
        """
        # Check cache
        if not force and self.last_price_update:
            age = (datetime.now() - self.last_price_update).total_seconds()
            if age < self.PRICE_CACHE_DURATION:
                return True  # Cache still valid
        
        try:
            # Fetch both items in batch
            orderbooks = await self.market_client.get_orderbook_batch(
                [self.CRON_STONE_ID, self.VALKS_CRY_ID]
            )
            
            # Extract prices (use lowest seller price)
            cron_orderbook = orderbooks.get(self.CRON_STONE_ID)
            valks_orderbook = orderbooks.get(self.VALKS_CRY_ID)
            
            if not cron_orderbook or not valks_orderbook:
                return False
            
            # Get lowest sell price (first order with sellers)
            self.cron_price = self._get_sell_price(cron_orderbook)
            self.valks_price = self._get_sell_price(valks_orderbook)
            
            if self.cron_price and self.valks_price:
                self.last_price_update = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error updating prices: {e}")
            return False
    
    def _get_sell_price(self, orderbook) -> Optional[int]:
        """
        Extract sell price from orderbook.
        
        Args:
            orderbook: OrderbookData object
            
        Returns:
            Lowest sell price or None
        """
        for order in orderbook.orders:
            if order.sellers > 0:
                return order.price
        
        # Fallback: use first price even if no sellers
        if orderbook.orders:
            return orderbook.orders[0].price
        
        return None
    
    def calculate_value(
        self,
        outfit_type: str,
        market_price: int
    ) -> Optional[PearlValueResult]:
        """
        Calculate extraction value and profitability.
        
        Args:
            outfit_type: Type of outfit ("premium", "classic", "simple", "mount")
            market_price: Current market listing price
            
        Returns:
            PearlValueResult or None if prices not available
            
        Example:
            >>> result = calculator.calculate_value("premium", 2_170_000_000)
            >>> print(f"Profit: {result.profit:,} (+{result.roi:.1%})")
            Profit: 6,933,000,000 (+319.4%)
        """
        # Check if prices are available
        if not self.cron_price or not self.valks_price:
            return None
        
        # Get outfit data
        outfit_data = self.OUTFIT_TYPES.get(outfit_type.lower())
        if not outfit_data:
            return None
        
        # Calculate extraction value
        cron_value = outfit_data.cron_stones * self.cron_price
        valks_value = outfit_data.valks_cry * self.valks_price
        extraction_value = cron_value + valks_value
        
        # Calculate profit (NO TAX!)
        profit = extraction_value - market_price
        roi = profit / market_price if market_price > 0 else 0
        
        # Check profitability
        is_profitable = (profit >= self.min_profit) and (roi >= self.min_roi)
        
        return PearlValueResult(
            outfit_type=outfit_type,
            extraction_value=extraction_value,
            market_price=market_price,
            profit=profit,
            roi=roi,
            is_profitable=is_profitable,
            cron_price=self.cron_price,
            valks_price=self.valks_price,
            cron_stones=outfit_data.cron_stones,
            valks_cry=outfit_data.valks_cry
        )
    
    def detect_outfit_type(self, item_name: str) -> Optional[str]:
        """
        Detect outfit type from item name (heuristic).
        
        Args:
            item_name: Name of the pearl item
            
        Returns:
            Outfit type string or None
            
        Note: This is a heuristic based on naming patterns.
              May need adjustment based on actual item names.
        """
        name_lower = item_name.lower()
        
        # Mount gear detection
        if any(word in name_lower for word in ['horse', 'mount', 'gear', 'saddle', 'stirrup']):
            return "mount"
        
        # Simple outfits (usually have "simple" or are 4-part)
        if 'simple' in name_lower:
            return "simple"
        
        # Classic outfits (usually 6-part, older designs)
        if 'classic' in name_lower or 'original' in name_lower:
            return "classic"
        
        # Premium outfits (7-part, newest designs)
        # Default assumption for outfit sets
        if 'outfit' in name_lower or 'set' in name_lower:
            return "premium"
        
        # Unknown - default to premium (highest value)
        return "premium"
    
    def get_price_info(self) -> Dict[str, any]:
        """
        Get current price information.
        
        Returns:
            Dict with price data and cache age
        """
        age = None
        if self.last_price_update:
            age = (datetime.now() - self.last_price_update).total_seconds()
        
        return {
            'cron_price': self.cron_price,
            'valks_price': self.valks_price,
            'last_update': self.last_price_update,
            'cache_age_seconds': age,
            'cache_valid': age < self.PRICE_CACHE_DURATION if age else False
        }
    
    def get_extraction_data(self, outfit_type: str) -> Optional[OutfitExtractionData]:
        """
        Get extraction data for outfit type.
        
        Args:
            outfit_type: Outfit type string
            
        Returns:
            OutfitExtractionData or None
        """
        return self.OUTFIT_TYPES.get(outfit_type.lower())

