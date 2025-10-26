"""
Market Intelligence - Track Pearl item trends using bdomarket API.

Monitors Pearl item activity by tracking stock changes in the marketplace.
Identifies popular items and provides statistics for optimization.

Features:
- Track Pearl item sales (stock decreases)
- Identify most-traded items in 24h window
- Calculate average prices
- No external APIs needed (bdomarket only)
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class MarketIntelligence:
    """
    Track Pearl item market activity and trends.
    
    Usage:
        intel = MarketIntelligence(market_client)
        await intel.update_statistics()
        popular = intel.get_popular_items(limit=5)
    """
    
    def __init__(self, market_client):
        """
        Initialize market intelligence.
        
        Args:
            market_client: MarketClient instance
        """
        self.market_client = market_client
        
        # Statistics storage
        # {item_id: {
        #   "name": str,
        #   "last_stock": int,
        #   "sales_count": int,
        #   "last_seen": datetime,
        #   "prices": [int],  # Recent prices for averaging
        #   "total_sales": int  # All-time counter
        # }}
        self.pearl_stats: Dict[int, dict] = {}
        
        # Configuration
        self.tracking_window = 86400  # 24 hours in seconds
        self.max_price_samples = 20  # Keep last N prices for averaging
        
        # Pearl item ID range
        self.pearl_id_min = 40000
        self.pearl_id_max = 50000
        
        # Statistics
        self.last_update = datetime.now()
        self.update_count = 0
    
    async def update_statistics(self) -> bool:
        """
        Update Pearl item statistics from market list.
        
        Tracks stock changes to detect sales.
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Fetch current market list
            market_list = await self.market_client.get_market_list()
            
            if not market_list:
                return False
            
            # Filter for Pearl items (40000-49999)
            pearl_items = [
                item for item in market_list
                if self.pearl_id_min <= item.get('id', 0) < self.pearl_id_max
            ]
            
            current_time = datetime.now()
            
            # Process each Pearl item
            for item in pearl_items:
                item_id = item.get('id')
                if not item_id:
                    continue
                
                item_name = item.get('name', f'Pearl Item {item_id}')
                current_stock = item.get('stock', 0)
                current_price = item.get('base_price', 0)
                
                # Initialize if new item
                if item_id not in self.pearl_stats:
                    self.pearl_stats[item_id] = {
                        'name': item_name,
                        'last_stock': current_stock,
                        'sales_count': 0,
                        'last_seen': current_time,
                        'prices': [current_price] if current_price > 0 else [],
                        'total_sales': 0
                    }
                    continue
                
                # Check for stock decrease (= sales detected)
                stats = self.pearl_stats[item_id]
                last_stock = stats['last_stock']
                
                if current_stock < last_stock:
                    # Sales detected!
                    sales = last_stock - current_stock
                    stats['sales_count'] += sales
                    stats['total_sales'] += sales
                
                # Update stock
                stats['last_stock'] = current_stock
                stats['last_seen'] = current_time
                
                # Update name (in case it changed)
                stats['name'] = item_name
                
                # Track price
                if current_price > 0:
                    stats['prices'].append(current_price)
                    # Keep only recent prices
                    if len(stats['prices']) > self.max_price_samples:
                        stats['prices'] = stats['prices'][-self.max_price_samples:]
            
            # Clean old data (items not seen in 24h)
            self._clean_old_data(current_time)
            
            self.last_update = current_time
            self.update_count += 1
            return True
            
        except Exception as e:
            print(f"Error updating market intelligence: {e}")
            return False
    
    def _clean_old_data(self, current_time: datetime):
        """
        Remove items not seen within tracking window.
        
        Args:
            current_time: Current datetime for comparison
        """
        cutoff = current_time - timedelta(seconds=self.tracking_window)
        
        # Find items to remove
        items_to_remove = []
        for item_id, stats in self.pearl_stats.items():
            if stats['last_seen'] < cutoff:
                items_to_remove.append(item_id)
        
        # Remove old items
        for item_id in items_to_remove:
            del self.pearl_stats[item_id]
    
    def get_popular_items(self, limit: int = 10) -> List[Dict]:
        """
        Get most popular Pearl items by sales count.
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of dicts with item stats, sorted by popularity
            
        Example:
            >>> popular = intel.get_popular_items(limit=5)
            >>> for item in popular:
            >>>     print(f"{item['name']}: {item['sales_count']} sales")
        """
        # Sort by sales_count (descending)
        sorted_items = sorted(
            self.pearl_stats.items(),
            key=lambda x: x[1]['sales_count'],
            reverse=True
        )
        
        # Build result list
        results = []
        for item_id, stats in sorted_items[:limit]:
            avg_price = sum(stats['prices']) // len(stats['prices']) if stats['prices'] else 0
            
            results.append({
                'item_id': item_id,
                'name': stats['name'],
                'sales_count': stats['sales_count'],
                'total_sales': stats['total_sales'],
                'avg_price': avg_price,
                'last_seen': stats['last_seen']
            })
        
        return results
    
    def get_item_statistics(self, item_id: int) -> Optional[Dict]:
        """
        Get statistics for specific Pearl item.
        
        Args:
            item_id: Pearl item ID
            
        Returns:
            Dict with stats or None if not tracked
            
        Example:
            >>> stats = intel.get_item_statistics(40001)
            >>> print(f"Sales: {stats['sales_count']}")
        """
        if item_id not in self.pearl_stats:
            return None
        
        stats = self.pearl_stats[item_id]
        avg_price = sum(stats['prices']) // len(stats['prices']) if stats['prices'] else 0
        
        return {
            'item_id': item_id,
            'name': stats['name'],
            'sales_count': stats['sales_count'],
            'total_sales': stats['total_sales'],
            'avg_price': avg_price,
            'current_stock': stats['last_stock'],
            'last_seen': stats['last_seen']
        }
    
    def get_tracked_count(self) -> int:
        """
        Get number of currently tracked items.
        
        Returns:
            Count of tracked Pearl items
        """
        return len(self.pearl_stats)
    
    def get_total_sales(self) -> int:
        """
        Get total sales across all tracked items.
        
        Returns:
            Total sales count in tracking window
        """
        return sum(stats['sales_count'] for stats in self.pearl_stats.values())
    
    def get_stats_summary(self) -> Dict:
        """
        Get summary statistics.
        
        Returns:
            Dict with overall stats
        """
        return {
            'tracked_items': self.get_tracked_count(),
            'total_sales': self.get_total_sales(),
            'last_update': self.last_update,
            'update_count': self.update_count,
            'tracking_window_hours': self.tracking_window / 3600
        }
    
    def reset_sales_counts(self):
        """Reset sales counts for all items (keeps other data)."""
        for stats in self.pearl_stats.values():
            stats['sales_count'] = 0

