#!/usr/bin/env python3
"""
Market History Watcher - Automatically record daily snapshots.

This script runs continuously and records market snapshots at midnight
each day, building up your historical database automatically.

Usage:
    # Run in foreground
    python watch_market_history.py
    
    # Run in background (Windows)
    pythonw watch_market_history.py
    
    # Run with custom schedule
    python watch_market_history.py --interval 24  # hours between snapshots

Features:
    - Automatic daily recording at midnight
    - Retry logic if API fails
    - Logs all activity
    - Can run as background service
"""
import asyncio
import argparse
from datetime import datetime, time
from pathlib import Path

from utils.market_history_tracker import MarketHistoryTracker


class HistoryWatcher:
    """Watches and records market history on schedule."""
    
    def __init__(self, region: str = 'eu', interval_hours: int = 24):
        """
        Initialize watcher.
        
        Args:
            region: Market region
            interval_hours: Hours between snapshots (default: 24)
        """
        self.region = region
        self.interval_hours = interval_hours
        self.tracker = MarketHistoryTracker(region=region)
        self.log_file = Path('data/market_history/recorder.log')
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str):
        """Log message to file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    
    async def record_with_retry(self, max_retries: int = 3):
        """Record snapshot with retry logic."""
        for attempt in range(1, max_retries + 1):
            self.log(f"Recording snapshot (attempt {attempt}/{max_retries})...")
            
            try:
                success = await self.tracker.record_snapshot(verbose=False)
                
                if success:
                    summary = self.tracker.get_summary()
                    self.log(f"✓ Snapshot recorded! Total days: {summary['days_of_data']}")
                    return True
                else:
                    self.log(f"✗ Snapshot failed (attempt {attempt})")
            except Exception as e:
                self.log(f"✗ Error during snapshot: {e}")
            
            if attempt < max_retries:
                self.log("Retrying in 5 minutes...")
                await asyncio.sleep(300)  # 5 minutes
        
        self.log("✗ All retry attempts failed")
        return False
    
    def should_record_now(self, last_recorded: str) -> bool:
        """
        Check if we should record now based on interval.
        
        Args:
            last_recorded: Last recorded date 'YYYY-MM-DD'
            
        Returns:
            True if interval has passed
        """
        today = datetime.now().strftime('%Y-%m-%d')
        return today != last_recorded
    
    async def run(self):
        """Run the watcher continuously."""
        self.log("=" * 60)
        self.log("Market History Watcher Started")
        self.log(f"Region: {self.region}")
        self.log(f"Interval: {self.interval_hours} hours")
        self.log("=" * 60)
        
        # Check if we should record on startup
        summary = self.tracker.get_summary()
        if summary['total_snapshots'] == 0:
            self.log("No existing snapshots - recording first snapshot...")
            await self.record_with_retry()
        else:
            last_date = summary['latest_snapshot']
            self.log(f"Last snapshot: {last_date}")
            
            if self.should_record_now(last_date):
                self.log("New day detected - recording snapshot...")
                await self.record_with_retry()
            else:
                self.log("Already recorded today")
        
        # Main loop
        while True:
            # Calculate time until midnight
            now = datetime.now()
            midnight = datetime.combine(now.date(), time(0, 0, 0))
            
            # If past midnight, calculate next midnight
            if now >= midnight:
                from datetime import timedelta
                midnight = midnight + timedelta(days=1)
            
            seconds_until_midnight = (midnight - now).total_seconds()
            
            self.log(f"Next snapshot in {seconds_until_midnight / 3600:.1f} hours (at midnight)")
            
            # Sleep until midnight (with periodic wake-ups to check)
            # Wake up every hour to show we're still alive
            wake_interval = 3600  # 1 hour
            
            while seconds_until_midnight > 0:
                sleep_time = min(wake_interval, seconds_until_midnight)
                await asyncio.sleep(sleep_time)
                seconds_until_midnight -= sleep_time
                
                if seconds_until_midnight > wake_interval:
                    now = datetime.now()
                    self.log(f"Still running... Next snapshot in {seconds_until_midnight / 3600:.1f} hours")
            
            # It's midnight! Record snapshot
            self.log("Midnight reached - recording daily snapshot...")
            await self.record_with_retry()


async def main():
    parser = argparse.ArgumentParser(
        description='Continuously monitor and record market history'
    )
    parser.add_argument(
        '--region',
        default='eu',
        choices=['eu', 'na', 'kr', 'sa'],
        help='Market region (default: eu)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Hours between snapshots (default: 24)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Record once and exit (for testing)'
    )
    
    args = parser.parse_args()
    
    watcher = HistoryWatcher(
        region=args.region,
        interval_hours=args.interval
    )
    
    if args.once:
        # Test mode: record once and exit
        await watcher.record_with_retry()
    else:
        # Normal mode: run continuously
        try:
            await watcher.run()
        except KeyboardInterrupt:
            watcher.log("\nShutting down gracefully...")
            watcher.log("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())

