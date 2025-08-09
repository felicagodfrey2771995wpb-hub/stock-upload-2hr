#!/usr/bin/env python3
"""
Stock photo platform support modules
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

@dataclass
class UploadResult:
    """Result of an upload operation"""
    success: bool
    message: str
    file_id: Optional[str] = None
    url: Optional[str] = None

class StockPlatform(ABC):
    """Abstract base class for stock photo platforms"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        self.driver = None
    
    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """Login to the platform"""
        pass
    
    @abstractmethod
    def upload_image(self, image_path: Path, metadata: Dict[str, Any]) -> UploadResult:
        """Upload an image with metadata"""
        pass
    
    @abstractmethod
    def get_upload_status(self, file_id: str) -> Dict[str, Any]:
        """Get upload status for a file"""
        pass
    
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

class ShutterstockPlatform(StockPlatform):
    """Shutterstock platform implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://submit.shutterstock.com"
        self.api_url = "https://api.shutterstock.com"
    
    def login(self, username: str, password: str) -> bool:
        """Login to Shutterstock"""
        try:
            self.setup_driver()
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            # Fill login form
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Submit form
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for successful login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def upload_image(self, image_path: Path, metadata: Dict[str, Any]) -> UploadResult:
        """Upload image to Shutterstock"""
        try:
            if not self.driver:
                return UploadResult(False, "Not logged in")
            
            # Navigate to upload page
            self.driver.get(f"{self.base_url}/upload")
            
            # Wait for upload form
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Upload file
            file_input.send_keys(str(image_path.absolute()))
            
            # Wait for upload to complete
            time.sleep(5)
            
            # Fill metadata
            title_field = self.driver.find_element(By.NAME, "title")
            title_field.clear()
            title_field.send_keys(metadata.get("title", ""))
            
            description_field = self.driver.find_element(By.NAME, "description")
            description_field.clear()
            description_field.send_keys(metadata.get("description", ""))
            
            # Add keywords
            keywords = metadata.get("keywords", [])
            if keywords:
                keyword_field = self.driver.find_element(By.NAME, "keywords")
                keyword_field.clear()
                keyword_field.send_keys("; ".join(keywords))
            
            # Submit
            submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            submit_button.click()
            
            # Wait for submission
            time.sleep(3)
            
            return UploadResult(True, "Upload successful")
            
        except Exception as e:
            return UploadResult(False, f"Upload failed: {e}")
    
    def get_upload_status(self, file_id: str) -> Dict[str, Any]:
        """Get upload status"""
        # Implementation would depend on Shutterstock's API
        return {"status": "unknown", "file_id": file_id}

class AdobeStockPlatform(StockPlatform):
    """Adobe Stock platform implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://stock.adobe.com"
    
    def login(self, username: str, password: str) -> bool:
        """Login to Adobe Stock"""
        try:
            self.setup_driver()
            self.driver.get(f"{self.base_url}/contributor")
            
            # Wait for login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "EmailPage-EmailField"))
            )
            username_field.send_keys(username)
            
            # Continue button
            continue_button = self.driver.find_element(By.ID, "EmailPage-ContinueButton")
            continue_button.click()
            
            # Password field
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "PasswordPage-PasswordField"))
            )
            password_field.send_keys(password)
            
            # Sign in button
            signin_button = self.driver.find_element(By.ID, "PasswordPage-SignInButton")
            signin_button.click()
            
            # Wait for successful login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "contributor-dashboard"))
            )
            
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def upload_image(self, image_path: Path, metadata: Dict[str, Any]) -> UploadResult:
        """Upload image to Adobe Stock"""
        try:
            if not self.driver:
                return UploadResult(False, "Not logged in")
            
            # Navigate to upload page
            self.driver.get(f"{self.base_url}/contributor/upload")
            
            # Wait for upload form
            file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Upload file
            file_input.send_keys(str(image_path.absolute()))
            
            # Wait for upload to complete
            time.sleep(5)
            
            # Fill metadata
            title_field = self.driver.find_element(By.NAME, "title")
            title_field.clear()
            title_field.send_keys(metadata.get("title", ""))
            
            description_field = self.driver.find_element(By.NAME, "description")
            description_field.clear()
            description_field.send_keys(metadata.get("description", ""))
            
            # Add keywords
            keywords = metadata.get("keywords", [])
            if keywords:
                keyword_field = self.driver.find_element(By.NAME, "keywords")
                keyword_field.clear()
                keyword_field.send_keys("; ".join(keywords))
            
            # Submit
            submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            submit_button.click()
            
            # Wait for submission
            time.sleep(3)
            
            return UploadResult(True, "Upload successful")
            
        except Exception as e:
            return UploadResult(False, f"Upload failed: {e}")
    
    def get_upload_status(self, file_id: str) -> Dict[str, Any]:
        """Get upload status"""
        return {"status": "unknown", "file_id": file_id}

class PlatformManager:
    """Manager for different stock platforms"""
    
    def __init__(self):
        self.platforms = {}
        self._register_platforms()
    
    def _register_platforms(self):
        """Register available platforms"""
        self.platforms["shutterstock"] = ShutterstockPlatform
        self.platforms["adobe_stock"] = AdobeStockPlatform
    
    def get_platform(self, platform_name: str, config: Dict[str, Any]) -> Optional[StockPlatform]:
        """Get platform instance"""
        platform_class = self.platforms.get(platform_name.lower())
        if platform_class:
            return platform_class(config)
        return None
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return list(self.platforms.keys())