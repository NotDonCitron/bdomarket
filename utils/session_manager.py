"""
Persistent Session Manager for BDO Central Market.

Handles authentication, session persistence, and automatic credential refresh.
Supports both cookie-based auth and browser-based Steam login.
"""
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import asyncio
import aiohttp


@dataclass
class SessionData:
    """Session authentication data."""
    cookie: str
    user_agent: str
    request_verification_token: str
    user_no: Optional[str] = None
    created_at: float = 0.0
    last_validated: float = 0.0
    is_valid: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary."""
        return cls(**data)


class SessionManager:
    """
    Manages BDO Central Market authentication sessions.
    
    Features:
    - Persistent session storage
    - Automatic credential refresh
    - Session validation
    - Support for cookie-based and browser-based auth
    
    Usage:
        manager = SessionManager()
        
        # Load existing session
        session = await manager.load_session()
        
        # Or create new from browser cookies
        session = await manager.create_session_from_cookies(
            cookie="...",
            user_agent="...",
            request_verification_token="..."
        )
        
        # Validate session
        is_valid = await manager.validate_session(session)
    """
    
    def __init__(self, session_file: str = "config/session.json", region: str = "eu"):
        """
        Initialize session manager.
        
        Args:
            session_file: Path to session storage file
            region: Market region (eu, na, kr, sa)
        """
        self.session_file = Path(session_file)
        self.region = region.lower()
        
        # Base URLs
        self.base_urls = {
            'eu': 'https://eu-trade.naeu.playblackdesert.com',
            'na': 'https://na-trade.naeu.playblackdesert.com',
            'kr': 'https://trade.kr.playblackdesert.com',
            'sa': 'https://sa-trade.tr.playblackdesert.com'
        }
        self.base_url = self.base_urls.get(self.region, self.base_urls['eu'])
        
        # Session validation cache (to avoid frequent API calls)
        self._last_validation_check = 0.0
        self._validation_cache_duration = 60.0  # 60 seconds
    
    async def load_session(self) -> Optional[SessionData]:
        """
        Load existing session from disk.
        
        Returns:
            SessionData if found and valid, None otherwise
        """
        if not self.session_file.exists():
            return None
        
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
            
            session = SessionData.from_dict(data)
            
            # Check if session is expired (24 hours)
            age = time.time() - session.created_at
            if age > 86400:  # 24 hours
                print(f"Session expired (age: {age/3600:.1f}h), need new login")
                return None
            
            # Validate session (with cache)
            if await self._should_validate_cached(session):
                is_valid = await self.validate_session(session)
                if not is_valid:
                    print("Session validation failed, need new login")
                    return None
            
            return session
            
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    async def save_session(self, session: SessionData):
        """
        Save session to disk.
        
        Args:
            session: Session data to save
        """
        try:
            # Create config directory if needed
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(self.session_file, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            
            print(f"Session saved to {self.session_file}")
            
        except Exception as e:
            print(f"Error saving session: {e}")
    
    async def create_session_from_cookies(
        self,
        cookie: str,
        user_agent: str,
        request_verification_token: str,
        user_no: Optional[str] = None
    ) -> SessionData:
        """
        Create new session from browser cookies.
        
        Args:
            cookie: Full cookie string from browser
            user_agent: User agent string
            request_verification_token: CSRF token
            user_no: User number (optional)
            
        Returns:
            SessionData object
        """
        session = SessionData(
            cookie=cookie,
            user_agent=user_agent,
            request_verification_token=request_verification_token,
            user_no=user_no,
            created_at=time.time(),
            last_validated=time.time(),
            is_valid=True
        )
        
        # Validate immediately
        is_valid = await self.validate_session(session)
        session.is_valid = is_valid
        
        if is_valid:
            await self.save_session(session)
        
        return session
    
    async def validate_session(self, session: SessionData) -> bool:
        """
        Validate session by making a test API call.
        
        Args:
            session: Session to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            headers = {
                'User-Agent': session.user_agent,
                'Cookie': session.cookie,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Test with a simple market list call
            data = {
                '__RequestVerificationToken': session.request_verification_token,
                'mainCategory': 55,
                'subCategory': 1
            }
            
            url = f"{self.base_url}/Home/GetWorldMarketList"
            
            async with aiohttp.ClientSession() as client:
                async with client.post(url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 401 or response.status == 403:
                        return False
                    
                    if response.status == 200:
                        # Try to parse response
                        try:
                            result = await response.json()
                            # If we get valid data, session is good
                            if isinstance(result, dict):
                                session.last_validated = time.time()
                                session.is_valid = True
                                await self.save_session(session)
                                return True
                        except:
                            pass
                    
                    return False
                    
        except Exception as e:
            print(f"Session validation error: {e}")
            return False
    
    async def _should_validate_cached(self, session: SessionData) -> bool:
        """
        Check if we should validate session or use cached result.
        
        Args:
            session: Session to check
            
        Returns:
            True if we should validate, False if cached result is recent enough
        """
        now = time.time()
        
        # If we validated recently, use cached result
        if session.last_validated > 0:
            age = now - session.last_validated
            if age < self._validation_cache_duration:
                return False
        
        return True
    
    async def extract_session_from_browser(self, page) -> Optional[SessionData]:
        """
        Extract session data from a Playwright page object.
        
        Args:
            page: Playwright Page object with active session
            
        Returns:
            SessionData if extraction successful, None otherwise
            
        Note: Requires Playwright to be installed
        """
        try:
            # Get cookies from browser
            cookies = await page.context.cookies()
            
            # Build cookie string
            cookie_parts = []
            request_token = None
            user_no = None
            
            for cookie in cookies:
                cookie_parts.append(f"{cookie['name']}={cookie['value']}")
                
                if cookie['name'] == '__RequestVerificationToken':
                    request_token = cookie['value']
                elif cookie['name'] == 'userNo':
                    user_no = cookie['value']
            
            cookie_string = '; '.join(cookie_parts)
            
            # Get user agent
            user_agent = await page.evaluate('navigator.userAgent')
            
            if not request_token:
                print("Warning: No __RequestVerificationToken found in cookies")
                return None
            
            # Create session
            session = await self.create_session_from_cookies(
                cookie=cookie_string,
                user_agent=user_agent,
                request_verification_token=request_token,
                user_no=user_no
            )
            
            return session
            
        except Exception as e:
            print(f"Error extracting session from browser: {e}")
            return None
    
    def clear_session(self):
        """Delete stored session file."""
        if self.session_file.exists():
            self.session_file.unlink()
            print(f"Session file deleted: {self.session_file}")


async def example_usage():
    """Example usage of SessionManager."""
    manager = SessionManager()
    
    # Try to load existing session
    print("Loading session...")
    session = await manager.load_session()
    
    if session:
        print(f"✅ Session loaded (age: {(time.time() - session.created_at)/3600:.1f}h)")
    else:
        print("❌ No valid session found")
        print("\nTo create a session:")
        print("1. Open BDO marketplace in browser")
        print("2. Login via Steam")
        print("3. Open DevTools (F12) -> Application -> Cookies")
        print("4. Copy all cookies and create session using create_session_from_cookies()")


if __name__ == "__main__":
    asyncio.run(example_usage())
