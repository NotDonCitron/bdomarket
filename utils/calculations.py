"""
Tax, ROI, and profit calculations for BDO trading.
"""
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class TaxConfig:
    """Tax configuration for profit calculations."""
    base_tax: float = 0.35  # 35% base tax
    value_pack: bool = False  # Value Pack reduces tax
    familia_fame_bonus: float = 0.0  # Familia Fame trading bonus (e.g., 0.015 = 1.5%)
    
    @property
    def effective_tax(self) -> float:
        """Calculate effective tax rate after bonuses."""
        tax = self.base_tax
        
        # Value Pack reduces tax by 30%
        if self.value_pack:
            tax = tax * 0.7  # 35% * 0.7 = 24.5%
        
        # Familia Fame bonus (additive reduction)
        tax = max(0.0, tax - self.familia_fame_bonus)
        
        return tax


def calculate_effective_tax(
    base_tax: float = 0.35,
    value_pack: bool = False,
    familia_fame_bonus: float = 0.0
) -> float:
    """
    Calculate effective tax rate after all bonuses.
    
    Args:
        base_tax: Base marketplace tax (default: 35%)
        value_pack: Whether user has Value Pack active
        familia_fame_bonus: Trading bonus from Familia Fame (e.g., 0.015 for 1.5%)
        
    Returns:
        Effective tax rate as decimal (e.g., 0.245 for 24.5%)
        
    Example:
        >>> calculate_effective_tax(value_pack=True, familia_fame_bonus=0.015)
        0.23  # 35% * 0.7 - 1.5% = 23%
    """
    config = TaxConfig(base_tax=base_tax, value_pack=value_pack, familia_fame_bonus=familia_fame_bonus)
    return config.effective_tax


def calculate_profit(
    buy_price: int,
    sell_price: int,
    quantity: int = 1,
    tax_rate: Optional[float] = None,
    tax_config: Optional[TaxConfig] = None
) -> int:
    """
    Calculate profit after taxes.
    
    Args:
        buy_price: Price paid per unit
        sell_price: Price received per unit (before tax)
        quantity: Number of items
        tax_rate: Effective tax rate (overrides tax_config if provided)
        tax_config: TaxConfig object (if tax_rate not provided)
        
    Returns:
        Total profit in silver
        
    Example:
        >>> calculate_profit(1000000, 1500000, quantity=10, tax_rate=0.35)
        2250000  # (1.5M * 0.65 - 1M) * 10
    """
    if tax_rate is None:
        if tax_config is None:
            tax_config = TaxConfig()
        tax_rate = tax_config.effective_tax
    
    sell_after_tax = sell_price * (1 - tax_rate)
    profit_per_unit = sell_after_tax - buy_price
    
    return int(profit_per_unit * quantity)


def calculate_roi(
    buy_price: int,
    sell_price: int,
    tax_rate: Optional[float] = None,
    tax_config: Optional[TaxConfig] = None
) -> float:
    """
    Calculate Return on Investment (ROI) as percentage.
    
    Args:
        buy_price: Price paid per unit
        sell_price: Price received per unit (before tax)
        tax_rate: Effective tax rate (overrides tax_config if provided)
        tax_config: TaxConfig object (if tax_rate not provided)
        
    Returns:
        ROI as decimal (e.g., 0.25 for 25%)
        
    Example:
        >>> calculate_roi(1000000, 1500000, tax_rate=0.35)
        -0.025  # (1.5M * 0.65 - 1M) / 1M = -2.5% (loss!)
    """
    if buy_price <= 0:
        return 0.0
    
    profit = calculate_profit(buy_price, sell_price, quantity=1, tax_rate=tax_rate, tax_config=tax_config)
    return profit / buy_price


def find_flip_opportunity(
    orders: List,  # List of OrderLevel objects
    tax_rate: float = 0.35
) -> Optional[Tuple[int, int, float, float]]:
    """
    Find flip opportunity from orderbook.
    
    Args:
        orders: List of OrderLevel objects (must have price, buyers, sellers attributes)
        tax_rate: Effective tax rate
        
    Returns:
        Tuple of (buy_price, sell_price, profit, roi) or None if no opportunity
        
    Example:
        >>> orders = [OrderLevel(1000000, 5, 10), OrderLevel(1500000, 2, 0)]
        >>> find_flip_opportunity(orders, tax_rate=0.35)
        (1000000, 1500000, -25000, -0.025)
    """
    if not orders:
        return None
    
    # Find lowest ask (sellers > 0) and highest bid (buyers > 0)
    lowest_sell = None
    highest_buy = None
    
    for order in orders:
        if order.sellers > 0:
            if lowest_sell is None or order.price < lowest_sell:
                lowest_sell = order.price
        if order.buyers > 0:
            if highest_buy is None or order.price > highest_buy:
                highest_buy = order.price
    
    if lowest_sell is None or highest_buy is None:
        return None
    
    profit = calculate_profit(lowest_sell, highest_buy, quantity=1, tax_rate=tax_rate)
    roi = calculate_roi(lowest_sell, highest_buy, tax_rate=tax_rate)
    
    return (lowest_sell, highest_buy, profit, roi)


def format_silver(amount: int) -> str:
    """
    Format silver amount for display.
    
    Args:
        amount: Silver amount
        
    Returns:
        Formatted string (e.g., "1.25M", "850K", "1,234")
        
    Example:
        >>> format_silver(1250000)
        '1.25M'
        >>> format_silver(850000)
        '850K'
        >>> format_silver(1234)
        '1,234'
    """
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f}M".rstrip('0').rstrip('.')
    elif amount >= 1_000:
        return f"{amount / 1_000:.0f}K"
    else:
        return f"{amount:,}"


def format_percentage(value: float) -> str:
    """
    Format percentage for display.
    
    Args:
        value: Decimal value (e.g., 0.25 for 25%)
        
    Returns:
        Formatted string (e.g., "25.0%", "-2.5%")
        
    Example:
        >>> format_percentage(0.2534)
        '25.3%'
    """
    return f"{value * 100:+.1f}%"

