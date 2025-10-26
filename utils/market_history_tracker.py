"""
Market History Tracker - Collect and query historical stock & trades data.

Since there's no API for historical market data (like Garmoth has),
this module lets you build your own local database by:
1. Running daily snapshots of all market items
2. Storing stock & trades counts over time
3. Querying historical data for analysis

Usage:
    # Record daily snapshot
    tracker = MarketHistoryTracker(region='eu')
    await tracker.record_snapshot()
    
    # Query history (after collecting data for days/weeks)
    stock_history = tracker.get_stock_history([16001, 16002], days=90)
    trades_history = tracker.get_trades_history([16001], days=30)
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict

from .market_client import MarketClient
from .storage import ensure_file_exists


class MarketHistoryTracker:
    """
    Track market stock and trades history by recording daily snapshots.
    
    This solves the problem that there's no API for historical data.
    You need to run this daily to build up your own database.
    
    Data Format:
        data/market_history/YYYY-MM/YYYY-MM-DD.jsonl
        Each line: {"date": "2025-10-25", "item_id": 16001, "stock": 100, "trades": 5000}
    """
    
    def __init__(self, region: str = 'eu', history_dir: str = 'data/market_history'):
        """
        Initialize history tracker.
        
        Args:
            region: Market region
            history_dir: Directory to store history files
        """
        self.region = region
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    async def record_snapshot(self, verbose: bool = True) -> bool:
        """
        Record current market snapshot (stock & trades for all items).
        
        Run this once per day to build historical data.
        
        Args:
            verbose: Print progress
            
        Returns:
            True if successful
            
        Example:
            >>> tracker = MarketHistoryTracker()
            >>> await tracker.record_snapshot()
            Recording market snapshot for 2025-10-25...
            Recorded 8,234 items
        """
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        
        if verbose:
            print(f"Recording market snapshot for {date_str}...")
        
        # Fetch current market data
        async with MarketClient(region=self.region) as client:
            market_list = await client.get_market_list()
            
            if not market_list:
                if verbose:
                    print("Failed to fetch market data!")
                return False
        
        # Prepare snapshot file
        year_month = today.strftime('%Y-%m')
        month_dir = self.history_dir / year_month
        month_dir.mkdir(parents=True, exist_ok=True)
        
        snapshot_file = month_dir / f"{date_str}.jsonl"
        
        # Write snapshot (one line per item)
        items_recorded = 0
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            for item in market_list:
                # Extract data from market API response
                # API returns: id, name, currentStock, totalTrades, basePrice
                item_id = item.get('id')
                if not item_id:
                    continue
                
                record = {
                    'date': date_str,
                    'item_id': item_id,
                    'stock': item.get('currentStock', 0),
                    'trades': item.get('totalTrades', 0),
                    'base_price': item.get('basePrice', 0)
                }
                
                f.write(json.dumps(record) + '\n')
                items_recorded += 1
        
        if verbose:
            print(f"✓ Recorded {items_recorded:,} items to {snapshot_file}")
        
        return True
    
    def get_stock_history(
        self,
        item_ids: List[int],
        days: int = 90,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[int, List[Tuple[str, int]]]:
        """
        Get stock history for items over time.
        
        Args:
            item_ids: List of item IDs to query
            days: Number of days to look back (default: 90)
            start_date: Optional start date 'YYYY-MM-DD' (overrides days)
            end_date: Optional end date 'YYYY-MM-DD'
            
        Returns:
            Dict mapping item_id to list of (date, stock_count) tuples
            
        Example:
            >>> tracker = MarketHistoryTracker()
            >>> history = tracker.get_stock_history([16001, 16002], days=7)
            >>> print(history[16001])
            [('2025-10-19', 150), ('2025-10-20', 145), ...]
        """
        # Determine date range
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = datetime.now()
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = end - timedelta(days=days)
        
        # Collect data
        result: Dict[int, List[Tuple[str, int]]] = {item_id: [] for item_id in item_ids}
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            records = self._read_snapshot(date_str)
            
            for item_id in item_ids:
                if item_id in records:
                    stock = records[item_id].get('stock', 0)
                    result[item_id].append((date_str, stock))
            
            current += timedelta(days=1)
        
        return result
    
    def get_trades_history(
        self,
        item_ids: List[int],
        days: int = 90,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[int, List[Tuple[str, int]]]:
        """
        Get trades history for items over time.
        
        Args:
            item_ids: List of item IDs to query
            days: Number of days to look back (default: 90)
            start_date: Optional start date 'YYYY-MM-DD'
            end_date: Optional end date 'YYYY-MM-DD'
            
        Returns:
            Dict mapping item_id to list of (date, total_trades) tuples
            
        Example:
            >>> history = tracker.get_trades_history([16001], days=30)
            >>> print(history[16001])
            [('2025-09-25', 45000), ('2025-09-26', 45200), ...]
        """
        # Same logic as stock but return trades
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = datetime.now()
        
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = end - timedelta(days=days)
        
        result: Dict[int, List[Tuple[str, int]]] = {item_id: [] for item_id in item_ids}
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            records = self._read_snapshot(date_str)
            
            for item_id in item_ids:
                if item_id in records:
                    trades = records[item_id].get('trades', 0)
                    result[item_id].append((date_str, trades))
            
            current += timedelta(days=1)
        
        return result
    
    def get_daily_sales(
        self,
        item_ids: List[int],
        days: int = 90
    ) -> Dict[int, List[Tuple[str, int]]]:
        """
        Calculate daily sales (delta in trades count).
        
        This is more useful than total_trades because it shows
        how many items were sold on each specific day.
        
        Args:
            item_ids: List of item IDs
            days: Number of days to analyze
            
        Returns:
            Dict mapping item_id to list of (date, daily_sales) tuples
            
        Example:
            >>> sales = tracker.get_daily_sales([16001], days=7)
            >>> print(sales[16001])
            [('2025-10-20', 150), ('2025-10-21', 180), ...]
            # 150 items sold on Oct 20, 180 on Oct 21
        """
        trades_history = self.get_trades_history(item_ids, days=days + 1)
        
        result: Dict[int, List[Tuple[str, int]]] = {}
        
        for item_id, history in trades_history.items():
            if len(history) < 2:
                result[item_id] = []
                continue
            
            daily_sales = []
            for i in range(1, len(history)):
                prev_date, prev_trades = history[i-1]
                curr_date, curr_trades = history[i]
                
                # Sales = increase in total trades
                sales = curr_trades - prev_trades
                daily_sales.append((curr_date, max(0, sales)))  # Avoid negative
            
            result[item_id] = daily_sales
        
        return result
    
    def _read_snapshot(self, date_str: str) -> Dict[int, dict]:
        """
        Read snapshot file for a specific date.
        
        Args:
            date_str: Date in 'YYYY-MM-DD' format
            
        Returns:
            Dict mapping item_id to {stock, trades, base_price}
        """
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year_month = date_obj.strftime('%Y-%m')
        snapshot_file = self.history_dir / year_month / f"{date_str}.jsonl"
        
        if not snapshot_file.exists():
            return {}
        
        records = {}
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    item_id = data.get('item_id')
                    if item_id:
                        records[item_id] = {
                            'stock': data.get('stock', 0),
                            'trades': data.get('trades', 0),
                            'base_price': data.get('base_price', 0)
                        }
        except Exception as e:
            print(f"Warning: Failed to read {snapshot_file}: {e}")
        
        return records
    
    def get_available_dates(self) -> List[str]:
        """
        Get list of dates with recorded snapshots.
        
        Returns:
            List of date strings in 'YYYY-MM-DD' format
            
        Example:
            >>> tracker.get_available_dates()
            ['2025-10-20', '2025-10-21', '2025-10-22', '2025-10-23', '2025-10-25']
        """
        dates = []
        
        for month_dir in sorted(self.history_dir.glob('*')):
            if not month_dir.is_dir():
                continue
            
            for snapshot_file in sorted(month_dir.glob('*.jsonl')):
                date_str = snapshot_file.stem  # filename without .jsonl
                dates.append(date_str)
        
        return dates
    
    def get_summary(self) -> dict:
        """
        Get summary of collected data.
        
        Returns:
            Dict with statistics about collected history
            
        Example:
            >>> print(tracker.get_summary())
            {
                'total_snapshots': 15,
                'date_range': ('2025-10-10', '2025-10-25'),
                'days_of_data': 15,
                'latest_snapshot': '2025-10-25'
            }
        """
        dates = self.get_available_dates()
        
        if not dates:
            return {
                'total_snapshots': 0,
                'date_range': None,
                'days_of_data': 0,
                'latest_snapshot': None
            }
        
        return {
            'total_snapshots': len(dates),
            'date_range': (dates[0], dates[-1]),
            'days_of_data': len(dates),
            'latest_snapshot': dates[-1]
        }

