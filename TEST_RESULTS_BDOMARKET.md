# BDO Market Testing Results

## Test Items Identified

- **Black Stone** (ID: 16001) - Stock: 75,563 | Base Price: 191,000
- **Black Stone (Armor)** (ID: 16002) - Stock: 0 | Base Price: 9,000
- **Black Stone (Basteer)** (ID: 16003) - Stock: 0 | Base Price: 0
- **Concentrated Magical Black Stone** (ID: 16004) - Stock: 27,735 | Base Price: 7,000,000

## Test Results

### ✅ Item Monitoring (READ-ONLY)

**Status:** WORKING

- Successfully connects to BDO market API
- Retrieves item information (name, stock, price)
- Detects stock changes
- Handles UTF-8 encoding on Windows

**Test Script:** `pearl_monitor_bdomarket.py`

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File start_pearl_monitor.ps1
```

### ✅ Alert Detection Logic

**Status:** WORKING

- Successfully detects new items
- Successfully detects stock increases
- Successfully detects items sold out
- Tested using Hot List (frequently changing items)

**Test Script:** `test_alert_verification.py`

**Command:**
```powershell
powershell -ExecutionPolicy Bypass -File run_alert_test.ps1
```

### ⚠️ Auto-Buy (REQUIRES AUTHENTICATION)

**Status:** BLOCKED BY AUTHENTICATION

**Issue:** Error code `-8745` indicates authentication failure

**Current Credentials:**
- ✅ `__RequestVerificationToken`: Present
- ❌ Authentication cookie: Missing or incorrect

**Error Message:**
```
resultCode: -8745
resultMsg: /Error
```

**Test Script:** `test_autobuy_blackstone.py`

**Commands:**
```powershell
# Dry-run (working)
.venv\Scripts\python.exe test_autobuy_blackstone.py --timeout 10 --interval 1.0

# Live buy (blocked by auth)
.venv\Scripts\python.exe test_autobuy_blackstone.py --timeout 10 --interval 1.0 --confirm
```

## Production Deployment

### Monitor Pearl Items

```powershell
# Production monitor with 2-second interval
powershell -ExecutionPolicy Bypass -File start_pearl_monitor.ps1

# Or manually:
cd "C:\Users\kekww\Desktop\bdo marketplace tool"
.venv\Scripts\python.exe pearl_monitor_bdomarket.py --interval 2.0
```

### Known Working Features

1. **Pearl Item Monitoring** - Monitors all 8 Pearl categories for availability
2. **Alert Detection** - Detects when items become available, stock increases, or items sell out
3. **Item Lookup** - Successfully resolves item IDs to names, stock, and prices
4. **UTF-8 Support** - Properly handles Unicode characters on Windows console

### Known Limitations

1. **Auto-Buy Blocked** - Requires correct authentication cookies (`userNo` or equivalent)
2. **Rare Items** - Pearl items are extremely rare, may require long monitoring periods
3. **Session Expiry** - Credentials expire when logged out

## Next Steps

1. **Get Correct Authentication Cookies**
   - Log into https://market.blackdesertonline.com/
   - Access Central Market warehouse in-game
   - Check DevTools for `userNo` cookie
   - Update `config/trader_auth.json`

2. **Enable Auto-Buy**
   - Once authentication works, test buy functionality
   - Monitor for actual Pearl item drops
   - Set up alerts for specific items

3. **Production Monitoring**
   - Run `pearl_monitor_bdomarket.py` continuously
   - Configure alerts (console, file, notifications)
   - Monitor logs for rare Pearl item availability

## Files Reference

- `pearl_monitor_bdomarket.py` - Main Pearl item monitor
- `test_autobuy_blackstone.py` - Auto-buy verification test
- `test_alert_verification.py` - Alert detection test
- `config/trader_auth.json` - Authentication credentials
- `start_pearl_monitor.ps1` - PowerShell runner with UTF-8 encoding
