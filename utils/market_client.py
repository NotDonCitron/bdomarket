"""
Market Client - Wrapper around bdomarket library.

Provides abstraction layer so we can easily switch implementations if needed.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from bdomarket import Market, MarketRegion


@dataclass
class OrderLevel:
    """Single price level in orderbook."""
    price: int
    buyers: int
    sellers: int


@dataclass
class ItemInfo:
    """Item information with name and ID."""
    id: int
    name: str
    sid: int = 0


@dataclass
class OrderbookData:
    """Orderbook data for an item."""
    item: ItemInfo
    orders: List[OrderLevel]


class MarketClient:
    """
    Wrapper around bdomarket for BDO Central Market API access.
    
    Usage:
        async with MarketClient(region='eu') as client:
            orderbook = await client.get_orderbook(16001)
            print(orderbook.item.name)  # "Black Stone"
    """
    
    def __init__(self, region: str = 'eu'):
        """
        Initialize market client.
        
        Args:
            region: Market region ('eu', 'na', 'kr', 'sa')
        """
        # Map string to MarketRegion enum
        region_map = {
            'eu': MarketRegion.EU,
            'na': MarketRegion.NA,
            'kr': MarketRegion.KR,
            'sa': MarketRegion.SA
        }
        
        region_enum = region_map.get(region.lower(), MarketRegion.EU)
        self.market = Market(region=region_enum)
        self.region = region.lower()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
    
    def close(self):
        """Close the market client."""
        if self.market:
            self.market.close()
    
    async def get_orderbook(self, item_id: int, sid: int = 0) -> Optional[OrderbookData]:
        """
        Get orderbook (bidding info) for an item.
        
        Args:
            item_id: Item ID
            sid: Sub-item ID (default: 0)
            
        Returns:
            OrderbookData or None if request failed
            
        Example:
            >>> orderbook = await client.get_orderbook(16001)
            >>> print(orderbook.item.name)  # "Black Stone"
            >>> print(len(orderbook.orders))  # Number of price levels
        """
        try:
            result = await self.market.get_bidding_info(
                ids=[str(item_id)],
                sids=[str(sid)]
            )
            
            if not result.success or not result.content:
                return None
            
            # bdomarket returns dict with item info + orders
            data = result.content
            
            item = ItemInfo(
                id=data.get('id', item_id),
                name=data.get('name', f'Item_{item_id}'),
                sid=data.get('sid', sid)
            )
            
            # Parse orders
            orders = []
            for order_data in data.get('orders', []):
                orders.append(OrderLevel(
                    price=order_data['price'],
                    buyers=order_data['buyers'],
                    sellers=order_data['sellers']
                ))
            
            return OrderbookData(item=item, orders=orders)
            
        except Exception as e:
            print(f"Error fetching orderbook for {item_id}: {e}")
            return None
    
    async def get_orderbook_batch(
        self,
        item_ids: List[int],
        sid: int = 0
    ) -> Dict[int, OrderbookData]:
        """
        Get orderbooks for multiple items.
        
        Args:
            item_ids: List of item IDs
            sid: Sub-item ID (default: 0)
            
        Returns:
            Dict mapping item_id to OrderbookData
            
        Example:
            >>> orderbooks = await client.get_orderbook_batch([16001, 16002])
            >>> for item_id, orderbook in orderbooks.items():
            >>>     print(f"{orderbook.item.name}: {len(orderbook.orders)} levels")
        """
        try:
            result = await self.market.post_bidding_info(
                ids=[str(i) for i in item_ids],
                sids=[str(sid)] * len(item_ids)
            )
            
            if not result.success or not result.content:
                return {}
            
            # Parse results
            orderbooks = {}
            content_list = result.content if isinstance(result.content, list) else [result.content]
            
            for data in content_list:
                if not isinstance(data, dict):
                    continue
                
                item_id = data.get('id')
                if item_id is None:
                    continue
                
                item = ItemInfo(
                    id=item_id,
                    name=data.get('name', f'Item_{item_id}'),
                    sid=data.get('sid', sid)
                )
                
                orders = []
                for order_data in data.get('orders', []):
                    orders.append(OrderLevel(
                        price=order_data['price'],
                        buyers=order_data['buyers'],
                        sellers=order_data['sellers']
                    ))
                
                orderbooks[item_id] = OrderbookData(item=item, orders=orders)
            
            return orderbooks
            
        except Exception as e:
            print(f"Error fetching batch orderbooks: {e}")
            return {}
    
    async def search_items(self, query: str, limit: int = 10) -> List[ItemInfo]:
        """
        Search for items by name (not fully implemented in bdomarket).
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of ItemInfo objects
            
        Note: This is a placeholder. bdomarket's search may need specific IDs.
              For now, we can use item database helper for search.
        """
        # TODO: Implement proper search or use item database
        return []
    
    async def get_market_list(self) -> List[Dict[str, Any]]:
        """
        Get full market list.
        
        Returns:
            List of items with IDs, stock, trades, base_price
        """
        try:
            result = await self.market.get_market()
            if result.success and result.content:
                return result.content if isinstance(result.content, list) else []
            return []
        except Exception as e:
            print(f"Error fetching market list: {e}")
            return []

