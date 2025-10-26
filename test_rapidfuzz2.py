#!/usr/bin/env python3
"""Test rapidfuzz with correct processor."""
from rapidfuzz import fuzz, process

# Test 1: Simple string list
print("=== Test 1: Simple strings ===")
choices1 = ["Black Stone (Weapon)", "Black Stone (Armor)", "Cron Stone"]
matches1 = process.extract("black stone", choices1, scorer=fuzz.WRatio, limit=3)
print(f"Matches: {len(matches1)}")
for match in matches1:
    print(f"  {match}")

# Test 2: Dict with processor
print("\n=== Test 2: Dict with custom processor ===")
choices2 = {
    16001: "Black Stone (Weapon)",
    16002: "Black Stone (Armor)",
    16004: "Cron Stone",
}
matches2 = process.extract(
    "black stone",
    choices2,
    scorer=fuzz.WRatio,
    limit=3,
    processor=lambda x: choices2[x]  # x is the key
)
print(f"Matches: {len(matches2)}")
for match in matches2:
    print(f"  {match}")

# Test 3: extractOne for single best match
print("\n=== Test 3: extractOne ===")
best = process.extractOne("black stone", choices1, scorer=fuzz.WRatio)
print(f"Best: {best}")

