"""
LinkedIn Authentication Module
Handles login, cookie management, and session maintenance
"""

import json
import time
import logging
import getpass
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
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
            config: Configuration dictionary
        """
        self.config = config
        self.email = None
        self.password = None
        self.username_display = None
        self.cookie_file = Path('cookies.json')
        self.browser_config = config.get('browser', {})
        self.wait_config = config.get('waits', {})
        
    def _get_credentials_from_user(self) -> Tuple[str, str, str]:
        """
        Prompt user for LinkedIn credentials
        
        Returns:
            Tuple of (email, password, display_name)
        """
        print("\n" + "="*60)
        print("LINKEDIN LOGIN REQUIRED")
        print("="*60)
        
        # Get email
        email = input("Enter LinkedIn email/username: ").strip()
        while not email:
            print("Email cannot be empty!")
            email = input("Enter LinkedIn email/username: ").strip()
        
        # Get password (hidden input)
        password = getpass.getpass("Enter LinkedIn password: ").strip()
        while not password:
            print("Password cannot be empty!")
            password = getpass.getpass("Enter LinkedIn password: ").strip()
        
        # Get display name for verification
        print("\n⚠️  For login verification, please enter your full name as displayed on LinkedIn")
        print("   (This will be used to verify successful login, case insensitive)")
        display_name = input("Enter your LinkedIn display name: ").strip()
        while not display_name:
            print("Display name cannot be empty!")
            display_name = input("Enter your LinkedIn display name: ").strip()
        
        print("="*60 + "\n")
        
        return email, password, display_name
    
    def _create_driver(self, headless: bool = None) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver
        
        Args:
            headless: Override headless setting (None = use config)
            
        Returns:
            Configured Chrome WebDriver instance
        """
        options = Options()
        
        # Determine headless mode
        if headless is None:
            use_headless = self.browser_config.get('headless', True)
        else:
            use_headless = headless
        
        # Configure browser options
        if use_headless:
            options.add_argument('--headless=new')
            options.add_argument('--force-device-scale-factor=0.1') # 关键：缩放页面以适应不同分辨率    
            options.add_argument('--window-size=19200,10800')     # 设置超大窗，以便让BrowserMob Proxy捕获完整页面内容
        
        options.add_argument('--disable-gpu')  
        ##options.add_argument(f'--window-size={self.browser_config.get("window_width", 1920)},{self.browser_config.get("window_height", 1080)}')
        options.add_argument('--incognito')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Additional options for better compatibility
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.browser_config.get('page_load_timeout', 300))
        driver.implicitly_wait(self.browser_config.get('implicit_wait', 10))
        
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
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
            # Remove domain attribute if it's causing issues
            if 'domain' in cookie and cookie['domain'].startswith('.'):
                # Keep domain as is, LinkedIn requires it
                pass
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.debug(f"Failed to add cookie {cookie.get('name')}: {e}")
    
    def _is_logged_in(self, driver: webdriver.Chrome) -> bool:
        """
        Check if user is already logged in (case insensitive)
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if logged in, False otherwise
        """
        if not self.username_display:
            return False
            
        try:
            # Try multiple XPath patterns to find the display name
            xpath_patterns = [
                f"//*[contains(text(), '{self.username_display}')]",
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{self.username_display.lower()}')]",
                "//*[contains(@class, 'global-nav__me')]//span",
                "//*[contains(@class, 'me-profile')]//span",
                "//img[@alt]"
            ]
            
            wait = WebDriverWait(driver, 10)
            
            for pattern in xpath_patterns:
                try:
                    elements = driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        element_text = element.text.strip()
                        element_alt = element.get_attribute('alt')
                        
                        # Check text content (case insensitive)
                        if element_text and self.username_display.lower() in element_text.lower():
                            logger.info(f"Logged in as: {element_text}")
                            return True
                        
                        # Check alt attribute
                        if element_alt and self.username_display.lower() in element_alt.lower():
                            logger.info(f"Logged in as: {element_alt}")
                            return True
                except:
                    continue
            
            # Also check the page source for the display name (case insensitive)
            page_source = driver.page_source.lower()
            if self.username_display.lower() in page_source:
                logger.info(f"Found display name in page source")
                return True
                
            return False
            
        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
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
            time.sleep(2)
            
            # Try multiple selectors for email input
            email_selectors = [
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[name='session_key']"),
                (By.XPATH, "//input[@type='text' or @type='email']")
            ]
            
            email_input = None
            for selector_type, selector_value in email_selectors:
                try:
                    email_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not email_input:
                logger.error("Could not find email input field")
                return False
            
            email_input.clear()
            email_input.send_keys(self.email)
            logger.info("Entered email")
            
            # Find password input
            password_selectors = [
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[name='session_password']"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            password_input = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_input = driver.find_element(selector_type, selector_value)
                    break
                except:
                    continue
            
            if not password_input:
                logger.error("Could not find password input field")
                return False
            
            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("Entered password")
            
            # Find and click sign in button
            sign_in_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(@class, 'sign-in')]"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            sign_in_button = None
            for selector_type, selector_value in sign_in_selectors:
                try:
                    sign_in_button = driver.find_element(selector_type, selector_value)
                    break
                except:
                    continue
            
            if not sign_in_button:
                logger.error("Could not find sign in button")
                return False
            
            sign_in_button.click()
            logger.info("Submitted login credentials")
            time.sleep(3)
            
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
            # Wait a bit to see if verification is needed
            time.sleep(3)
            
            # Check for verification code input
            verification_input = None
            verification_selectors = [
                (By.ID, "input__email_verification_pin"),
                (By.NAME, "pin"),
                (By.CSS_SELECTOR, "input[type='tel']"),
                (By.XPATH, "//input[contains(@id, 'verification')]")
            ]
            
            for selector_type, selector_value in verification_selectors:
                try:
                    verification_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except TimeoutException:
                    continue
            
            if verification_input:
                logger.info("Verification code input found")
                
                # Try to get verification code automatically
                pin_code = None
                retry_count = 0
                max_retries = 5
                
                print("\n" + "="*60)
                print("TWO-FACTOR AUTHENTICATION REQUIRED")
                print("="*60)
                
                while not pin_code and retry_count < max_retries:
                    print(f"Attempting to retrieve verification code from Gmail... (attempt {retry_count + 1}/{max_retries})")
                    pin_code = self._get_verification_code()
                    if pin_code == '0':
                        print(f"  No verification code found yet. Waiting {self.wait_config.get('verification_retry', 30)} seconds...")
                        time.sleep(self.wait_config.get('verification_retry', 30))
                        retry_count += 1
                    else:
                        print(f"  ✓ Verification code retrieved: {pin_code}")
                        break
                
                # If automatic retrieval fails, ask user to enter manually
                if not pin_code or pin_code == '0':
                    print("\n⚠️  Could not automatically retrieve verification code from Gmail")
                    print("Please check your email for the LinkedIn verification code")
                    pin_code = input("Enter the 6-digit verification code manually: ").strip()
                
                if pin_code and len(pin_code) == 6:
                    verification_input.clear()
                    verification_input.send_keys(pin_code)
                    
                    # Find submit button
                    submit_selectors = [
                        (By.ID, "email-pin-submit-button"),
                        (By.XPATH, "//button[@type='submit']"),
                        (By.CSS_SELECTOR, "button[type='submit']")
                    ]
                    
                    submit_button = None
                    for selector_type, selector_value in submit_selectors:
                        try:
                            submit_button = driver.find_element(selector_type, selector_value)
                            break
                        except:
                            continue
                    
                    if submit_button:
                        submit_button.click()
                        logger.info("Submitted verification code")
                        time.sleep(3)
                        return True
                    else:
                        # If no submit button, the code might auto-submit
                        logger.info("Verification code submitted (auto-submit detected)")
                        return True
                else:
                    logger.warning("Invalid verification code")
                    return False
            else:
                logger.info("No verification code required")
                return True
                
        except Exception as e:
            logger.debug(f"Error in verification handling: {e}")
            return True  # No verification needed
    
    def _manual_login_intervention(self, driver: webdriver.Chrome) -> bool:
        """
        Handle manual login intervention when automatic login fails
        
        Args:
            driver: WebDriver instance
            
        Returns:
            True if manual login successful, False otherwise
        """
        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("Automatic login failed. Please complete the login process manually.")
        print("The browser window is now visible for you to log in.")
        print("After successful login, press Enter to continue with scraping.")
        print("="*60)
        
        input("\nPress Enter after you have successfully logged into LinkedIn...")
        
        # Check if login was successful
        if self._is_logged_in(driver):
            print("✓ Manual login successful!")
            self._save_cookies(driver)
            return True
        else:
            print("✗ Could not verify successful login. Please make sure you're logged in.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry == 'y':
                return self._manual_login_intervention(driver)
            return False
    
    def authenticate(self) -> webdriver.Chrome:
        """
        Main authentication flow
        
        Returns:
            Authenticated WebDriver instance
        """
        # Get credentials from user
        self.email, self.password, self.username_display = self._get_credentials_from_user()
        
        # First try headless mode with cookies
        driver = None
        try:
            # Try cookie-based login first (headless)
            print("🔐 Attempting cookie-based login...")
            driver = self._create_driver(headless=True)
            driver.get("https://www.linkedin.com")
            time.sleep(2)
            
            cookies = self._load_cookies()
            if cookies:
                logger.info("Attempting cookie-based login...")
                self._add_cookies_to_driver(driver, cookies)
                driver.refresh()
                time.sleep(3)
                
                if self._is_logged_in(driver):
                    logger.info("✓ Cookie-based login successful")
                    self._save_cookies(driver)
                    print("✓ Successfully logged in using saved cookies!")
                    return driver
                else:
                    logger.info("Cookie-based login failed, proceeding with credential login")
                    driver.quit()
                    driver = None
            else:
                driver.quit()
                driver = None
                
        except Exception as e:
            logger.warning(f"Cookie-based login attempt failed: {e}")
            if driver:
                driver.quit()
                driver = None
        
        # Try credential-based login in headless mode
        try:
            print("🔐 Attempting credential-based login...")
            driver = self._create_driver(headless=True)
            driver.get("https://www.linkedin.com")
            time.sleep(2)
            
            if not self._login_with_credentials(driver):
                raise Exception("Failed to submit login credentials")
            
            # Handle verification if needed
            if not self._handle_verification(driver):
                raise Exception("Failed to complete verification")
            
            # Wait for login to complete
            time.sleep(5)
            
            # Verify login success
            if self._is_logged_in(driver):
                self._save_cookies(driver)
                logger.info("✓ Login completed successfully")
                print("✓ Successfully logged into LinkedIn!")
                return driver
            else:
                raise Exception("Could not verify successful login")
                
        except Exception as e:
            logger.warning(f"Headless credential login failed: {e}")
            if driver:
                driver.quit()
                driver = None
            
            # Switch to visible mode for manual intervention
            print("\n⚠️ Automatic login failed. Switching to manual mode...")
            return self._authenticate_manual()
    
    def _authenticate_manual(self) -> webdriver.Chrome:
        """
        Manual authentication flow with visible browser
        
        Returns:
            Authenticated WebDriver instance
        """
        print("\n🖥️ Opening visible browser for manual login...")
        
        # Create driver in visible mode
        driver = self._create_driver(headless=False)
        
        try:
            # Navigate to LinkedIn
            driver.get("https://www.linkedin.com")
            time.sleep(2)
            
            # Try to use existing cookies first
            cookies = self._load_cookies()
            if cookies:
                print("Attempting to use saved cookies...")
                self._add_cookies_to_driver(driver, cookies)
                driver.refresh()
                time.sleep(3)
                
                if self._is_logged_in(driver):
                    print("✓ Successfully logged in using saved cookies!")
                    self._save_cookies(driver)
                    return driver
            
            # Fill in credentials automatically (to save user effort)
            print("Filling in credentials automatically...")
            try:
                # Find and fill email
                email_selectors = [
                    (By.ID, "username"),
                    (By.CSS_SELECTOR, "input[name='session_key']"),
                    (By.XPATH, "//input[@type='text' or @type='email']")
                ]
                
                for selector_type, selector_value in email_selectors:
                    try:
                        email_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        email_input.clear()
                        email_input.send_keys(self.email)
                        break
                    except:
                        continue
                
                # Find and fill password
                password_selectors = [
                    (By.ID, "password"),
                    (By.CSS_SELECTOR, "input[name='session_password']"),
                    (By.XPATH, "//input[@type='password']")
                ]
                
                for selector_type, selector_value in password_selectors:
                    try:
                        password_input = driver.find_element(selector_type, selector_value)
                        password_input.clear()
                        password_input.send_keys(self.password)
                        break
                    except:
                        continue
                
                # Try to click sign in button automatically
                sign_in_selectors = [
                    (By.XPATH, "//button[@type='submit']"),
                    (By.XPATH, "//button[contains(@class, 'sign-in')]"),
                    (By.CSS_SELECTOR, "button[type='submit']")
                ]
                
                for selector_type, selector_value in sign_in_selectors:
                    try:
                        sign_in_button = driver.find_element(selector_type, selector_value)
                        sign_in_button.click()
                        print("Submitted credentials automatically")
                        break
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"Auto-fill failed: {e}")
                print("Please enter credentials manually in the browser.")
            
            # Manual intervention for completing login
            success = self._manual_login_intervention(driver)
            
            if success:
                # Save cookies for future headless use
                self._save_cookies(driver)
                print("✓ Manual login completed successfully!")
                
                # Ask user if they want to continue with headless mode
                print("\n" + "="*60)
                choice = input("Continue with headless mode for scraping? (y/n): ").strip().lower()
                
                if choice == 'y':
                    # Save current session data
                    current_url = driver.current_url
                    cookies = driver.get_cookies()
                    
                    # Close current visible driver
                    driver.quit()
                    
                    # Create new headless driver
                    print("Switching to headless mode...")
                    new_driver = self._create_driver(headless=True)
                    new_driver.get("https://www.linkedin.com")
                    
                    # Add saved cookies to new driver
                    for cookie in cookies:
                        if 'expiry' in cookie:
                            cookie['expiry'] = int(cookie['expiry'])
                        try:
                            new_driver.add_cookie(cookie)
                        except:
                            pass
                    
                    # Navigate to the same page
                    new_driver.get(current_url)
                    time.sleep(2)
                    
                    print("✓ Switched to headless mode successfully!")
                    return new_driver
                else:
                    print("Continuing with visible browser mode...")
                    return driver
            else:
                raise Exception("Manual login failed")
                
        except Exception as e:
            logger.error(f"Manual authentication failed: {e}")
            if driver:
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
            time.sleep(3)
            if self._is_logged_in(driver):
                self._save_cookies(driver)
                logger.info("Session refreshed successfully")
                return True
            else:
                logger.warning("Session refresh failed - not logged in")
                return False
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            return False
    
    def update_credentials(self, email: str = None, password: str = None, display_name: str = None) -> None:
        """
        Update credentials manually
        
        Args:
            email: New email
            password: New password
            display_name: New display name
        """
        if email:
            self.email = email
        if password:
            self.password = password
        if display_name:
            self.username_display = display_name