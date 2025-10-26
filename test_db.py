#!/usr/bin/env python3
"""Quick test script for item database."""
from utils.item_db import get_item_db

db = get_item_db()
print(f"Items loaded: {db.size()}")

# Test search
results = db.search('black stone')
print(f"\nSearch test ('black stone'): {len(results)} results")
for item, score in results[:5]:
    print(f"  - {item.name} (ID: {item.id}, Score: {score:.1f})")

# Test by ID
test_id = 16001  # Common item
item = db.get_by_id(test_id)
if item:
    print(f"\nDirect ID lookup ({test_id}): {item.name}")
else:
    print(f"\nID {test_id} not found in database")

