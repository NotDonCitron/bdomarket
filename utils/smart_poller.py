"""
Smart Poller - Adaptive polling rate optimization.

Adjusts polling interval based on:
- Time of day (peak hours = faster polling)
- Recent activity (recent listings = faster polling)
- Configuration settings

Typical intervals:
- Peak hours (18-22 UTC): 1 second
- Recent activity: 1.5 seconds
- Normal hours: 2 seconds
"""
from typing import Optional
from datetime import datetime, timedelta
from collections import deque


class SmartPoller:
    """
    Adaptive polling rate manager.
    
    Usage:
        poller = SmartPoller(base_interval=2, peak_interval=1)
        while True:
            # ... do work ...
            await asyncio.sleep(poller.get_interval())
            poller.record_activity()  # Call when item detected
    """
    
    def __init__(
        self,
        base_interval: float = 2.0,
        peak_interval: float = 1.0,
        activity_interval: float = 1.5,
        peak_hours_enabled: bool = True,
        prime_time_enabled: bool = True
    ):
        """
        Initialize smart poller.
        
        Args:
            base_interval: Default polling interval (seconds)
            peak_interval: Interval during peak hours (seconds)
            activity_interval: Interval when recent activity detected (seconds)
            peak_hours_enabled: Enable peak hours boost
            prime_time_enabled: Enable prime time boost (EU maintenance + weekends)
        """
        self.base_interval = base_interval
        self.peak_interval = peak_interval
        self.activity_interval = activity_interval
        self.peak_hours_enabled = peak_hours_enabled
        self.prime_time_enabled = prime_time_enabled
        
        # Peak hours configuration (UTC)
        self.peak_start_hour = 18  # 18:00 UTC
        self.peak_end_hour = 22    # 22:00 UTC
        
        # Prime time configuration (EU specific)
        self.maintenance_day = 2  # Wednesday (0=Monday)
        self.maintenance_hours = (10, 14)  # 10:00-14:00 UTC
        
        # Weekend prime hours
        self.weekend_prime = {
            4: (18, 23),  # Friday 18-23 UTC
            5: (18, 23),  # Saturday 18-23 UTC
        }
        
        # Activity tracking
        self.activity_window = 300  # 5 minutes
        self.recent_activities: deque = deque()  # Timestamps of recent activities
        
        # Statistics
        self.total_polls = 0
        self.activity_count = 0
        self.start_time = datetime.now()
    
    def get_interval(self) -> float:
        """
        Get current polling interval based on conditions.
        
        Priority order:
        1. Recent activity (highest)
        2. Prime time (EU maintenance + weekends)
        3. Peak hours (18-22 UTC)
        4. Base interval (default)
        
        Returns:
            Polling interval in seconds
        """
        self.total_polls += 1
        
        # Check for recent activity first (highest priority)
        if self._has_recent_activity():
            return self.activity_interval
        
        # Check prime time (EU-specific optimal listing times)
        if self.prime_time_enabled and self._is_prime_time():
            return self.peak_interval  # 1s during prime time
        
        # Check peak hours (general evening hours)
        if self.peak_hours_enabled and self._is_peak_hours():
            return self.peak_interval
        
        # Default interval
        return self.base_interval
    
    def record_activity(self):
        """
        Record activity (e.g., pearl item detected).
        
        Call this whenever a potentially valuable event is detected
        to boost polling rate temporarily.
        """
        self.recent_activities.append(datetime.now())
        self.activity_count += 1
        
        # Clean old activities
        self._clean_old_activities()
    
    def _has_recent_activity(self) -> bool:
        """
        Check if there was recent activity within the time window.
        
        Returns:
            True if activity detected within activity_window seconds
        """
        self._clean_old_activities()
        return len(self.recent_activities) > 0
    
    def _clean_old_activities(self):
        """Remove activities older than activity_window."""
        cutoff = datetime.now() - timedelta(seconds=self.activity_window)
        
        while self.recent_activities and self.recent_activities[0] < cutoff:
            self.recent_activities.popleft()
    
    def _is_peak_hours(self) -> bool:
        """
        Check if current time is within peak hours (UTC).
        
        Returns:
            True if within peak hours
        """
        current_hour = datetime.utcnow().hour
        
        # Handle overnight peak hours (e.g., 22-02)
        if self.peak_start_hour < self.peak_end_hour:
            return self.peak_start_hour <= current_hour < self.peak_end_hour
        else:
            # Overnight case
            return current_hour >= self.peak_start_hour or current_hour < self.peak_end_hour
    
    def _is_prime_time(self) -> bool:
        """
        Check if current time is within EU prime time.
        
        Prime time windows:
        - Post-maintenance: Wednesday 10-14 UTC
        - Weekend prime: Friday 18-23 UTC
        - Weekend prime: Saturday 18-23 UTC
        
        Returns:
            True if within prime time
        """
        now = datetime.utcnow()
        day = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        
        # Post-maintenance window (Wednesday)
        if day == self.maintenance_day:
            start, end = self.maintenance_hours
            if start <= hour < end:
                return True
        
        # Weekend prime hours
        if day in self.weekend_prime:
            start, end = self.weekend_prime[day]
            if start <= hour < end:
                return True
        
        return False
    
    def set_peak_hours(self, start_hour: int, end_hour: int):
        """
        Set peak hours (UTC).
        
        Args:
            start_hour: Start hour (0-23, UTC)
            end_hour: End hour (0-23, UTC)
        """
        self.peak_start_hour = start_hour
        self.peak_end_hour = end_hour
    
    def get_stats(self) -> dict:
        """
        Get polling statistics.
        
        Returns:
            Dict with stats (uptime, polls, activity, current interval)
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        current_interval = self.get_interval()
        
        return {
            'uptime_seconds': uptime,
            'total_polls': self.total_polls,
            'activity_count': self.activity_count,
            'current_interval': current_interval,
            'is_peak_hours': self._is_peak_hours(),
            'is_prime_time': self._is_prime_time(),
            'has_recent_activity': self._has_recent_activity(),
            'avg_polls_per_hour': (self.total_polls / uptime * 3600) if uptime > 0 else 0
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.total_polls = 0
        self.activity_count = 0
        self.start_time = datetime.now()
        self.recent_activities.clear()

