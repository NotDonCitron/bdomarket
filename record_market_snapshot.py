#!/usr/bin/env python3
"""
Market History Recorder - Run this daily to build historical database.

This script records a snapshot of the entire market (stock & trades for all items)
and stores it locally. Over time, you'll build up historical data like Garmoth.com.

Usage:
    # Manual run
    python record_market_snapshot.py
    
    # With region
    python record_market_snapshot.py --region eu
    
    # Show summary
    python record_market_snapshot.py --summary

Schedule this to run daily:
    - Windows Task Scheduler: Run at midnight
    - Linux cron: 0 0 * * * /path/to/python record_market_snapshot.py
    - Or use watch_market_history.py for continuous monitoring
"""
import asyncio
import argparse
from datetime import datetime

from utils.market_history_tracker import MarketHistoryTracker


async def main():
    parser = argparse.ArgumentParser(
        description='Record daily market snapshot for historical tracking'
    )
    parser.add_argument(
        '--region',
        default='eu',
        choices=['eu', 'na', 'kr', 'sa'],
        help='Market region (default: eu)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of collected data instead of recording'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    tracker = MarketHistoryTracker(region=args.region)
    
    if args.summary:
        # Show summary
        summary = tracker.get_summary()
        
        print("=" * 60)
        print("Market History Database Summary")
        print("=" * 60)
        
        if summary['total_snapshots'] == 0:
            print("No snapshots recorded yet!")
            print("\nRun without --summary to record your first snapshot.")
        else:
            print(f"Total Snapshots:  {summary['total_snapshots']}")
            print(f"Date Range:       {summary['date_range'][0]} to {summary['date_range'][1]}")
            print(f"Days of Data:     {summary['days_of_data']}")
            print(f"Latest Snapshot:  {summary['latest_snapshot']}")
            
            print("\nAvailable dates:")
            dates = tracker.get_available_dates()
            for i in range(0, len(dates), 7):
                week = dates[i:i+7]
                print("  " + "  ".join(week))
        
        print("=" * 60)
    else:
        # Record snapshot
        if not args.quiet:
            print(f"\n{'='*60}")
            print(f"Market History Recorder - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
        
        success = await tracker.record_snapshot(verbose=not args.quiet)
        
        if success:
            if not args.quiet:
                summary = tracker.get_summary()
                print(f"\n✓ Success! You now have {summary['days_of_data']} days of data")
                
                if summary['days_of_data'] < 7:
                    print("\n💡 Tip: Run this daily to build up 90 days of history")
                    print("   You can then query stock/trades trends over time")
        else:
            print("\n✗ Failed to record snapshot")
            return 1
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)

