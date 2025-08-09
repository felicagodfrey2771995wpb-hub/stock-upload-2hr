#!/usr/bin/env python3
"""
Platform APIs for Stock Photo Upload

This module provides API integrations for major stock photo platforms:
- Shutterstock
- Adobe Stock  
- Getty Images
- Other platforms

Features:
- Automated image upload
- Metadata submission
- Progress tracking
- Error handling and retry logic
- Rate limiting compliance
"""

from __future__ import annotations
import base64
import json
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

from config import *

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------- Data Models ----------------------------- #

@dataclass
class UploadResult:
    """Result of an upload operation"""
    success: bool
    platform: str
    filename: str
    upload_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class PlatformCredentials:
    """Platform API credentials"""
    api_key: str
    secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

# ----------------------------- Base Platform API ----------------------------- #

class PlatformAPI(ABC):
    """Abstract base class for stock photo platform APIs"""
    
    def __init__(self, credentials: PlatformCredentials, rate_limit: int = 10):
        self.credentials = credentials
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _rate_limit_wait(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    def upload_image(self, image_path: Path, metadata: Dict) -> UploadResult:
        """Upload image with metadata"""
        pass
    
    @abstractmethod
    def get_upload_status(self, upload_id: str) -> Dict:
        """Get status of uploaded image"""
        pass
    
    def validate_metadata(self, metadata: Dict) -> Tuple[bool, List[str]]:
        """Validate metadata for platform requirements"""
        errors = []
        
        # Common validations
        if not metadata.get('title'):
            errors.append("Title is required")
        
        if not metadata.get('description'):
            errors.append("Description is required")
        
        if not metadata.get('keywords'):
            errors.append("Keywords are required")
        
        return len(errors) == 0, errors

# ----------------------------- Shutterstock API ----------------------------- #

class ShutterstockAPI(PlatformAPI):
    """Shutterstock API integration"""
    
    def __init__(self, credentials: PlatformCredentials):
        super().__init__(credentials, rate_limit=5)  # 5 requests per second
        self.base_url = "https://api.shutterstock.com/v2"
        self.upload_url = "https://submit-api.shutterstock.com/v1"
    
    def authenticate(self) -> bool:
        """Authenticate with Shutterstock API"""
        try:
            # Test authentication with a simple API call
            headers = {
                "Authorization": f"Bearer {self.credentials.api_key}"
            }
            
            response = self.session.get(
                f"{self.base_url}/user",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Shutterstock authentication successful")
                return True
            else:
                logger.error(f"Shutterstock authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Shutterstock authentication error: {e}")
            return False
    
    def upload_image(self, image_path: Path, metadata: Dict) -> UploadResult:
        """Upload image to Shutterstock"""
        self._rate_limit_wait()
        
        try:
            # Validate metadata
            is_valid, errors = self.validate_metadata(metadata)
            if not is_valid:
                return UploadResult(
                    success=False,
                    platform="shutterstock",
                    filename=image_path.name,
                    error_message=f"Validation errors: {'; '.join(errors)}"
                )
            
            # Prepare image data
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Create multipart form data
            files = {
                'image_file': (image_path.name, image_data, 'image/jpeg')
            }
            
            # Prepare metadata
            form_data = {
                'title': metadata['title'][:200],  # Shutterstock limit
                'description': metadata['description'][:1000],
                'keywords': ','.join(metadata['keywords'][:50]),  # Max 50 keywords
                'category': metadata.get('category', 'Miscellaneous'),
                'editorial': 'false',  # Commercial content
                'mature': 'false'
            }
            
            headers = {
                "Authorization": f"Bearer {self.credentials.api_key}"
            }
            
            # Upload image
            response = self.session.post(
                f"{self.upload_url}/submissions",
                files=files,
                data=form_data,
                headers=headers,
                timeout=300  # 5 minute timeout for uploads
            )
            
            if response.status_code in [200, 201]:
                result_data = response.json()
                return UploadResult(
                    success=True,
                    platform="shutterstock",
                    filename=image_path.name,
                    upload_id=str(result_data.get('id')),
                    metadata=result_data
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return UploadResult(
                    success=False,
                    platform="shutterstock",
                    filename=image_path.name,
                    error_message=error_msg
                )
                
        except Exception as e:
            return UploadResult(
                success=False,
                platform="shutterstock",
                filename=image_path.name,
                error_message=str(e)
            )
    
    def get_upload_status(self, upload_id: str) -> Dict:
        """Get status of uploaded image on Shutterstock"""
        try:
            headers = {
                "Authorization": f"Bearer {self.credentials.api_key}"
            }
            
            response = self.session.get(
                f"{self.upload_url}/submissions/{upload_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def validate_metadata(self, metadata: Dict) -> Tuple[bool, List[str]]:
        """Validate metadata for Shutterstock requirements"""
        is_valid, errors = super().validate_metadata(metadata)
        
        # Shutterstock specific validations
        if len(metadata.get('title', '')) > 200:
            errors.append("Title must be 200 characters or less")
        
        if len(metadata.get('description', '')) > 1000:
            errors.append("Description must be 1000 characters or less")
        
        keywords = metadata.get('keywords', [])
        if len(keywords) > 50:
            errors.append("Maximum 50 keywords allowed")
        
        # Check for forbidden words
        forbidden = ["shutterstock", "watermark", "copyright", "royalty"]
        title_lower = metadata.get('title', '').lower()
        desc_lower = metadata.get('description', '').lower()
        
        for word in forbidden:
            if word in title_lower or word in desc_lower:
                errors.append(f"Forbidden word '{word}' found in title or description")
        
        return len(errors) == 0, errors

# ----------------------------- Adobe Stock API ----------------------------- #

class AdobeStockAPI(PlatformAPI):
    """Adobe Stock API integration"""
    
    def __init__(self, credentials: PlatformCredentials):
        super().__init__(credentials, rate_limit=10)  # 10 requests per second
        self.base_url = "https://stock-upload.adobe.io/v2"
    
    def authenticate(self) -> bool:
        """Authenticate with Adobe Stock API"""
        try:
            # Adobe uses OAuth 2.0, simplified for demo
            headers = {
                "Authorization": f"Bearer {self.credentials.access_token}",
                "x-api-key": self.credentials.api_key
            }
            
            response = self.session.get(
                f"{self.base_url}/user/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Adobe Stock authentication successful")
                return True
            else:
                logger.error(f"Adobe Stock authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Adobe Stock authentication error: {e}")
            return False
    
    def upload_image(self, image_path: Path, metadata: Dict) -> UploadResult:
        """Upload image to Adobe Stock"""
        self._rate_limit_wait()
        
        try:
            # Validate metadata
            is_valid, errors = self.validate_metadata(metadata)
            if not is_valid:
                return UploadResult(
                    success=False,
                    platform="adobe_stock",
                    filename=image_path.name,
                    error_message=f"Validation errors: {'; '.join(errors)}"
                )
            
            # Step 1: Create submission
            headers = {
                "Authorization": f"Bearer {self.credentials.access_token}",
                "x-api-key": self.credentials.api_key,
                "Content-Type": "application/json"
            }
            
            submission_data = {
                "submission_name": metadata['title'],
                "submitter_tags": metadata['keywords'][:49],  # Max 49 for Adobe
                "category": metadata.get('category', 'Graphics'),
                "content_type": "photo"
            }
            
            # Create submission
            response = self.session.post(
                f"{self.base_url}/submissions",
                headers=headers,
                json=submission_data
            )
            
            if response.status_code not in [200, 201]:
                return UploadResult(
                    success=False,
                    platform="adobe_stock",
                    filename=image_path.name,
                    error_message=f"Failed to create submission: {response.text}"
                )
            
            submission_id = response.json()['id']
            
            # Step 2: Upload file
            with open(image_path, 'rb') as f:
                files = {
                    'content': (image_path.name, f, 'image/jpeg')
                }
                
                upload_headers = {
                    "Authorization": f"Bearer {self.credentials.access_token}",
                    "x-api-key": self.credentials.api_key
                }
                
                upload_response = self.session.post(
                    f"{self.base_url}/submissions/{submission_id}/content",
                    headers=upload_headers,
                    files=files,
                    timeout=300
                )
            
            if upload_response.status_code in [200, 201]:
                return UploadResult(
                    success=True,
                    platform="adobe_stock",
                    filename=image_path.name,
                    upload_id=submission_id,
                    metadata=upload_response.json()
                )
            else:
                return UploadResult(
                    success=False,
                    platform="adobe_stock",
                    filename=image_path.name,
                    error_message=f"Upload failed: {upload_response.text}"
                )
                
        except Exception as e:
            return UploadResult(
                success=False,
                platform="adobe_stock",
                filename=image_path.name,
                error_message=str(e)
            )
    
    def get_upload_status(self, upload_id: str) -> Dict:
        """Get status of uploaded image on Adobe Stock"""
        try:
            headers = {
                "Authorization": f"Bearer {self.credentials.access_token}",
                "x-api-key": self.credentials.api_key
            }
            
            response = self.session.get(
                f"{self.base_url}/submissions/{upload_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def validate_metadata(self, metadata: Dict) -> Tuple[bool, List[str]]:
        """Validate metadata for Adobe Stock requirements"""
        is_valid, errors = super().validate_metadata(metadata)
        
        # Adobe Stock specific validations
        keywords = metadata.get('keywords', [])
        if len(keywords) > 49:
            errors.append("Maximum 49 keywords allowed for Adobe Stock")
        
        # Check minimum keyword requirement
        if len(keywords) < 7:
            errors.append("Minimum 7 keywords required for Adobe Stock")
        
        # Check for forbidden words
        forbidden = ["adobe", "stock", "watermark"]
        title_lower = metadata.get('title', '').lower()
        desc_lower = metadata.get('description', '').lower()
        
        for word in forbidden:
            if word in title_lower or word in desc_lower:
                errors.append(f"Forbidden word '{word}' found in title or description")
        
        return len(errors) == 0, errors

# ----------------------------- Getty Images API ----------------------------- #

class GettyImagesAPI(PlatformAPI):
    """Getty Images API integration (simplified)"""
    
    def __init__(self, credentials: PlatformCredentials):
        super().__init__(credentials, rate_limit=5)  # Conservative rate limit
        self.base_url = "https://api.gettyimages.com/v3"
    
    def authenticate(self) -> bool:
        """Authenticate with Getty Images API"""
        # Getty Images has a complex contributor workflow
        # This is a simplified implementation
        logger.info("Getty Images API authentication (simplified)")
        return True
    
    def upload_image(self, image_path: Path, metadata: Dict) -> UploadResult:
        """Upload image to Getty Images (simplified)"""
        # Getty Images requires special contributor agreements and workflows
        # This is a placeholder implementation
        return UploadResult(
            success=False,
            platform="getty_images",
            filename=image_path.name,
            error_message="Getty Images upload requires special contributor setup"
        )
    
    def get_upload_status(self, upload_id: str) -> Dict:
        """Get status of uploaded image on Getty Images"""
        return {"status": "not_implemented"}

# ----------------------------- Platform Factory ----------------------------- #

class PlatformFactory:
    """Factory class to create platform API instances"""
    
    @staticmethod
    def create_platform_api(platform: str, credentials: PlatformCredentials) -> PlatformAPI:
        """Create platform API instance"""
        if platform.lower() == "shutterstock":
            return ShutterstockAPI(credentials)
        elif platform.lower() == "adobe_stock":
            return AdobeStockAPI(credentials)
        elif platform.lower() == "getty_images":
            return GettyImagesAPI(credentials)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

# ----------------------------- Upload Manager ----------------------------- #

class UploadManager:
    """Manages uploads across multiple platforms"""
    
    def __init__(self):
        self.platforms = {}
        self._setup_platforms()
    
    def _setup_platforms(self):
        """Setup platform APIs with credentials from environment"""
        
        # Shutterstock
        if SHUTTERSTOCK_API_KEY:
            credentials = PlatformCredentials(
                api_key=SHUTTERSTOCK_API_KEY,
                secret=SHUTTERSTOCK_SECRET
            )
            self.platforms["shutterstock"] = PlatformFactory.create_platform_api("shutterstock", credentials)
        
        # Adobe Stock
        if ADOBE_STOCK_API_KEY:
            credentials = PlatformCredentials(
                api_key=ADOBE_STOCK_API_KEY,
                secret=ADOBE_STOCK_SECRET
            )
            self.platforms["adobe_stock"] = PlatformFactory.create_platform_api("adobe_stock", credentials)
        
        # Getty Images
        if GETTY_API_KEY:
            credentials = PlatformCredentials(
                api_key=GETTY_API_KEY,
                secret=GETTY_SECRET
            )
            self.platforms["getty_images"] = PlatformFactory.create_platform_api("getty_images", credentials)
    
    def authenticate_all(self) -> Dict[str, bool]:
        """Authenticate with all configured platforms"""
        results = {}
        
        for platform_name, platform_api in self.platforms.items():
            try:
                results[platform_name] = platform_api.authenticate()
            except Exception as e:
                logger.error(f"Authentication failed for {platform_name}: {e}")
                results[platform_name] = False
        
        return results
    
    def upload_to_platform(self, platform_name: str, image_path: Path, metadata: Dict) -> UploadResult:
        """Upload image to specific platform"""
        if platform_name not in self.platforms:
            return UploadResult(
                success=False,
                platform=platform_name,
                filename=image_path.name,
                error_message=f"Platform {platform_name} not configured"
            )
        
        platform_api = self.platforms[platform_name]
        return platform_api.upload_image(image_path, metadata)
    
    def upload_to_multiple_platforms(self, platforms: List[str], image_path: Path, 
                                   metadata: Dict) -> List[UploadResult]:
        """Upload image to multiple platforms"""
        results = []
        
        for platform_name in platforms:
            result = self.upload_to_platform(platform_name, image_path, metadata)
            results.append(result)
            
            # Add delay between uploads to different platforms
            time.sleep(1)
        
        return results
    
    def get_platform_status(self, platform_name: str) -> Dict:
        """Get platform configuration status"""
        if platform_name not in self.platforms:
            return {"configured": False, "authenticated": False}
        
        try:
            authenticated = self.platforms[platform_name].authenticate()
            return {"configured": True, "authenticated": authenticated}
        except Exception:
            return {"configured": True, "authenticated": False}

# ----------------------------- Upload Utilities ----------------------------- #

def prepare_metadata_for_platform(metadata: Dict, platform: str) -> Dict:
    """Prepare metadata for specific platform requirements"""
    platform_config = get_platform_config(platform)
    
    # Create platform-specific metadata
    platform_metadata = {
        "title": metadata.get("title", "")[:platform_config["max_title_length"]],
        "description": metadata.get("description", "")[:platform_config["max_description_length"]],
        "keywords": metadata.get("keywords", [])[:platform_config["max_keywords"]],
        "category": metadata.get("category", ""),
    }
    
    # Add platform-specific fields
    if platform == "shutterstock":
        platform_metadata["editorial"] = False
        platform_metadata["mature"] = False
    elif platform == "adobe_stock":
        platform_metadata["content_type"] = "photo"
        platform_metadata["releases"] = []
    
    return platform_metadata

def batch_upload_images(upload_manager: UploadManager, image_paths: List[Path], 
                       metadata_list: List[Dict], platforms: List[str]) -> List[List[UploadResult]]:
    """Batch upload images to multiple platforms"""
    results = []
    
    for image_path, metadata in zip(image_paths, metadata_list):
        image_results = []
        
        for platform in platforms:
            # Prepare platform-specific metadata
            platform_metadata = prepare_metadata_for_platform(metadata, platform)
            
            # Upload to platform
            result = upload_manager.upload_to_platform(platform, image_path, platform_metadata)
            image_results.append(result)
            
            logger.info(f"Upload to {platform}: {'✅' if result.success else '❌'} {image_path.name}")
        
        results.append(image_results)
    
    return results

# ----------------------------- Mock Platform for Testing ----------------------------- #

class MockPlatformAPI(PlatformAPI):
    """Mock platform API for testing without real uploads"""
    
    def __init__(self, platform_name: str = "mock"):
        credentials = PlatformCredentials(api_key="mock_key")
        super().__init__(credentials)
        self.platform_name = platform_name
    
    def authenticate(self) -> bool:
        """Mock authentication"""
        time.sleep(0.1)  # Simulate network delay
        return True
    
    def upload_image(self, image_path: Path, metadata: Dict) -> UploadResult:
        """Mock image upload"""
        time.sleep(2)  # Simulate upload time
        
        # Simulate occasional failures
        import random
        if random.random() < 0.1:  # 10% failure rate
            return UploadResult(
                success=False,
                platform=self.platform_name,
                filename=image_path.name,
                error_message="Mock upload failure"
            )
        
        # Generate mock upload ID
        upload_id = hashlib.md5(f"{image_path.name}_{time.time()}".encode()).hexdigest()[:12]
        
        return UploadResult(
            success=True,
            platform=self.platform_name,
            filename=image_path.name,
            upload_id=upload_id,
            metadata={"status": "uploaded", "mock": True}
        )
    
    def get_upload_status(self, upload_id: str) -> Dict:
        """Mock upload status"""
        return {
            "id": upload_id,
            "status": "processed",
            "mock": True
        }