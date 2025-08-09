#!/usr/bin/env python3
"""
Configuration management for StockMate
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class PlatformConfig:
    """Configuration for a stock photo platform"""
    name: str
    max_keywords: int = 50
    max_title_length: int = 60
    max_description_length: int = 220
    supported_formats: list = None
    keyword_separator: str = ";"
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [".jpg", ".jpeg", ".png", ".tif", ".tiff"]

@dataclass
class AIConfig:
    """AI generation configuration"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 500
    system_prompt: str = ""
    user_prompt: str = ""

class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".stockmate" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Default configurations
        self.platforms = {
            "shutterstock": PlatformConfig(
                name="Shutterstock",
                max_keywords=50,
                max_title_length=60,
                max_description_length=220,
                keyword_separator=";"
            ),
            "adobe_stock": PlatformConfig(
                name="Adobe Stock",
                max_keywords=49,
                max_title_length=60,
                max_description_length=220,
                keyword_separator=";"
            ),
            "istock": PlatformConfig(
                name="iStock",
                max_keywords=50,
                max_title_length=60,
                max_description_length=220,
                keyword_separator=";"
            ),
            "getty": PlatformConfig(
                name="Getty Images",
                max_keywords=50,
                max_title_length=60,
                max_description_length=220,
                keyword_separator=";"
            )
        }
        
        self.ai_config = AIConfig()
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Load platform configs
                if 'platforms' in data:
                    for platform_name, platform_data in data['platforms'].items():
                        if platform_name in self.platforms:
                            for key, value in platform_data.items():
                                if hasattr(self.platforms[platform_name], key):
                                    setattr(self.platforms[platform_name], key, value)
                
                # Load AI config
                if 'ai_config' in data:
                    for key, value in data['ai_config'].items():
                        if hasattr(self.ai_config, key):
                            setattr(self.ai_config, key, value)
                            
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config_data = {
                'platforms': {
                    name: asdict(platform) for name, platform in self.platforms.items()
                },
                'ai_config': asdict(self.ai_config)
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")
    
    def get_platform_config(self, platform_name: str) -> Optional[PlatformConfig]:
        """Get configuration for a specific platform"""
        return self.platforms.get(platform_name.lower())
    
    def update_platform_config(self, platform_name: str, **kwargs):
        """Update configuration for a specific platform"""
        platform = self.platforms.get(platform_name.lower())
        if platform:
            for key, value in kwargs.items():
                if hasattr(platform, key):
                    setattr(platform, key, value)
            self.save_config()
    
    def get_supported_platforms(self) -> list:
        """Get list of supported platforms"""
        return list(self.platforms.keys())