# BDO Market Trader - Complete Guide

**Authenticated trading functionality for BDO Central Market** - Based on [kookehs/bdo-marketplace](https://github.com/kookehs/bdo-marketplace) implementation.

## 🎯 Features

The Market Trader adds authenticated trading capabilities to the BDO Trading Tools:

### ✅ Implemented Features

- **Buy Items** - Place buy orders on the marketplace
- **Sell Items** - List items for sale
- **Cancel Listings** - Cancel pending sell orders
- **Collect Funds** - Collect silver from completed sales
- **View Inventory** - Check Central Market warehouse
- **View Listings** - See active buy/sell orders
- **Check Funds** - View available trading silver
- **Hot List** - View trending/hot items (read-only)
- **Wait List** - View low-stock items (read-only)

## 🔐 Authentication Setup

### Step 1: Get Your Credentials

Trading requires authentication cookies from the BDO Central Market website:

1. **Open Browser**
   - Go to https://market.blackdesertonline.com/
   - Log in with your BDO account

2. **Open DevTools**
   - Press `F12` (or right-click → Inspect)
   - Go to the **Network** tab

3. **Trigger a Request**
   - Search for any item on the marketplace
   - Click on any request in the Network tab

4. **Copy Cookies**
   - Find the **Cookies** section in the request headers
   - Copy these two values:
     - `__RequestVerificationToken` - Long string (e.g., `CfDJ8...`)
     - `userNo` - Your user number (e.g., `12345678`)

### Step 2: Save Credentials

Run the interactive setup:

```bash
python trader.py auth
```

**Or** manually create `config/trader_auth.json`:

```json
{
  "region": "eu",
  "session_id": "your__RequestVerificationToken_value",
  "user_no": "your_userNo_value"
}
```

**⚠️ Important Notes:**
- Credentials expire when you log out
- Keep `trader_auth.json` **private** (already in `.gitignore`)
- You'll need to update credentials periodically

## 📖 Usage Examples

### Basic Commands

```bash
# Setup authentication
python trader.py auth

# View inventory
python trader.py inventory

# View active listings
python trader.py listings

# Check available funds
python trader.py funds

# Collect funds from sales
python trader.py collect
```

### Buying Items

```bash
# Buy by item name
python trader.py buy "Black Stone (Weapon)" --price 180000 --quantity 100

# Buy by item ID
python trader.py buy 16001 --price 180000 --quantity 100

# Buy with enhancement level (e.g., +15 gear)
python trader.py buy 11010 --price 50000000 --sid 15 --quantity 1

# Skip confirmation prompt
python trader.py buy 16001 --price 180000 --quantity 100 --confirm
```

### Selling Items

```bash
# Sell by item name
python trader.py sell "Black Stone (Weapon)" --price 250000 --quantity 50

# Sell by item ID
python trader.py sell 16001 --price 250000 --quantity 50

# Sell enhanced item (+15)
python trader.py sell 11010 --price 80000000 --sid 15 --quantity 1

# Skip confirmation prompt
python trader.py sell 16001 --price 250000 --quantity 50 --confirm
```

### Managing Listings

```bash
# View your active listings (to get order numbers)
python trader.py listings

# Cancel a specific listing
python trader.py cancel --item-id 16001 --order-no 123456789

# Cancel enhanced item listing
python trader.py cancel --item-id 11010 --sid 15 --order-no 123456789
```

## 🐍 Python API Usage

### Basic Trading

```python
import asyncio
from utils.market_trader import MarketTrader, load_credentials

async def trade_example():
    # Load credentials from config
    creds = load_credentials()
    
    async with MarketTrader(creds) as trader:
        # Buy item
        result = await trader.buy_item(
            item_id=16001,
            price=180000,
            quantity=100
        )
        
        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")

asyncio.run(trade_example())
```

### Advanced Trading

```python
import asyncio
from utils.market_trader import MarketTrader, TradeCredentials

async def advanced_trading():
    # Manual credentials
    creds = TradeCredentials(
        session_id="your_token",
        user_no="your_user_no",
        region='eu'
    )
    
    async with MarketTrader(creds) as trader:
        # Check funds
        funds = await trader.get_funds_available()
        print(f"Available: {funds:,} silver")
        
        # Get inventory
        inventory = await trader.get_inventory()
        for item in inventory:
            print(f"{item['name']}: {item['count']} units")
        
        # Get active listings
        listings = await trader.get_bid_listings()
        for listing in listings:
            order_type = "BUY" if listing['isBuy'] else "SELL"
            print(f"{order_type}: {listing['name']} x{listing['count']} @ {listing['price']:,}")
        
        # Sell item
        result = await trader.sell_item(
            item_id=16001,
            sid=0,
            price=250000,
            quantity=50
        )
        
        # Collect funds after sales complete
        result = await trader.collect_funds()
        if result.success and result.details:
            total = result.details.get('totalSilver', 0)
            print(f"Collected {total:,} silver")

asyncio.run(advanced_trading())
```

### Hot List & Wait List (Read-Only)

```python
import asyncio
from utils.market_client import MarketClient

async def view_hot_items():
    async with MarketClient(region='eu') as client:
        # Get trending items
        hot_items = await client.get_hot_list()
        for item in hot_items[:10]:
            print(f"{item['name']}: {item['stock']} stock @ {item['basePrice']:,}")
        
        # Get low-stock items
        wait_items = await client.get_wait_list()
        for item in wait_items[:10]:
            print(f"{item['name']}: {item.get('stock', 0)} stock")

asyncio.run(view_hot_items())
```

## ⚠️ Important Warnings

### Trading Constraints

1. **Registration Queue (1-90 seconds)**
   - Orders enter a random queue before execution
   - Speed advantage is limited
   - No guarantee of purchase even if stock available

2. **34.5% Effective Tax**
   - Applied to all sales (before Value Pack/Familia discounts)
   - Requires ~53% price increase to break even on flips
   - Tax already deducted when you collect funds

3. **Discrete Pricing**
   - Cannot set arbitrary prices
   - Prices are quantized by the market
   - Profit margins are limited

4. **Authentication Expiry**
   - Credentials expire when you log out
   - Session tokens expire periodically
   - Need to re-run `trader.py auth` to update

### Security Best Practices

- **Never commit** `config/trader_auth.json` to git
- **Never share** your credentials publicly
- **Use at your own risk** - automated trading may violate ToS
- **Start small** - test with low-value items first

## 🧪 Testing

```bash
# Test trader with mock credentials (will fail auth, but tests structure)
python test_trader.py

# Test hot list and wait list (no auth required)
python test_hot_list.py

# Test with real credentials (after setup)
python trader.py inventory
python trader.py listings
python trader.py funds
```

## 🔄 Integration with Existing Tools

The trader integrates seamlessly with existing BDO Trading Tools:

### Example: Sniper + Auto-Buy

```python
# Combine sniper alerts with automated buying
import asyncio
from utils.market_client import MarketClient
from utils.market_trader import MarketTrader, load_credentials

async def snipe_and_buy():
    creds = load_credentials()
    
    async with MarketClient(region='eu') as client, \
               MarketTrader(creds) as trader:
        
        # Monitor item
        orderbook = await client.get_orderbook(16001)
        
        # Check if price is good
        if orderbook and orderbook.orders:
            best_ask = orderbook.orders[0].price
            
            if best_ask <= 180000:  # Target buy price
                # Auto-buy
                result = await trader.buy_item(
                    item_id=16001,
                    price=best_ask,
                    quantity=100
                )
                print(f"Auto-buy: {result.message}")

asyncio.run(snipe_and_buy())
```

### Example: Portfolio + Auto-Collect

```python
# Automatically collect funds after tracking sales
import asyncio
from utils.market_trader import MarketTrader, load_credentials

async def collect_and_log():
    creds = load_credentials()
    
    async with MarketTrader(creds) as trader:
        # Collect funds
        result = await trader.collect_funds()
        
        if result.success and result.details:
            total = result.details.get('totalSilver', 0)
            
            # Log to portfolio (manual step)
            print(f"Collected {total:,} silver")
            print("Update portfolio.csv with sale proceeds")

asyncio.run(collect_and_log())
```

## 📊 API Reference

### MarketTrader Class

```python
class MarketTrader:
    """Authenticated trading client."""
    
    async def buy_item(item_id: int, sid: int, price: int, quantity: int) -> TradeResult
    async def sell_item(item_id: int, sid: int, price: int, quantity: int) -> TradeResult
    async def cancel_listing(item_id: int, sid: int, order_no: int) -> TradeResult
    async def collect_funds() -> TradeResult
    async def get_inventory() -> List[Dict]
    async def get_bid_listings() -> List[Dict]
    async def get_funds_available() -> int
```

### MarketClient Extended

```python
class MarketClient:
    """Market data client (read-only)."""
    
    async def get_hot_list() -> List[Dict]
    async def get_wait_list() -> List[Dict]
    # ... existing methods ...
```

## 🔗 Related Resources

- **Original Go Implementation**: [kookehs/bdo-marketplace](https://github.com/kookehs/bdo-marketplace)
- **BDO Market Website**: https://market.blackdesertonline.com/
- **Item Database**: https://bdocodex.com/us/items/
- **Market Data**: https://garmoth.com/market

## 🐛 Troubleshooting

### "No credentials found" Error

```bash
# Run authentication setup
python trader.py auth
```

### Authentication Fails

- Credentials may have expired
- Re-run `trader.py auth` with fresh cookies
- Ensure you copied the full cookie values

### "Request failed" Error

- Check your internet connection
- Verify region is correct in config
- BDO Central Market API may be down

### Item Not Found

- Use item ID instead of name
- Check item exists on https://bdocodex.com/
- Verify spelling and case sensitivity

## 📝 License

MIT License - See main README.md

## 🙏 Credits

- **Original Implementation**: [kookehs/bdo-marketplace](https://github.com/kookehs/bdo-marketplace) (Go)
- **Python Port**: BDO Trading Tools v3
- **BDO Central Market API**: Pearl Abyss

---

**⚠️ Disclaimer**: Use at your own risk. Automated trading may violate BDO Terms of Service. This tool is for educational purposes.



