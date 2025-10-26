# 🔐 BDO Pearl Monitor - Manual Login Guide

## Problem: Browser schließt sich vor Steam-Login

**Grund:** Playwright startet Browser und öffnet sofort alle Tabs, aber du bist noch nicht eingeloggt.

**Lösung:** Manual Login Mode - Browser wartet bis du eingeloggt bist!

---

## 🚀 Nutzung - Manual Login Mode

### Option 1: Mit Batch-File (Einfachste)

```bash
run_pearl_browser_manual.cmd
```

### Option 2: Direkt

```bash
python pearl_monitor_browser.py --manual-login
```

---

## 📋 Ablauf Schritt-für-Schritt

### 1. Start

```
C:\...\bdo marketplace tool> run_pearl_browser_manual.cmd

======================================================================
🌐 BDO PEARL MONITOR - BROWSER MODE
======================================================================
...
Starte Browser...

======================================================================
⚠️  MANUAL LOGIN MODE
======================================================================
1. Browser öffnet sich
2. Logge dich über Steam ein
3. Navigiere zu einer beliebigen Pearl-Kategorie
4. Drücke ENTER hier im Terminal wenn du eingeloggt bist
======================================================================

Drücke ENTER nachdem du eingeloggt bist: _
```

### 2. Browser öffnet sich

- Chromium-Fenster erscheint
- Zeigt BDO Marketplace Homepage
- **WICHTIG:** Browser bleibt offen, wartet auf dich!

### 3. Du loggst dich ein

**Im Browser:**
1. Klicke auf "Login" Button
2. Wähle "Steam"
3. Steam-Login-Fenster öffnet sich
4. Logge dich ein
5. Warte bis du wieder auf der Marketplace-Seite bist

### 4. Bestätige im Terminal

**Zurück zum Terminal:**
- Drücke **ENTER**

### 5. Monitoring startet

```
Opening Männliche Outfits (Set)...
  ✅ Männliche Outfits (Set) monitoring active
Opening Weibliche Outfits (Set)...
  ✅ Weibliche Outfits (Set) monitoring active
...

======================================================================
✅ MONITORING AKTIV!
======================================================================
Tabs offen: 8
Drücke STRG+C zum Beenden

Warte auf Pearl Items...
======================================================================

[22:45:12] 🔍 Monitoring läuft... (8 Tabs aktiv)
```

---

## 🎯 Vorteile - Manual Login

### ✅ Keine Cookie-Probleme
- Kein manuelles Kopieren von Cookies nötig
- Kein `config/trader_auth.json` erforderlich
- Browser managed Session selbst

### ✅ Langlebige Session
- Steam-Login bleibt gültig
- Keine Token-Erneuerung nötig
- Läuft stundenlang

### ✅ Einfacher
- Kein DevTools öffnen
- Keine Request-Headers kopieren
- Einfach einloggen und los!

---

## 🆚 Vergleich: Manual vs. Cookie-basiert

| Feature | Manual Login | Cookie-basiert |
|---------|--------------|----------------|
| Setup | Login im Browser | Cookies aus DevTools |
| Session-Dauer | Stunden/Tage | Bis Cookie expires |
| Wartung | Keine | Token erneuern |
| Start-Zeit | +30s (Login) | Sofort |
| **Empfohlen für** | **Erste Nutzung** | Fortgeschrittene |

---

## 🔄 Workflow

### Erstes Mal / Neue Session

```bash
run_pearl_browser_manual.cmd
# → Einloggen
# → Monitor läuft
```

### Nächstes Mal (Session noch gültig)

```bash
# Option A: Weiter manual (einfach)
run_pearl_browser_manual.cmd

# Option B: Cookies speichern für schnelleren Start
# (siehe unten)
```

---

## 💡 Optional: Cookies für späteren Gebrauch speichern

Wenn du willst kannst du nach Manual Login die Cookies speichern:

### Im Browser (nach Login):

1. F12 (DevTools öffnen)
2. Application Tab
3. Cookies → `https://eu-trade.naeu.playblackdesert.com`
4. Kopiere alle Cookies als String

### In `config/trader_auth.json`:

```json
{
  "cookie": "DEINE_KOPIERTEN_COOKIES",
  "user_agent": "Mozilla/5.0 ..."
}
```

### Dann kannst du später nutzen:

```bash
# Schneller Start mit gespeicherten Cookies
python pearl_monitor_browser.py
```

**Aber:** Nicht nötig! Manual Login ist genauso gut.

---

## 🛠️ Troubleshooting

### Browser schließt sich sofort

**Problem:** Du drückst ENTER bevor du eingeloggt bist

**Lösung:** 
1. Restart Script
2. Warte bis Login komplett ist
3. **Dann erst** ENTER drücken

### "Login Required" in Tabs

**Problem:** Session ist expired

**Lösung:**
1. STRG+C (Monitor stoppen)
2. Restart mit `run_pearl_browser_manual.cmd`
3. Neu einloggen

### Tabs laden nicht

**Problem:** Netzwerk/Firewall

**Lösung:**
1. Check Internet-Verbindung
2. Prüfe ob BDO Marketplace im normalen Browser läuft
3. Firewall-Ausnahme für Python/Chromium

---

## ✅ Zusammenfassung

### Empfohlener Weg (Manual Login):

```bash
1. run_pearl_browser_manual.cmd
2. Browser öffnet → Einloggen über Steam
3. ENTER drücken
4. Monitoring läuft automatisch
5. Bei Neustart: Schritt 1-4 wiederholen
```

**Fertig!** Kein Cookie-Kopieren, keine Token-Probleme. Einfach einloggen und loslegen! 🚀

