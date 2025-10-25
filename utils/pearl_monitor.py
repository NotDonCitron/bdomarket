import time
import json
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import asdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from .config_manager import ConfigManager
from .pearl_calculator import PearlItem, PearlCalculator

class PearlShopMonitor:
    """Chrome-based web traffic monitor for Pearl shop listings"""
    
    def __init__(self, config_path: str = "config/pearl_monitor.yaml"):
        self.config = ConfigManager(config_path)
        self.driver: Optional[webdriver.Chrome] = None
        self.is_monitoring = False
        self.listed_items_cache: Dict[str, datetime] = {}
        self.alert_callbacks: List[Callable] = []
        
    async def initialize(self) -> None:
        """Initialize Chrome driver"""
        try:
            # Setup Chrome options
            chrome_options = Options()
            if self.config.get("pearl_monitor.headless", True):
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"--user-agent={self.config.get('pearl_monitor.user_agent')}")
            
            # Enable network logging
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            # Initialize Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("✅ Chrome driver initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            raise
    
    async def authenticate(self) -> bool:
        """Authenticate with BDO website using existing session if available"""
        try:
            # Check if we have saved authentication tokens
            session_token = self.config.get("auth.session_token")
            if session_token:
                return await self._restore_session(session_token)
            
            # Otherwise, navigate to login page
            self.driver.get("https://www.bdoverseas.com/en-US/account/login")
            
            print("🔑 Please log in manually in the browser window...")
            print("⏳ Waiting for authentication completion...")
            
            # Wait for successful login (redirect to main page or account page)
            WebDriverWait(self.driver, 300).until(
                lambda driver: "account" not in driver.current_url.lower() or 
                              "dashboard" in driver.current_url.lower()
            )
            
            # Save authentication tokens
            await self._save_session()
            
            print("✅ Authentication successful!")
            return True
            
        except TimeoutException:
            print("❌ Authentication timed out")
            return False
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    async def _restore_session(self, session_token: str) -> bool:
        """Restore existing session"""
        try:
            # Add session cookie
            self.driver.add_cookie({
                'name': 'session_token',
                'value': session_token,
                'domain': '.bdoverseas.com'
            })
            
            # Test session validity
            self.driver.get("https://www.bdoverseas.com/en-US/pearlshop")
            await asyncio.sleep(3)
            
            # Check if we're logged in
            if "login" not in self.driver.current_url.lower():
                print("✅ Session restored successfully")
                return True
            
        except Exception as e:
            print(f"⚠️ Session restoration failed: {e}")
        
        return False
    
    async def _save_session(self) -> None:
        """Save current session tokens"""
        try:
            cookies = self.driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] in ['session_token', 'auth_token']:
                    self.config.set(f"auth.{cookie['name']}", cookie['value'])
            
            print("💾 Session tokens saved")
            
        except Exception as e:
            print(f"⚠️ Failed to save session: {e}")
    
    async def setup_network_monitoring(self) -> None:
        """Setup Chrome to monitor network requests for Pearl shop updates"""
        try:
            # Enable performance logging to capture network requests
            print("🌐 Network monitoring enabled for Pearl shop")
            
        except Exception as e:
            print(f"❌ Failed to setup network monitoring: {e}")
            raise
    
    async def start_monitoring(self) -> None:
        """Start monitoring Pearl shop for new listings"""
        if not self.driver:
            await self.initialize()
        
        # Navigate to Pearl shop
        self.driver.get("https://www.bdoverseas.com/en-US/pearlshop")
        await asyncio.sleep(5)
        
        # Setup network monitoring
        await self.setup_network_monitoring()
        
        self.is_monitoring = True
        print("🔍 Started monitoring Pearl shop for new listings...")
        
        # Main monitoring loop
        while self.is_monitoring:
            try:
                # Check for new network responses
                await self._check_network_responses()
                
                # Also check page content directly as fallback
                await self._scan_page_content()
                
                # Poll at configured interval
                poll_interval = self.config.get("pearl_monitor.poll_interval", 1)
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _check_network_responses(self) -> None:
        """Check network responses for Pearl shop updates"""
        try:
            # Get performance logs from Chrome
            logs = self.driver.get_log('performance')
            
            for log in logs:
                message = json.loads(log['message'])
                
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    
                    # Check if this is a Pearl shop API response
                    if 'pearlshop' in url.lower() and 'items' in url.lower():
                        await self._process_pearl_shop_response(message)
                        
        except Exception as e:
            print(f"⚠️ Network monitoring error: {e}")
    
    async def _process_pearl_shop_response(self, message: Dict) -> None:
        """Process Pearl shop API response for new items"""
        try:
            # For Chrome performance logs, extract the response data differently
            # This is a simplified version that works with Chrome performance logs
            response_data = message.get('message', {}).get('params', {}).get('response', {})
            url = response_data.get('url', '')
            
            if 'pearlshop' in url.lower() and 'items' in url.lower():
                # Try to get response body (limited by Chrome security)
                # In practice, we'll rely more on page scanning
                print(f"🔍 Detected Pearl shop API call: {url}")
                
        except Exception as e:
            print(f"⚠️ Failed to process Pearl shop response: {e}")
    
    async def _scan_page_content(self) -> None:
        """Scan page content directly for new Pearl items (fallback method)"""
        try:
            # Look for item listings in the page
            item_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "[data-item-id], .pearl-item, .shop-item"
            )
            
            for element in item_elements:
                try:
                    item_data = await self._extract_item_data(element)
                    if item_data:
                        await self._process_new_item(item_data)
                except Exception as e:
                    continue  # Skip problematic elements
                    
        except Exception as e:
            print(f"⚠️ Page scanning error: {e}")
    
    async def _extract_item_data(self, element) -> Optional[PearlItem]:
        """Extract item data from DOM element"""
        try:
            # Extract item information
            item_id = element.get_attribute('data-item-id') or ""
            name_element = element.find_element(By.CSS_SELECTOR, ".item-name, .name")
            name = name_element.text.strip() if name_element else "Unknown"
            
            price_element = element.find_element(By.CSS_SELECTOR, ".price, .cost")
            price_text = price_element.text.strip() if price_element else "0"
            
            # Parse price (handle formats like "1,500 Pearl", "1500")
            price = self._parse_price(price_text)
            
            category = "outfit"  # Default, can be enhanced
            
            return PearlItem(
                item_id=item_id,
                name=name,
                category=category,
                price=price,
                listed_time=datetime.now()
            )
            
        except Exception as e:
            return None
    
    def _parse_price(self, price_text: str) -> int:
        """Parse price from text string"""
        try:
            # Remove non-numeric characters except commas
            cleaned = ''.join(c for c in price_text if c.isdigit() or c == ',')
            return int(cleaned.replace(',', '')) if cleaned else 0
        except:
            return 0
    
    async def _parse_pearl_items(self, data: Dict) -> None:
        """Parse Pearl items from API response data"""
        try:
            items = data.get('items', data.get('data', []))
            
            for item_data in items:
                pearl_item = PearlItem(
                    item_id=str(item_data.get('id', '')),
                    name=item_data.get('name', 'Unknown'),
                    category=item_data.get('category', 'outfit'),
                    price=int(item_data.get('price', 0)),
                    listed_time=datetime.now()
                )
                
                await self._process_new_item(pearl_item)
                
        except Exception as e:
            print(f"⚠️ Failed to parse Pearl items: {e}")
    
    async def _process_new_item(self, item: PearlItem) -> None:
        """Process and check if item is new and profitable"""
        try:
            # Check if we've seen this item before
            cache_key = f"{item.item_id}_{item.name}"
            
            if cache_key in self.listed_items_cache:
                # Update timestamp but don't alert
                self.listed_items_cache[cache_key] = item.listed_time
                return
            
            # This is a new listing
            self.listed_items_cache[cache_key] = item.listed_time
            
            # Calculate profit metrics
            item = PearlCalculator.calculate_profit_metrics(item)
            
            # Check if it meets alert criteria
            min_profit = self.config.get("pearl_monitor.alert_threshold.minimum_profit", 100_000_000)
            min_roi = self.config.get("pearl_monitor.alert_threshold.minimum_roi", 0.05)
            
            if item.profit_margin >= min_profit and item.roi >= min_roi:
                await self._trigger_alert(item)
            
            # Log the new item
            print(f"🔍 New Pearl item detected: {item.name} - {item.price:,} Pearl")
            
        except Exception as e:
            print(f"⚠️ Failed to process new item: {e}")
    
    async def _trigger_alert(self, item: PearlItem) -> None:
        """Trigger alert for profitable Pearl item"""
        alert_msg = (
            f"💎 PEARL ALERT! {item.name}\n"
            f"   Listed: {item.price:,} Pearl\n"
            f"   Extraction: {item.extraction_value:,} ({item.extraction_value//3_000_000:,} Crons)\n"
            f"   Profit: {item.profit_margin:+,.0f} ({item.roi:+.1%} ROI) ✓✓✓\n"
            f"   Time: {item.listed_time.strftime('%H:%M:%S')} (ACT NOW!)"
        )
        
        print("\n" + "="*60)
        print(alert_msg)
        print("="*60 + "\n")
        
        # Sound alert
        if self.config.get("pearl_monitor.notifications.sound_alert", True):
            print('\a')  # System beep
        
        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(item)
            except Exception as e:
                print(f"⚠️ Alert callback error: {e}")
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add custom alert callback function"""
        self.alert_callbacks.append(callback)
    
    def stop_monitoring(self) -> None:
        """Stop monitoring and cleanup resources"""
        self.is_monitoring = False
        
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        print("🛑 Pearl shop monitoring stopped")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.stop_monitoring()