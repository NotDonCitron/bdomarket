import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PearlItem:
    """Data class for Pearl shop item information"""
    item_id: str
    name: str
    category: str
    price: int
    listed_time: datetime
    extraction_value: int = 0
    profit_margin: float = 0.0
    roi: float = 0.0

class PearlCalculator:
    """Calculate extraction values and profit margins for Pearl items"""
    
    # Extraction values (based on BDO extraction mechanics)
    EXTRACTION_VALUES = {
        "premium_outfit": {
            "cron_stones": 993,
            "valks_cry": 331,
            "total_value": 9_100_000_000  # ~9.1B
        },
        "classic_outfit": {
            "cron_stones": 801,
            "valks_cry": 267,
            "total_value": 7_300_000_000  # ~7.3B
        },
        "simple_outfit": {
            "cron_stones": 543,
            "valks_cry": 181,
            "total_value": 5_000_000_000  # ~5B
        },
        "mount_gear": {
            "cron_stones": 900,
            "valks_cry": 300,
            "total_value": 8_300_000_000  # ~8.3B
        }
    }
    
    @classmethod
    def categorize_item(cls, item_name: str, category: str) -> str:
        """Categorize item based on name and category"""
        item_name_lower = item_name.lower()
        
        if "outfit" in item_name_lower or "costume" in item_name_lower:
            if "premium" in item_name_lower or "kibelius" in item_name_lower:
                return "premium_outfit"
            elif "classic" in item_name_lower:
                return "classic_outfit"
            else:
                return "simple_outfit"
        elif "mount" in item_name_lower or "horse" in item_name_lower:
            return "mount_gear"
        
        return "simple_outfit"  # Default fallback
    
    @classmethod
    def calculate_extraction_value(cls, item: PearlItem) -> int:
        """Calculate extraction value for a Pearl item"""
        item_type = cls.categorize_item(item.name, item.category)
        return cls.EXTRACTION_VALUES.get(item_type, cls.EXTRACTION_VALUES["simple_outfit"])["total_value"]
    
    @classmethod
    def calculate_profit_metrics(cls, item: PearlItem) -> PearlItem:
        """Calculate profit margin and ROI for a Pearl item"""
        extraction_value = cls.calculate_extraction_value(item)
        item.extraction_value = extraction_value
        
        # Profit = extraction value - purchase price (no tax on extraction)
        profit = extraction_value - item.price
        item.profit_margin = profit
        
        # ROI = profit / purchase price
        if item.price > 0:
            item.roi = profit / item.price
        else:
            item.roi = 0.0
        
        return item