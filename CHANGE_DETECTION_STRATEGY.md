# BDO Pearl Monitor - Change Detection Strategy

## Problem
Polling zeigt immer "leer" weil Pearl Items extrem selten sind. Wir brauchen eine bessere Strategie um zu erkennen WANN ein neues Item gelistet wird.

## Lösungsansätze

### ✅ Option 1: Wait List API (EMPFOHLEN)
**Konzept:** BDO hat einen "Wird registriert" Endpoint der Items zeigt die gerade gelistet werden

**Vorteile:**
- Offizielle API (`GetWorldMarketWaitList`)
- Zeigt Items die GERADE gelistet wurden (wartet auf Käufer)
- Viel höhere Trefferquote als leere Kategorien
- Bereits im Code vorhanden (`test_hot_list.py`)

**API:**
```python
URL_WAIT_LIST = "https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketWaitList"
# Response: {"waitList": [...]} mit allen wartenden Items
```

**Implementierung:**
1. Parallel zu Pearl-Kategorien auch Wait List abfragen
2. Filtern nach `mainCategory == 55` (nur Pearl Items)
3. Alert bei jedem neuen Pearl Item in Wait List

---

### ✅ Option 2: Change Detection (Hash-basiert)
**Konzept:** Speichere Hash der kompletten marketList, erkenne Änderungen

**Vorteile:**
- Erkennt JEDE Änderung (neue Items, Stock-Änderungen)
- Funktioniert für alle Kategorien
- Keine falschen Positives

**Implementierung:**
```python
import hashlib

def compute_hash(market_list):
    # Sortiere Items und erstelle Hash
    items_str = json.dumps(sorted(market_list, key=lambda x: x['mainKey']))
    return hashlib.md5(items_str.encode()).hexdigest()

# Pro Kategorie:
new_hash = compute_hash(items)
if new_hash != last_hash[category]:
    print("ÄNDERUNG ERKANNT!")
    last_hash[category] = new_hash
```

---

### ✅ Option 3: Browser DevTools Network Listener
**Konzept:** Im Browser die Pearl-Seiten offen halten und auf XHR-Responses lauschen

**Vorteile:**
- Cookies/Token automatisch aktuell
- Sieht echte Browser-Requests
- Kann visuelle Änderungen erkennen

**Implementierung:**
- Playwright/Selenium hält Tabs offen
- Network listener auf `GetWorldMarketList` Responses
- Bei Änderung → Alert

**Problem:** Ressourcen-intensiv (Browser im Hintergrund)

---

### ✅ Option 4: Differential Detection
**Konzept:** Speichere komplette Item-Liste, vergleiche bei jedem Loop

**Vorteile:**
- Zeigt genau WAS sich geändert hat (neues Item, mehr Stock, etc.)
- Sehr präzise Alerts

**Implementierung:**
```python
last_items = {}  # {category: {mainKey: item_data}}

for category, items in results:
    current_keys = {item['mainKey'] for item in items}
    last_keys = set(last_items.get(category, {}).keys())
    
    # Neue Items
    new_keys = current_keys - last_keys
    if new_keys:
        for key in new_keys:
            print(f"NEUES ITEM: {key}")
    
    # Verschwundene Items (ausverkauft)
    removed_keys = last_keys - current_keys
    
    # Update state
    last_items[category] = {item['mainKey']: item for item in items}
```

---

## 🎯 EMPFOHLENE STRATEGIE

### Kombination: Wait List + Differential Detection

**Phase 1: Wait List Monitoring**
- Fokus auf `GetWorldMarketWaitList`
- Filter: Nur Pearl Items (`mainCategory == 55`)
- Catch Items die GERADE gelistet wurden

**Phase 2: Pearl Category Differential**
- Parallel dazu normale Pearl-Kategorien
- Differential Detection (vorher/nachher Vergleich)
- Erkennt wenn Item von Wait List → verfügbar wechselt

**Phase 3: Alert-System**
- Bei neuem Item in Wait List: "🟡 Item wird registriert"
- Bei neuem Item in Kategorie: "🟢 Item verfügbar!"
- Bei Stock-Änderung: "📊 Stock Update"

---

## Implementierungs-Plan

### Schritt 1: Wait List Integration
```python
async def fetch_wait_list(client, token):
    response = await client.post(URL_WAIT_LIST, data={"__RequestVerificationToken": token})
    data = response.json()
    
    pearl_items = []
    if isinstance(data.get("waitList"), list):
        for item in data["waitList"]:
            if item.get("mainCategory") == 55:  # Nur Pearl Items
                pearl_items.append(item)
    
    return pearl_items
```

### Schritt 2: Differential State
```python
class MarketState:
    def __init__(self):
        self.category_items = {}  # {category_id: {mainKey: item}}
        self.wait_list_items = {}  # {mainKey: item}
    
    def update_category(self, category_id, items):
        old_keys = set(self.category_items.get(category_id, {}).keys())
        new_keys = {item['mainKey'] for item in items}
        
        added = new_keys - old_keys
        removed = old_keys - new_keys
        
        self.category_items[category_id] = {item['mainKey']: item for item in items}
        return added, removed
```

### Schritt 3: Enhanced Monitor
```python
async def monitor_loop_enhanced(client, token, interval):
    state = MarketState()
    
    while True:
        # Parallel: Wait List + Pearl Categories
        tasks = [
            fetch_wait_list(client, token),
            *[fetch_category(client, token, cat) for cat in PEARL_CATEGORIES]
        ]
        
        results = await asyncio.gather(*tasks)
        wait_items = results[0]
        category_results = results[1:]
        
        # Check Wait List for new Pearl Items
        for item in wait_items:
            key = item['mainKey']
            if key not in state.wait_list_items:
                print(f"🟡 NEUES PEARL ITEM wird registriert: {item['name']}")
                state.wait_list_items[key] = item
        
        # Check Categories for changes
        for category, items in category_results:
            added, removed = state.update_category(category['subCategory'], items)
            
            for key in added:
                item = next(it for it in items if it['mainKey'] == key)
                print(f"🟢 PEARL ITEM VERFÜGBAR: {item['name']} (Stock: {item['sumCount']})")
            
            for key in removed:
                print(f"🔴 AUSVERKAUFT: mainKey={key}")
        
        await asyncio.sleep(interval)
```

---

## 📊 Erwartete Verbesserungen

| Strategie | Trefferquote | False Positives | Latenz |
|-----------|--------------|-----------------|--------|
| Nur Kategorien (aktuell) | Niedrig | 0% | ~0.3s |
| + Wait List | **Hoch** | 0% | ~0.3s |
| + Differential | **Sehr hoch** | 0% | ~0.3s |
| + Hash Detection | **100%** | 0% | ~0.3s |

---

## Nächste Schritte

1. ✅ Wait List API testen
2. ✅ Differential Detection implementieren  
3. ✅ Enhanced Monitor mit beiden Features
4. ✅ Über Nacht testen

---

## Test-Kommandos

```bash
# Test Wait List API
python -c "
import asyncio
import httpx
import json

async def test():
    auth = json.load(open('config/trader_auth.json'))
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://eu-trade.naeu.playblackdesert.com/Home/GetWorldMarketWaitList',
            data={'__RequestVerificationToken': auth['request_verification_token']},
            headers={'cookie': auth['cookie']}
        )
        print(resp.json())

asyncio.run(test())
"

# Enhanced Monitor starten
python pearl_monitor_enhanced.py --interval 0.5
```

