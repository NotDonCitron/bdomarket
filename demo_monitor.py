#!/usr/bin/env python3
"""
Simple demo script to show Pearl extraction profitability calculations
without requiring any external services or authentication.
"""

from datetime import datetime
from dataclasses import dataclass
from typing import List

from utils.pearl_calculator import PearlValueCalculator
from utils.market_client import MarketClient


@dataclass
class DemoItem:
    name: str
    outfit_type: str  # premium | classic | simple | mount
    price: int


def print_header(title: str) -> None:
    print("=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    print_header("BDO Pearl Extraction - Demo")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize market client and calculator
    market_client = MarketClient()
    calculator = PearlValueCalculator(market_client)

    # Fetch Cron/Valks prices (uses API; cached by calculator)
    import asyncio
    success = asyncio.run(calculator.update_prices(force=True))

    if not success:
        # Fallback to sample prices if live fetch fails
        calculator.cron_price = 3_000_000
        calculator.valks_price = 2_500_000
        print("Using fallback sample prices -> Cron: 3,000,000 | Valks: 2,500,000")
    else:
        price_info = calculator.get_price_info()
        print(
            f"Using prices -> Cron: {price_info['cron_price']:,} | Valks: {price_info['valks_price']:,}"
        )

    demo_items: List[DemoItem] = [
        DemoItem("Kibelius Outfit Set (PREMIUM)", "premium", 1_350_000_000),
        DemoItem("Classic Outfit Set", "classic", 980_000_000),
        DemoItem("Simple Outfit", "simple", 650_000_000),
        DemoItem("Mount Gear Package", "mount", 1_200_000_000),
    ]

    for item in demo_items:
        result = calculator.calculate_value(item.outfit_type, item.price)
        if not result:
            print(f"Could not calculate value for: {item.name}")
            continue

        print()
        print(f"Item: {item.name}")
        print(
            f"   Listed: {result.market_price:,} | Extraction: {result.extraction_value:,}"
        )
        print(
            f"   Profit: {result.profit:+,} ({result.roi:+.1%} ROI)"
        )
        if result.is_profitable:
            print("   PROFITABLE OPPORTUNITY!")
        else:
            print("   Not profitable enough")

    print()
    print("Demo completed!")


if __name__ == "__main__":
    main()
