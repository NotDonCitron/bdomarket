"""
Pearl Alert System - Multi-channel notifications for pearl item opportunities.

Supports:
- Terminal: Colored output with ASCII beep
- Windows Toast: Desktop notifications (win10toast)
- Discord Webhook: Rich embeds with item details

Priority Levels:
- CRITICAL: ROI >50% or Profit >5B
- HIGH: ROI 30-50% or Profit 2-5B
- NORMAL: Any positive profit
"""
from typing import Optional
from datetime import datetime
from enum import Enum
import sys
import asyncio
import json

try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class AlertPriority(Enum):
    """Alert priority levels."""
    CRITICAL = "critical"  # 🔥
    HIGH = "high"          # ⚡
    NORMAL = "normal"      # ✓


class PearlAlerter:
    """
    Multi-channel alert system for pearl item opportunities.
    
    Usage:
        alerter = PearlAlerter(
            terminal_enabled=True,
            toast_enabled=True,
            webhook_url="https://discord.com/..."
        )
        
        await alerter.send_alert(item_data, value_result)
    """
    
    def __init__(
        self,
        terminal_enabled: bool = True,
        terminal_beep: bool = True,
        toast_enabled: bool = True,
        webhook_url: Optional[str] = None
    ):
        """
        Initialize alerter.
        
        Args:
            terminal_enabled: Enable terminal output
            terminal_beep: Enable ASCII beep (\a)
            toast_enabled: Enable Windows toast notifications
            webhook_url: Discord webhook URL (optional)
        """
        self.terminal_enabled = terminal_enabled
        self.terminal_beep = terminal_beep
        self.toast_enabled = toast_enabled and TOAST_AVAILABLE
        self.webhook_url = webhook_url
        
        # Initialize components
        if self.toast_enabled:
            self.toaster = ToastNotifier()
        else:
            self.toaster = None
        
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
        
        # Statistics
        self.alerts_sent = 0
        self.alerts_by_priority = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 0,
            AlertPriority.NORMAL: 0
        }
    
    def _get_priority(self, value_result) -> AlertPriority:
        """
        Determine alert priority based on value result.
        
        Args:
            value_result: PearlValueResult object
            
        Returns:
            AlertPriority enum
        """
        profit = value_result.profit
        roi = value_result.roi
        
        # CRITICAL: ROI >50% or Profit >5B
        if roi > 0.5 or profit > 5_000_000_000:
            return AlertPriority.CRITICAL
        
        # HIGH: ROI 30-50% or Profit 2-5B
        if roi > 0.3 or profit > 2_000_000_000:
            return AlertPriority.HIGH
        
        # NORMAL: Any positive profit
        return AlertPriority.NORMAL
    
    def _format_silver(self, amount: int) -> str:
        """
        Format silver amount for display.
        
        Args:
            amount: Silver amount
            
        Returns:
            Formatted string (e.g., "2.17B", "450M", "50K")
        """
        if amount >= 1_000_000_000:
            return f"{amount / 1_000_000_000:.2f}B"
        elif amount >= 1_000_000:
            return f"{amount / 1_000_000:.0f}M"
        elif amount >= 1_000:
            return f"{amount / 1_000:.0f}K"
        else:
            return str(amount)
    
    def _get_priority_emoji(self, priority: AlertPriority) -> str:
        """Get emoji for priority level."""
        emoji_map = {
            AlertPriority.CRITICAL: "🔥",
            AlertPriority.HIGH: "⚡",
            AlertPriority.NORMAL: "✓"
        }
        return emoji_map.get(priority, "💎")
    
    async def send_alert(self, item_data: dict, value_result) -> bool:
        """
        Send alert through all enabled channels.
        
        Args:
            item_data: Dict with item info (id, name, price, etc.)
            value_result: PearlValueResult object
            
        Returns:
            True if at least one alert sent successfully
        """
        priority = self._get_priority(value_result)
        self.alerts_sent += 1
        self.alerts_by_priority[priority] += 1
        
        success = False
        
        # Terminal alert
        if self.terminal_enabled:
            self._send_terminal_alert(item_data, value_result, priority)
            success = True
        
        # Toast notification
        if self.toast_enabled and self.toaster:
            self._send_toast_alert(item_data, value_result, priority)
            success = True
        
        # Discord webhook
        if self.webhook_url:
            webhook_success = await self._send_discord_alert(item_data, value_result, priority)
            success = success or webhook_success
        
        return success
    
    def _send_terminal_alert(self, item_data: dict, value_result, priority: AlertPriority):
        """Send terminal alert with rich formatting."""
        emoji = self._get_priority_emoji(priority)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Build alert message
        item_name = item_data.get('name', 'Unknown Item')
        item_id = item_data.get('id', 0)
        
        market_price_str = self._format_silver(value_result.market_price)
        extraction_value_str = self._format_silver(value_result.extraction_value)
        profit_str = self._format_silver(value_result.profit)
        roi_str = f"{value_result.roi * 100:.1f}%"
        
        # Beep for high-priority alerts
        if self.terminal_beep and priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]:
            sys.stdout.write('\a')
            sys.stdout.flush()
        
        if self.console and RICH_AVAILABLE:
            # Rich formatted output
            priority_colors = {
                AlertPriority.CRITICAL: "red",
                AlertPriority.HIGH: "yellow",
                AlertPriority.NORMAL: "green"
            }
            color = priority_colors.get(priority, "white")
            
            title = f"{emoji} PEARL ALERT! {item_name} ({value_result.outfit_type.upper()})"
            
            content = (
                f"[bold]Listed:[/bold] {market_price_str}\n"
                f"[bold]Extraction:[/bold] {extraction_value_str} "
                f"({value_result.cron_stones} Crons + {value_result.valks_cry} Valks)\n"
                f"[bold]Profit:[/bold] +{profit_str} (+{roi_str} ROI) ✓✓✓\n"
                f"[bold]Time:[/bold] {timestamp} (ACT NOW!)\n"
                f"[bold]Item ID:[/bold] {item_id}"
            )
            
            panel = Panel(
                content,
                title=title,
                border_style=color,
                expand=False
            )
            
            self.console.print(panel)
        else:
            # Fallback: plain text
            print(f"\n{emoji} PEARL ALERT! [{timestamp}]")
            print(f"  Item: {item_name} ({value_result.outfit_type.upper()})")
            print(f"  Listed: {market_price_str}")
            print(f"  Extraction: {extraction_value_str}")
            print(f"  Profit: +{profit_str} (+{roi_str} ROI)")
            print(f"  Time: {timestamp} (ACT NOW!)")
            print()
    
    def _send_toast_alert(self, item_data: dict, value_result, priority: AlertPriority):
        """Send Windows toast notification."""
        if not self.toaster:
            return
        
        try:
            emoji = self._get_priority_emoji(priority)
            item_name = item_data.get('name', 'Unknown Item')
            profit_str = self._format_silver(value_result.profit)
            roi_str = f"{value_result.roi * 100:.0f}%"
            
            title = f"{emoji} Pearl Alert: {item_name}"
            message = f"Profit: +{profit_str} (+{roi_str})\nACT NOW!"
            
            # Non-blocking toast
            self.toaster.show_toast(
                title=title,
                msg=message,
                duration=10,  # 10 seconds
                threaded=True  # Non-blocking
            )
        except Exception as e:
            print(f"Toast notification error: {e}")
    
    async def _send_discord_alert(
        self,
        item_data: dict,
        value_result,
        priority: AlertPriority
    ) -> bool:
        """
        Send Discord webhook alert.
        
        Args:
            item_data: Item data dict
            value_result: PearlValueResult object
            priority: AlertPriority enum
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            return False
        
        try:
            import aiohttp
            
            # Color codes by priority
            color_map = {
                AlertPriority.CRITICAL: 0xFF0000,  # Red
                AlertPriority.HIGH: 0xFFAA00,      # Orange
                AlertPriority.NORMAL: 0x00FF00     # Green
            }
            color = color_map.get(priority, 0x00AAFF)
            
            emoji = self._get_priority_emoji(priority)
            item_name = item_data.get('name', 'Unknown Item')
            item_id = item_data.get('id', 0)
            
            # Build embed
            embed = {
                "title": f"{emoji} Pearl Alert: {item_name}",
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "Outfit Type",
                        "value": value_result.outfit_type.upper(),
                        "inline": True
                    },
                    {
                        "name": "Market Price",
                        "value": self._format_silver(value_result.market_price),
                        "inline": True
                    },
                    {
                        "name": "Extraction Value",
                        "value": self._format_silver(value_result.extraction_value),
                        "inline": True
                    },
                    {
                        "name": "Profit",
                        "value": f"+{self._format_silver(value_result.profit)}",
                        "inline": True
                    },
                    {
                        "name": "ROI",
                        "value": f"+{value_result.roi * 100:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "Extraction",
                        "value": f"{value_result.cron_stones} Crons + {value_result.valks_cry} Valks",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Item ID: {item_id} | ACT NOW!"
                }
            }
            
            payload = {
                "embeds": [embed],
                "username": "Pearl Sniper"
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 204
                    
        except Exception as e:
            print(f"Discord webhook error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get alerter statistics.
        
        Returns:
            Dict with alert counts by priority
        """
        return {
            'total_alerts': self.alerts_sent,
            'critical': self.alerts_by_priority[AlertPriority.CRITICAL],
            'high': self.alerts_by_priority[AlertPriority.HIGH],
            'normal': self.alerts_by_priority[AlertPriority.NORMAL]
        }

