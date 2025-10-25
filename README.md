# BDO Trading Tools v3

Python-basierte Trading-Assistenten für Black Desert Online Central Market mit **bdomarket** Library-Integration.

## 🎯 Features

### ✅ Implementiert (Phase 0-6 COMPLETE!)

- **✅ bdomarket Integration** - Nutzt existierende API-Library statt eigenem Client
- **✅ Item-Sniper** - Preis-Alarme für Watchlist-Items mit auto-fetched Item-Namen
- **✅ Portfolio-Tracker** - CSV-basiertes Trading-Log mit P&L-Berechnung + Live-Status
- **✅ Analysis-Engine** - Competition-Monitor, Market-Cycles, Heuristiken
- **✅ Enhanced Flip-Scanner** - Mit Item-Namen, Risk-Levels, Competition-Scores
- **✅ Flip-Optimizer** - Budget-Constraint-Optimierung mit Knapsack-Algorithm
- **✅ Pearl Sniper** - 1-2 Sekunden Pearl Item Detection mit NO TAX Extraction Profit

### 🔮 Future Extensions

- **Discord/Telegram Bot** - Remote notifications
- **Web-Dashboard** - Interactive UI
- **ML-Price-Predictor** - Machine Learning (needs 4+ weeks data)

## 📦 Installation

```bash
# Installiere Dependencies
pip install -r requirements.txt

# Kopiere Example-Config
cp config/sniper_watchlist.example.yaml config/sniper_watchlist.yaml

# Edit Config mit deinen gewünschten Items (IDs findest du auf bdocodex.com)
```

## 🚀 Usage

### 1. Item-Sniper

Überwacht Items und alertet bei Zielpreisen:

```bash
python sniper.py
```

### 2. Pearl Item Sniper 💎 NEW!

Speed-optimized monitoring für Pearl Items mit Extraction-Profitberechnung:

```bash
# Normal usage (runs 24/7)
python pearl_sniper.py

# Test mode with mock data
python pearl_sniper.py --test

# Dry run (no alerts)
python pearl_sniper.py --dry-run

# Background mode (Windows)
pythonw pearl_sniper.py
```

**What it does:**
- Detects Pearl Items within 1-2 seconds of listing
- Calculates extraction value (Cron Stones + Valks' Cry) with **NO TAX**
- Alerts on ANY positive profit margin
- Multi-channel notifications (Terminal, Toast, Discord)
- Adaptive polling (1s during peak hours, 2s normal)

**Example Output:**
```
🔥 PEARL ALERT! [Kibelius] Outfit Set (PREMIUM)
  Listed: 1.35B
  Extraction: 9.10B (993 Crons + 331 Valks)
  Profit: +7.75B (+574% ROI) ✓✓✓
  Time: 17:46:15 (ACT NOW!)
```

**Config (`config/pearl_sniper.yaml`):**
```yaml
region: eu
pearl_sniper:
  poll_interval: 2              # Base interval
  peak_hours_boost: true        # 1s during 18-22 UTC
  alert_threshold:
    minimum_profit: 100_000_000  # 100M
    minimum_roi: 0.05            # 5%
  notifications:
    terminal_beep: true
    windows_toast: true
    discord_webhook: null         # Optional webhook URL
```

**Pearl Extraction Values:**
- **Premium Outfit** (7 parts): 993 Cron + 331 Valks → ~9B value
- **Classic Outfit** (6 parts): 801 Cron + 267 Valks → ~7.3B value
- **Simple Outfit** (4 parts): 543 Cron + 181 Valks → ~5B value
- **Mount Gear**: ~900 Cron + ~300 Valks → ~8.3B value

**Why it's profitable:**
- Cron Stone NPC price: **3M** (reference)
- Cron Stone market price: ~2-2.5M (already cheaper)
- Extraction effective cost: **Even lower!** (~1.3-2.2M per Cron)
- **NO marketplace tax** on extraction (vs 65.5% tax on resale)

> **Note:** You're getting Crons at 27-55% cheaper than NPC price!

### 3. Portfolio-Tracker

Track deine Trades und P&L:

```bash
# Log trade (interactive - nicht im Automation-Context)
python portfolio.py log

# Show P&L report
python portfolio.py report

# Show live status with current prices
python portfolio.py status --live
```

### 4. Market Analyzer

Analyse Competition und Market-Timing:

```bash
# Competition analysis
python analyzer.py competition --items 16001,16002,16004

# Market timing
python analyzer.py timing
```

### 5. Enhanced Flip-Scanner

Scan für profitable Flips mit Intelligence:

```bash
python flip_scanner.py --max-items 100 --filter-risk LOW
```

### 6. Portfolio Optimizer

Optimiere Budget-Allocation:

```bash
python optimizer.py --budget 500000000 --max-positions 10 --filter-risk LOW
```

**Config (`config/sniper_watchlist.yaml`):**
```yaml
region: eu
poll_interval: 5

watchlist:
  - id: 16001  # Black Stone (Weapon)
    target_buy_max: 180000
    target_sell_min: 250000
    alert_on: both
```

**Output:**
```
🔔 ALERT! Black Stone
  ✓ BUY: 177K (Target: <180K) | +1.7%
  Potential ROI: -40.1%
```

## 🏗️ Architektur

```
BDO Trading Tools
    ├── bdomarket (PyPI)      # API-Client für arsha.io
    ├── MarketClient          # Wrapper für Abstraction
    ├── ItemHelper            # Caching & Fuzzy-Search
    └── Trading Tools
        ├── sniper.py         # Item-Sniper ✅
        ├── pearl_sniper.py   # Pearl Item Sniper ✅
        ├── portfolio.py      # Portfolio-Tracker ✅
        ├── analyzer.py       # Analysis-Engine ✅
        ├── flip_scanner.py   # Enhanced Flip-Scanner ✅
        └── optimizer.py      # Flip-Optimizer ✅
```

## 📁 Projekt-Struktur

```
bdo-trading-tools/
├── sniper.py                # Item-Sniper ✅
├── pearl_sniper.py          # Pearl Item Sniper ✅
├── portfolio.py             # Portfolio-Tracker ✅
├── analyzer.py              # Analysis-Engine ✅
├── flip_scanner.py          # Enhanced Flip-Scanner ✅
├── optimizer.py             # Flip-Optimizer ✅
├── main.py                  # Legacy Flip-Scanner
│
├── utils/
│   ├── market_client.py     # bdomarket Wrapper
│   ├── item_helper.py       # Item-Suche + Cache
│   ├── calculations.py      # ROI/Tax-Formeln
│   ├── storage.py           # File I/O
│   ├── pearl_calculator.py  # Pearl extraction calculator
│   ├── smart_poller.py      # Adaptive polling
│   └── pearl_alerts.py      # Multi-channel alerts
│
├── config/
│   ├── sniper_watchlist.yaml    # Item sniper config
│   └── pearl_sniper.yaml        # Pearl sniper config
│
├── data/
│   ├── portfolio.csv
│   ├── portfolio_settings.json
│   └── market_history/
│
├── tests/
│   └── test_pearl_mock.py   # Pearl sniper tests
│
└── requirements.txt
```

## 🔑 Key Design Decisions

**✅ Warum bdomarket?**
- ✅ Item-Namen automatisch verfügbar (kein manuelles Scraping)
- ✅ API-Client fertig & gepflegt (24 Releases)
- ✅ Boss Timer als Bonus-Feature
- ✅ Spart 50%+ Entwicklungszeit

**✅ Warum Wrapper-Layer?**
- ✅ Decoupling: Wenn bdomarket Probleme hat, nur 1 Datei ändern
- ✅ Konsistente API für alle Tools
- ✅ Einfacher zu testen

## 📚 Dependencies

```
bdomarket>=0.2.18     # BDO Market API
pyyaml>=6.0           # YAML Config
rapidfuzz>=3.0        # Fuzzy-Search
rich>=13.0            # Pretty CLI
pandas>=2.0           # Data-Analysis
win10toast>=0.9       # Windows notifications (Pearl Sniper)
aiohttp>=3.8          # Discord webhooks (Pearl Sniper)
```

## 🗺️ Roadmap

**✅ Phase 0-6 (COMPLETE!):**
- ✅ bdomarket Integration
- ✅ MarketClient Wrapper
- ✅ Item-Sniper mit auto-fetched Namen
- ✅ Portfolio-Tracker mit Live-Status
- ✅ Analysis-Engine (Competition + Timing)
- ✅ Enhanced Flip-Scanner mit Risk-Levels
- ✅ Flip-Optimizer mit Budget-Constraints
- ✅ Pearl Item Sniper mit NO TAX Extraction Profit

**🔮 Future (Optional):**
- Discord/Telegram Bot für Notifications
- Web-Dashboard für interactive UI
- ML-Price-Predictor (needs historical data)
- Auto-Trading Integration (risky!)

## 🚀 Advanced Data-Driven Market Advantage Strategies

Neue Analyse- und Automations-Features, die auf den bestehenden API- und Datapoints aufbauen, um gegenüber dem Markt einen strukturellen Vorteil zu erzielen:

### 1. Velocity & Momentum Radar
- **Datapoints:** `trade_count`, `total_trade_count`, `basePrice`, Zeitstempel
- **Ansatz:** Berechne Handelsgeschwindigkeit (Trades pro Minute) und deren Beschleunigung. Kombiniere sie mit kurzfristigen Preisänderungen, um Momentum-Phasen zu erkennen (Breakouts & Trendwenden).
- **Edge:** Frühzeitig in steigende Trends einsteigen und vor Momentum-Verlust wieder aussteigen.

### 2. Supply Shock Detector
- **Datapoints:** `stock`, `total_trade_count` in Intervallen, Historie
- **Ansatz:** Tracke Standardabweichung der Handelsaktivität. Alert, wenn Angebot oder Käufe um >2-3σ von der Norm abweichen (Massendumps, Hamsterkäufe).
- **Edge:** Crashs kaufen, künstliche Verknappung ausnutzen, bevor der Markt reagiert.

### 3. Cross-Item Correlation Signals
- **Datapoints:** Zeitreihen aller relevanten Items
- **Ansatz:** baue Korrelation/Lag-Matrizen (z. B. Grunil-Set, Alchemy-Mats). Wird ein Leit-Item aktiv, triggern Alerts für verzögert folgende Items.
- **Edge:** Preisbewegungen antizipieren, indem man Vorläufer misst und Nachzügler kauft.

### 4. Whale Activity Monitor
- **Datapoints:** Ordergrößen, Häufigkeit, `total_trade_count`
- **Ansatz:** Erkenne Ausreißer-Volumen (z. B. 3σ über Median). Speichere Whale-Profile (Item, Uhrzeit, Häufigkeit).
- **Edge:** "Smart Money" folgen oder dem Markt ausweichen, wenn dominierende Spieler aktiv werden.

### 5. Event-Driven Playbook
- **Datapoints:** Patch-Notes, Events, Roadmap + historische Preisreaktionen
- **Ansatz:** verknüpfe Kalender (Season Starts, Content Patches) mit Item-Historie. Lerne typische Vor- und Nachlaufzeiten.
- **Edge:** Pre-positioning vor Meta-Shifts (Buff/Nerf), gezielte Profit-Mitnahme kurz nach Events.

### 6. Market Depth & Price Wall Analytics
- **Datapoints:** Orderbuch (falls API verfügbar), Listings pro Preisstufe
- **Ansatz:** Identifiziere Preiswände, Liquiditätslücken, Buy-/Sell-Pressure-Ratio.
- **Edge:** Exakte Entry/Exit-Level, Erkennen wann Wände brechen und Trends beschleunigen.

### 7. Volatility Harvesting & Mean Reversion
- **Datapoints:** Rolling Preisfenster (z. B. 1h, 6h, 24h)
- **Ansatz:** Berechne Bollinger-Bänder/ATR. Kauf am unteren Band bei stabiler Nachfrage, Verkauf am oberen Band.
- **Edge:** Stetige Profite aus oszillierenden Items mit begrenztem Risiko.

### 8. Intelligent Alert Prioritization
- **Datapoints:** Alle oben genannten Metriken + bestehende Alerts
- **Ansatz:** Multiparameter-Scoring (Momentum + Volumen + Spread). Machine Learning zur Reduktion von False Positives über Feedback.
- **Edge:** Fokus auf die profitabelsten Chancen, weniger Alarm-Müdigkeit.

> **Implementation Hint:** Die meisten Strategien profitieren von einer Zeitseriendatenbank (z. B. SQLite/Parquet) + Batch/Streaming-Pipeline. Kombiniere existierende Module (MarketClient, Analyzer, Flip-Scanner) mit neuen Services für Metrikberechnung und Alert Routing (Discord/Telegram/Webhooks).

## 📖 Resources

- **bdomarket**: https://github.com/Fizzor96/bdomarket
- **Item IDs**: https://bdocodex.com/us/items/
- **Market Data**: https://garmoth.com/market
- **auciel (Referenz)**: https://github.com/jpegzilla/auciel

## 🤝 Contributing

Pull Requests willkommen! Für große Änderungen bitte erst ein Issue öffnen.

## 📝 License

MIT License - siehe LICENSE file

## 🙏 Credits

- **bdomarket** by Fizzor96 - API-Client
- **arsha.io** - Market API
- **Pearl Abyss** - Black Desert Online

## 🎓 Pearl Sniper - Quick Start

**1. Setup:**
```bash
pip install -r requirements.txt
python pearl_sniper.py --test  # Test with mock data
```

**2. Configure:**
Edit `config/pearl_sniper.yaml` to set thresholds and Discord webhook.

**3. Run 24/7:**
```bash
# Windows (background)
pythonw pearl_sniper.py

# Or as Windows Service (recommended)
nssm install PearlSniper "C:\Python312\pythonw.exe" "C:\path\to\pearl_sniper.py"
nssm start PearlSniper
```

**4. Expected Results:**
- Detection speed: 1-2 seconds after listing
- Coverage: 80-90% of listings
- Alert channels: Terminal + Windows Toast + Discord (optional)
- Resource usage: <5% CPU, ~50MB RAM

**Known Limitations:**
- Cannot guarantee purchase (high competition + 1-90s registration queue)
- bdomarket rate limits unknown (monitor for issues)
- Toast notifications require Windows 10+

---

**Status**: Phase 0-6 Complete ✅ | All Features Implemented Including Pearl Sniper! 🎉💎

