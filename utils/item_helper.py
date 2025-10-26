"""
Item Helper - Convenience layer for item operations with caching.
"""
from typing import List, Optional, Tuple
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from .market_client import MarketClient, ItemInfo


@dataclass
class ItemSearchResult:
    """Result from item search with fuzzy score."""
    item: ItemInfo
    score: float


class ItemHelper:
    """
    Helper for item search with caching and fuzzy matching.
    
    Usage:
        helper = ItemHelper()
        await helper.init()  # Load market data
        
        results = helper.search("black stone")
        for result in results:
            print(f"{result.item.name} - Score: {result.score}")
    """
    
    def __init__(self, region: str = 'eu'):
        """
        Initialize item helper.
        
        Args:
            region: Market region
        """
        self.client = MarketClient(region=region)
        self._cache: dict[int, ItemInfo] = {}
        self._name_to_id: dict[str, int] = {}
        self._initialized = False
    
    async def init(self):
        """
        Initialize helper by loading market data.
        Call this once before using search.
        """
        if self._initialized:
            return
        
        try:
            # Get market list to build cache
            market_list = await self.client.get_market_list()
            
            # We only have IDs and basic info, not names
            # Names come from orderbook calls
            for item_data in market_list:
                item_id = item_data.get('id')
                if item_id:
                    # Create placeholder ItemInfo
                    # Real names will be fetched on-demand
                    self._cache[item_id] = ItemInfo(
                        id=item_id,
                        name=f"Item_{item_id}",
                        sid=0
                    )
            
            self._initialized = True
            print(f"ItemHelper initialized with {len(self._cache)} items")
            
        except Exception as e:
            print(f"Warning: Failed to initialize ItemHelper: {e}")
    
    async def get_by_id(self, item_id: int) -> Optional[ItemInfo]:
        """
        Get item by ID, fetching name from orderbook if needed.
        
        Args:
            item_id: Item ID
            
        Returns:
            ItemInfo with real name or None
        """
        # Check cache first
        if item_id in self._cache:
            cached = self._cache[item_id]
            # If we have a real name, return it
            if not cached.name.startswith("Item_"):
                return cached
        
        # Fetch from orderbook to get real name
        orderbook = await self.client.get_orderbook(item_id)
        if orderbook and orderbook.item:
            # Update cache
            self._cache[item_id] = orderbook.item
            self._name_to_id[orderbook.item.name.lower()] = item_id
            return orderbook.item
        
        return None
    
    def search(self, query: str, limit: int = 10, min_score: int = 60) -> List[ItemSearchResult]:
        """
        Fuzzy search items by name.
        
        Args:
            query: Search query
            limit: Max results
            min_score: Minimum fuzzy match score (0-100)
            
        Returns:
            List of ItemSearchResult sorted by score
            
        Note: Only works for items that have been fetched (have real names).
              For full search, use await get_by_id() first to populate cache.
        """
        if not query:
            return []
        
        # Build dict of items with real names
        searchable = {}
        for item_id, item in self._cache.items():
            if not item.name.startswith("Item_"):
                searchable[item_id] = item.name
        
        if not searchable:
            return []
        
        # Fuzzy search
        matches = process.extract(
            query,
            searchable,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=min_score
        )
        
        # Convert to results
        results = []
        for name, score, item_id in matches:
            item = self._cache.get(item_id)
            if item:
                results.append(ItemSearchResult(item=item, score=score))
        
        return results
    
    def get_by_name_exact(self, name: str) -> Optional[ItemInfo]:
        """
        Get item by exact name (case-insensitive).
        
        Args:
            name: Item name
            
        Returns:
            ItemInfo or None
        """
        item_id = self._name_to_id.get(name.lower())
        if item_id is not None:
            return self._cache.get(item_id)
        return None
    
    def close(self):
        """Close the client."""
        self.client.close()

