# 🚀 BDO Pearl Monitor - Schnellstart

## Installation (Einmalig)

```bash
pip install "httpx[http2]>=0.27.0"
```

## Nutzung

### 1. Standard-Modus (Empfohlen)
```bash
python pearl_monitor_parallel.py --interval 0.2
```
- **Sehr schnell** (200ms pro Loop)
- Alle 8 Pearl-Kategorien parallel
- HTTP/2 + Keep-Alive

### 2. Schneller Modus (Aggressiv)
```bash
python pearl_monitor_parallel.py --interval 0.1
```
- **Ultra-schnell** (100ms pro Loop)
- ⚠️ Vorsicht vor Rate-Limits!

### 3. Long-Running (Über Nacht)
```bash
run_pearl_monitor_longrun.cmd
```
Oder manuell:
```bash
python pearl_monitor_parallel.py --interval 5.0 > monitor.log 2>&1
```
- **Schonend** (5s Intervall)
- Log-Datei für Auswertung

### 4. Mit Hot List (Testing)
```bash
python pearl_monitor_test.py --interval 0.5
```
- Zeigt auch "Schwankende Preise" Items
- Gut zum Testen ob Monitoring funktioniert

---

## ⚙️ Konfiguration

### Auth-Daten aktualisieren

Wenn `401/403` Fehler auftreten:

1. Browser DevTools öffnen (F12)
2. Network-Tab → Refresh marketplace page
3. Request finden (`GetWorldMarketList`)
4. Copy → Copy as cURL
5. Extrahiere:
   - `Cookie:` Header
   - `User-Agent:` Header  
   - `__RequestVerificationToken` aus Request Body

6. Eintragen in `config/trader_auth.json`:
```json
{
  "cookie": "HIER_COOKIE_STRING",
  "user_agent": "HIER_USER_AGENT",
  "request_verification_token": "HIER_TOKEN"
}
```

---

## 📊 Was wird überwacht?

**8 Pearl-Kategorien:**
1. Männliche Outfits (Set)
2. Weibliche Outfits (Set)
3. Männliche Outfits (Einzel)
4. Weibliche Outfits (Einzel)
5. Klassen-Outfits (Set)
6. Funktional (Tiere, Elixiere etc.)
7. Reittiere (Pferdeausrüstung)
8. Begleiter (Pets)

**Alle gleichzeitig!** (Parallel, nicht sequentiell)

---

## 🎯 Output-Beispiel

```
[2025-10-25 22:30:15] Loop #42 | 0.31s | ✓ leer
[2025-10-25 22:30:20] Loop #43 | 0.29s | ✓ leer

============================================================
🚨🚨🚨 NEUER ARTIKEL GEFUNDEN! 🚨🚨🚨
============================================================
Kategorie: Begleiter (Pets)
Name: [Event] Junger Goldener Löwe
Verfügbarkeit: 3
Item-ID (mainKey): 336037
Preis: 3200000000
============================================================

[2025-10-25 22:30:25] Loop #44 | 0.33s | ✨ 1 NEU
```

---

## 🛠️ Troubleshooting

### "Auth failed (401/403)"
→ Cookie/Token abgelaufen, siehe "Auth-Daten aktualisieren" oben

### "ImportError: 'h2' package not installed"
→ `pip install "httpx[http2]"`

### Zu viele Items werden gemeldet
→ Erhöhe `--interval` (z.B. 1.0 oder 5.0)

### Keine Items gefunden
→ Pearl Items sind selten! Nutze `pearl_monitor_test.py` mit Hot List zum Testen

---

## 📁 Dateien

| Datei | Beschreibung |
|-------|-------------|
| `pearl_monitor_parallel.py` | **Hauptskript** (Produktion) |
| `pearl_monitor_test.py` | Test-Version mit Hot List |
| `config/trader_auth.json` | Auth-Daten |
| `run_pearl_monitor_longrun.cmd` | Long-Running Helper |
| `MONITOR_TEST_RESULTS.md` | Ausführliche Test-Dokumentation |

---

## ⚡ Performance

- **8× schneller** als sequentielles Polling
- HTTP/2 Multiplexing + Keep-Alive
- Loop-Zeit: 0.2-0.5s (bei 200ms Latenz)
- Deduplizierung verhindert Spam

**Viel Erfolg beim Pearl-Sniping!** 🎯


