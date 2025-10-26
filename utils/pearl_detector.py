"""
High-speed detection of Pearl Shop listings using HTTP/2 parallel polling.
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Set, Tuple, Optional, Callable

import httpx


PEARL_ITEM_CATEGORIES: List[Dict[str, Any]] = [
    {"mainCategory": 55, "subCategory": 1, "name": "Male Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 2, "name": "Female Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 3, "name": "Male Outfits (Single)"},
    {"mainCategory": 55, "subCategory": 4, "name": "Female Outfits (Single)"},
    {"mainCategory": 55, "subCategory": 5, "name": "Class Outfits (Set)"},
    {"mainCategory": 55, "subCategory": 6, "name": "Functional"},
    {"mainCategory": 55, "subCategory": 7, "name": "Mounts"},
    {"mainCategory": 55, "subCategory": 8, "name": "Pets"},
]


@dataclass
class DetectionEvent:
    """Represents a detected pearl item listing."""
    category: Dict[str, Any]
    item: Dict[str, Any]
    timestamp: float
    is_new_listing: bool
    price: Optional[int] = None
    quantity: Optional[int] = None

    def format_summary(self) -> str:
        """Format a summary string for this event."""
        name = self.item.get('name', 'Unknown Item')
        price = self.price if self.price is not None else self.item.get('pricePerOne', 0)
        quantity = self.quantity if self.quantity is not None else self.item.get('sumCount', 0)
        main_key = self.item.get('mainKey', 'N/A')
        category_name = self.category.get('name', 'Unknown Category')
        
        return (
            f"[{category_name}] {name}\n"
            f"  ID: {main_key}\n"
            f"  Price: {price:,} silver\n"
            f"  Quantity: {quantity}\n"
            f"  Detected: {time.strftime('%H:%M:%S', time.localtime(self.timestamp))}\n"
        )


class PearlDetector:
    """
    High-speed pearl item detector using parallel HTTP/2 polling.
    
    Features:
    - Polls all 8 pearl categories in parallel
    - Uses HTTP/2 keep-alive connections
    - Detects new listings based on stock changes
    - Supports custom event handlers
    - Tracks detection metrics
    """
    
    def __init__(
        self,
        headers: Dict[str, str],
        token: str,
        interval: float = 0.1,
        categories: Optional[List[Dict[str, Any]]] = None,
        region: str = 'eu'
    ):
        """
        Initialize the detector.
        
        Args:
            headers: HTTP headers including cookies and user agent
            token: Request verification token (__RequestVerificationToken)
            interval: Polling interval in seconds
            categories: List of categories to monitor
            region: Market region
        """
        self.headers = headers
        self.token = token
        self.interval = max(0.05, interval)  # Minimum 50ms to avoid rate limits
        self.categories = categories or PEARL_ITEM_CATEGORIES
        self.region = region.lower()
        
        # Base URL
        self.base_urls = {
            'eu': 'https://eu-trade.naeu.playblackdesert.com',
            'na': 'https://na-trade.naeu.playblackdesert.com',
            'kr': 'https://trade.kr.playblackdesert.com',
            'sa': 'https://sa-trade.tr.playblackdesert.com'
        }
        self.base_url = self.base_urls.get(self.region, self.base_urls['eu'])
        self.url = f"{self.base_url}/Home/GetWorldMarketList"
        
        # Detection state
        self.seen_items: Set[Tuple[int, str, int]] = set()
        self.last_seen_stock: Dict[Tuple[int, int], int] = {}
        
        # Event handlers
        self.on_event: Optional[Callable[[DetectionEvent], Any]] = None
        self.on_error: Optional[Callable[[Exception], Any]] = None
        
        # Metrics
        self.total_loops = 0
        self.total_requests = 0
        self.total_new_items = 0
        self.total_updates = 0
        self.start_time = time.time()
        
        # HTTP client
        limits = httpx.Limits(
            max_connections=16,
            max_keepalive_connections=16,
        )
        timeout = httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0)
        
        self.client = httpx.AsyncClient(
            http2=True,
            headers=self.headers,
            limits=limits,
            timeout=timeout,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _fetch_category(self, category: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetch items for a single category."""
        payload = {
            '__RequestVerificationToken': self.token,
            'mainCategory': category['mainCategory'],
            'subCategory': category['subCategory'],
        }
        
        response = await self.client.post(self.url, data=payload)
        self.total_requests += 1
        
        if response.status_code in (401, 403):
            raise httpx.HTTPStatusError(
                f"Auth failed ({response.status_code})",
                request=response.request,
                response=response,
            )
        
        response.raise_for_status()
        data = response.json()
        
        items: List[Dict[str, Any]] = []
        if isinstance(data, dict) and isinstance(data.get('marketList'), list):
            for item in data['marketList']:
                if isinstance(item, dict):
                    # sumCount = number of items currently available
                    sum_count = int(item.get('sumCount', 0) or 0)
                    if sum_count >= 1:
                        items.append(item)
        
        return category, items
    
    async def _process_category_items(
        self,
        category: Dict[str, Any],
        items: List[Dict[str, Any]],
        timestamp: float
    ):
        """Process items from a category for new and updated listings."""
        for item in items:
            main_key = item.get('mainKey')
            name = item.get('name', 'Unknown Item')
            price = item.get('pricePerOne', 0)
            quantity = item.get('sumCount', 0)
            sub_category = category['subCategory']
            
            # Deduplication key (mainKey + price + subCategory)
            dedup_key = (main_key, price, sub_category)
            stock_key = (main_key, sub_category)
            
            last_stock = self.last_seen_stock.get(stock_key, 0)
            is_new_listing = dedup_key not in self.seen_items
            stock_increased = quantity > last_stock
            
            if is_new_listing or stock_increased:
                event = DetectionEvent(
                    category=category,
                    item=item,
                    timestamp=timestamp,
                    is_new_listing=is_new_listing,
                    price=price,
                    quantity=quantity,
                )
                
                if self.on_event:
                    await self._dispatch_event(event)
                
                self.seen_items.add(dedup_key)
                if is_new_listing:
                    self.total_new_items += 1
                else:
                    self.total_updates += 1
            
            # Update stock tracking
            self.last_seen_stock[stock_key] = max(quantity, last_stock)
    
    async def _dispatch_event(self, event: DetectionEvent):
        """Dispatch event to handler with exception safety."""
        try:
            result = self.on_event(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            if self.on_error:
                self.on_error(e)
            else:
                print(f"Error in event handler: {e}")
    
    async def start(self):
        """Start monitoring loop."""
        try:
            while True:
                self.total_loops += 1
                timestamp = time.time()
                
                # Fetch all categories in parallel
                tasks = [self._fetch_category(cat) for cat in self.categories]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        if self.on_error:
                            self.on_error(result)
                        else:
                            print(f"Detector error: {result}")
                        continue
                    
                    category, items = result
                    await self._process_category_items(category, items, timestamp)
                
                await asyncio.sleep(self.interval)
        finally:
            await self.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        elapsed = time.time() - self.start_time
        loops_per_sec = self.total_loops / elapsed if elapsed > 0 else 0
        
        return {
            'total_loops': self.total_loops,
            'total_requests': self.total_requests,
            'total_new_items': self.total_new_items,
            'total_updates': self.total_updates,
            'runtime_seconds': elapsed,
            'loops_per_second': loops_per_sec,
        }


async def example_usage():
    """Example usage of the PearlDetector."""
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'user-agent': 'Mozilla/5.0',
        'cookie': 'your_cookie_here',
        'x-requested-with': 'XMLHttpRequest',
        'origin': 'https://eu-trade.naeu.playblackdesert.com',
        'referer': 'https://eu-trade.naeu.playblackdesert.com/Home/list/55-1',
    }
    token = 'your_request_verification_token'
    
    detector = PearlDetector(headers, token, interval=0.1)
    
    async def on_event(event: DetectionEvent):
        print("New item detected:")
        print(event.format_summary())
    
    detector.on_event = on_event
    
    await detector.start()


if __name__ == '__main__':
    asyncio.run(example_usage())
