#!/usr/bin/env python3
"""Test rapidfuzz to understand its output format."""
from rapidfuzz import fuzz, process

choices = [
    ("Black Stone (Weapon)", 16001),
    ("Black Stone (Armor)", 16002),
    ("Cron Stone", 16004),
    ("Item_123", 123),
]

query = "black stone"
matches = process.extract(
    query,
    choices,
    scorer=fuzz.WRatio,
    limit=5,
    score_cutoff=60
)

print(f"Query: '{query}'")
print(f"Matches type: {type(matches)}")
print(f"Number of matches: {len(matches)}")
print("\nMatch structure:")
for i, match in enumerate(matches):
    print(f"  [{i}] Type: {type(match)}, Length: {len(match)}")
    print(f"      Content: {match}")
    print(f"      Parts: {match[0]}, {match[1]}, {match[2]}")

