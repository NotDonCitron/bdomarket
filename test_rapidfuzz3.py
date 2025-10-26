#!/usr/bin/env python3
"""Test with actual item database structure."""
from rapidfuzz import fuzz, process

# Simulate actual database structure
choices = {
    16001: "Black Stone (Weapon)",
    16002: "Black Stone (Armor)",
    16004: "Cron Stone",
    123: "Item_123",
    456: "Item_456",
}

print(f"Choices: {len(choices)} items")
print(f"Sample: {list(choices.items())[:3]}")

query = "black stone"
print(f"\nQuery: '{query}'")

try:
    matches = process.extract(
        query,
        choices,
        scorer=fuzz.WRatio,
        limit=5,
        score_cutoff=60
    )
    print(f"Matches: {len(matches)}")
    for match in matches:
        print(f"  {match}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

