"""
LinkedIn Authentication Module
Handles login, cookie management, and session maintenance
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess

logger = logging.getLogger(__name__)


class LinkedInAuthenticator:
    """LinkedIn authentication handler"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authenticator
        
        Args:
            config: Configuration dictionary containing LinkedIn credentials
        """
        self.email = config.get('linkedin', {}).get('email')
        self.password = config.get('linkedin', {}).get('password')
        self.username_display = config.get('linkedin', {}).get('username_display', '')
        self.cookie_file = Path('cookies.json')
        self.browser_config = config.get('browser', {})
        self.wait_config = config.get('waits', {})
        
    def _create_driver(self) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver
        
        Returns:
            Configured Chrome WebDriver instance
        """
        options = Options()
        
        # Configure browser options
        if self.browser_config.get('headless', True):
            options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--window-size={self.browser_config.get("window_width", 1920)},{self.browser_config.get("window_height", 1080)}')
        options.add_argument('--incognito')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.browser_config.get('page_load_timeout', 300))
        driver.implicitly_wait(self.browser_config.get('implicit_wait', 10))
        
        return driver
    
    def _get_verification_code(self) -> str:
        """
        Retrieve LinkedIn verification code from Gmail
        
        Returns:
            6-digit verification code or '0' if not found
        """
        cmd = [
            'gog', 'gmail', 'search', 
            'from:security-noreply@linkedin.com subject:"verification code" newer_than:1m', 
            '--max', '2', '--json'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.returncode == 0:
                emails = json.loads(result.stdout)
                for email in emails.get('threads', []):
                    return email['subject'][-6:]
            return '0'
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to get verification code: {e}")
            return '0'
    
    def _load_cookies(self) -> Optional[list]:
        """
        Load cookies from file
        
        Returns:
            List of cookies or None if file doesn't exist
        """
        if self.cookie_file.exists():
            try:
                with open(self.cookie_file, 'r') as f:
                    cookies = json.load(f)
                logger.info(f"Loaded {len(cookies)} cookies from {self.cookie_file}")
                return cookies
            except Exception as e:
                logger.error(f"Failed to load cookies: {e}")
        return None
    
    def _save_cookies(self, driver: webdriver.Chrome) -> None:
        """
        Save current cookies to file
        
        Args:
            driver: WebDriver instance
        """
        try:
            cookies = driver.get_cookies()
            with open(self.cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Saved {len(cookies)} cookies to {self.cookie_file}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
    
    def _add_cookies_to_driver(self, driver: webdriver.Chrome, cookies: list) -> None:
        """
        Add cookies to WebDriver
        
        Args:
            driver: WebDriver instance
            cookies: List of cookies to add
        """
        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
    
    def _is_logged_in(self, driver: webdriver.Chrome) -> bool:
        """
        Check if user is already logged in
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if logged in, False otherwise
        """
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(), '{self.username_display}')]")
            ))
            logger.info("Already logged in via cookies")
            return True
        except TimeoutException:
            logger.info("Not logged in, proceeding with login flow")
            return False
    
    def _login_with_credentials(self, driver: webdriver.Chrome) -> bool:
        """
        Perform login using email and password
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            driver.get("https://www.linkedin.com/login")
            
            # Wait for and fill email
            email_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            
            # Fill password
            password_input = driver.find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Click sign in button
            sign_in_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            sign_in_button.click()
            logger.info("Submitted login credentials")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to login with credentials: {e}")
            return False
    
    def _handle_verification(self, driver: webdriver.Chrome) -> bool:
        """
        Handle 2FA verification if prompted
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            # Check for verification code input
            verification_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "input__email_verification_pin"))
            )
            logger.info("Verification code input found")
            
            # Get verification code
            pin_code = None
            retry_count = 0
            max_retries = 5
            
            while not pin_code and retry_count < max_retries:
                pin_code = self._get_verification_code()
                if pin_code == '0':
                    logger.info(f"Waiting for verification code... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(self.wait_config.get('verification_retry', 30))
                    retry_count += 1
                else:
                    break
            
            if pin_code and pin_code != '0':
                verification_input.send_keys(pin_code)
                submit_button = driver.find_element(By.ID, "email-pin-submit-button")
                submit_button.click()
                logger.info("Submitted verification code")
                return True
            else:
                logger.warning("Could not retrieve verification code")
                return False
                
        except TimeoutException:
            logger.info("No verification code required")
            return True
        except Exception as e:
            logger.error(f"Error handling verification: {e}")
            return False
    
    def authenticate(self) -> webdriver.Chrome:
        """
        Main authentication flow
        
        Returns:
            Authenticated WebDriver instance
        """
        driver = self._create_driver()
        
        try:
            # Navigate to LinkedIn
            driver.get("https://www.linkedin.com")
            
            # Try cookie-based login
            cookies = self._load_cookies()
            if cookies:
                self._add_cookies_to_driver(driver, cookies)
                driver.refresh()
                
                if self._is_logged_in(driver):
                    self._save_cookies(driver)
                    return driver
            
            # Perform credential-based login
            logger.info("Proceeding with credential-based login")
            if not self._login_with_credentials(driver):
                raise Exception("Failed to submit login credentials")
            
            # Handle verification if needed
            if not self._handle_verification(driver):
                raise Exception("Failed to complete verification")
            
            # Verify login success
            if self._is_logged_in(driver):
                self._save_cookies(driver)
                logger.info("Login completed successfully")
                return driver
            else:
                raise Exception("Login verification failed")
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            driver.quit()
            raise
    
    def refresh_session(self, driver: webdriver.Chrome) -> bool:
        """
        Refresh session by validating and renewing cookies
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            driver.get("https://www.linkedin.com/feed/")
            if self._is_logged_in(driver):
                self._save_cookies(driver)
                return True
            return False
        except Exception:
            return False