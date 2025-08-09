#!/usr/bin/env python3
"""
Configuration settings for StockMate Pro
"""

import os
from pathlib import Path
from typing import Dict, List, Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
CACHE_DIR = BASE_DIR / ".cache"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
for dir_path in [UPLOADS_DIR, EXPORTS_DIR, CACHE_DIR, TEMPLATES_DIR]:
    dir_path.mkdir(exist_ok=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHUTTERSTOCK_API_KEY = os.getenv("SHUTTERSTOCK_API_KEY")
SHUTTERSTOCK_SECRET = os.getenv("SHUTTERSTOCK_SECRET")
ADOBE_STOCK_API_KEY = os.getenv("ADOBE_STOCK_API_KEY")
ADOBE_STOCK_SECRET = os.getenv("ADOBE_STOCK_SECRET")
GETTY_API_KEY = os.getenv("GETTY_API_KEY")
GETTY_SECRET = os.getenv("GETTY_SECRET")

# Application Settings
MAX_KEYWORDS_DEFAULT = int(os.getenv("MAX_KEYWORDS_DEFAULT", 30))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en,zh")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))

# File Processing
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_FORMATS: Set[str] = {
    ext.strip().lower() 
    for ext in os.getenv("SUPPORTED_FORMATS", "jpg,jpeg,png,tiff,tif").split(",")
}

SUPPORTED_EXTS = {f".{fmt}" for fmt in SUPPORTED_FORMATS}

# SEO Settings
KEYWORD_DENSITY_TARGET = float(os.getenv("KEYWORD_DENSITY_TARGET", 0.02))
MIN_KEYWORD_LENGTH = int(os.getenv("MIN_KEYWORD_LENGTH", 3))
MAX_KEYWORD_LENGTH = int(os.getenv("MAX_KEYWORD_LENGTH", 30))

# Platform specific settings
PLATFORM_CONFIGS = {
    "shutterstock": {
        "max_keywords": 50,
        "max_title_length": 200,
        "max_description_length": 1000,
        "required_keywords": ["stock", "photo"],
        "forbidden_words": ["shutterstock", "watermark", "copyright"],
        "categories": [
            "Abstract", "Animals/Wildlife", "Arts", "Backgrounds/Textures",
            "Beauty/Fashion", "Buildings/Landmarks", "Business/Finance",
            "Celebrities", "Education", "Food and Drink", "Healthcare/Medical",
            "Holidays", "Industrial", "Interiors", "Miscellaneous", "Nature",
            "Objects", "Parks/Outdoor", "People", "Religion", "Science",
            "Signs/Symbols", "Sports/Recreation", "Technology", "Transportation",
            "Travel", "Vintage"
        ]
    },
    "adobe_stock": {
        "max_keywords": 49,
        "max_title_length": 200,
        "max_description_length": 1000,
        "required_keywords": [],
        "forbidden_words": ["adobe", "stock", "watermark"],
        "categories": [
            "Animals", "Architecture", "Arts", "Beauty", "Business",
            "Education", "Food", "Health", "Industrial", "Lifestyle",
            "Nature", "People", "Places", "Science", "Sports", "Technology",
            "Transportation", "Travel"
        ]
    },
    "getty_images": {
        "max_keywords": 50,
        "max_title_length": 150,
        "max_description_length": 800,
        "required_keywords": [],
        "forbidden_words": ["getty", "watermark"],
        "categories": [
            "News", "Sports", "Entertainment", "Archival", "Creative"
        ]
    }
}

# Popular trending keywords by category
TRENDING_KEYWORDS = {
    "business": [
        "remote work", "digital transformation", "sustainability",
        "artificial intelligence", "teamwork", "leadership",
        "innovation", "startup", "entrepreneur", "meeting"
    ],
    "lifestyle": [
        "wellness", "mindfulness", "work-life balance", "healthy eating",
        "exercise", "family time", "social media", "minimalism",
        "eco-friendly", "mental health"
    ],
    "technology": [
        "AI", "machine learning", "cloud computing", "cybersecurity",
        "blockchain", "IoT", "5G", "virtual reality", "automation",
        "digital nomad"
    ],
    "nature": [
        "climate change", "renewable energy", "biodiversity",
        "conservation", "sustainable living", "organic farming",
        "green technology", "carbon neutral", "eco-tourism"
    ]
}

# Color keywords for better searchability
COLOR_KEYWORDS = {
    "red": ["crimson", "scarlet", "burgundy", "cherry", "rose"],
    "blue": ["azure", "navy", "cobalt", "turquoise", "indigo"],
    "green": ["emerald", "forest", "mint", "sage", "olive"],
    "yellow": ["golden", "amber", "lemon", "mustard", "cream"],
    "purple": ["violet", "lavender", "magenta", "plum", "mauve"],
    "orange": ["coral", "peach", "tangerine", "apricot", "rust"],
    "pink": ["rose", "blush", "salmon", "fuchsia", "carnation"],
    "brown": ["chocolate", "coffee", "mahogany", "caramel", "bronze"],
    "gray": ["silver", "charcoal", "slate", "ash", "steel"],
    "white": ["ivory", "cream", "pearl", "snow", "vanilla"],
    "black": ["ebony", "jet", "obsidian", "coal", "midnight"]
}

# Style and mood keywords
STYLE_KEYWORDS = [
    "minimalist", "vintage", "modern", "rustic", "elegant",
    "dramatic", "soft", "bold", "artistic", "professional",
    "casual", "formal", "abstract", "realistic", "creative"
]

MOOD_KEYWORDS = [
    "peaceful", "energetic", "mysterious", "romantic", "playful",
    "serious", "joyful", "calm", "exciting", "inspiring",
    "melancholic", "optimistic", "dynamic", "serene", "powerful"
]

# Market research data (example trends)
MARKET_TRENDS = {
    "high_demand": [
        "remote work", "sustainability", "diversity", "mental health",
        "AI technology", "electric vehicles", "plant-based", "minimalism"
    ],
    "seasonal": {
        "spring": ["renewal", "growth", "fresh", "blooming"],
        "summer": ["vacation", "beach", "outdoor", "bright"],
        "autumn": ["harvest", "cozy", "warm colors", "thanksgiving"],
        "winter": ["holiday", "celebration", "snow", "family"]
    },
    "evergreen": [
        "business", "technology", "nature", "people", "food",
        "travel", "education", "health", "lifestyle", "abstract"
    ]
}

def get_platform_config(platform: str) -> Dict:
    """Get configuration for a specific platform"""
    return PLATFORM_CONFIGS.get(platform.lower(), PLATFORM_CONFIGS["shutterstock"])

def is_supported_file(file_path: Path) -> bool:
    """Check if file format is supported"""
    return file_path.suffix.lower() in SUPPORTED_EXTS

def validate_file_size(file_path: Path) -> bool:
    """Check if file size is within limits"""
    try:
        return file_path.stat().st_size <= MAX_FILE_SIZE_BYTES
    except (OSError, AttributeError):
        return False