#!/usr/bin/env python3
"""Debug item database search."""
from utils.item_db import ItemDatabase

db = ItemDatabase()
db.load()

print(f"Items: {db.size()}")
print(f"Cache size: {len(db._name_cache)}")

# Manual search test
item = db.get_by_id(16001)
if item:
    print(f"\nItem 16001: {item.name}")
    print(f"In cache? {item.name.lower() in db._name_cache}")

# Try exact match
exact = db.get_by_name_exact("Black Stone (Weapon)")
print(f"\nExact match 'Black Stone (Weapon)': {exact}")

# Debug fuzzy search
print("\nTrying fuzzy search...")
results = db.search("black", limit=5, min_score=50)
print(f"Results: {len(results)}")
for item, score in results:
    print(f"  - {item.name} [{score:.1f}]")

