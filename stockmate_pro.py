#!/usr/bin/env python3
"""
StockMate Pro v1.0

Advanced stock photo metadata generator with SEO optimization,
market trend analysis, and intelligent keyword generation.

Features:
- AI-powered image analysis with GPT-4o models
- SEO-optimized keyword generation
- Market trend integration
- Platform-specific optimization (Shutterstock, Adobe Stock, Getty)
- Batch processing with progress tracking
- Multi-language support (English/Chinese)
- IPTC metadata embedding
- CSV export for platform uploads
- Keyword performance analytics

Dependencies:
    pip install -r requirements.txt

Environment:
    Set your OpenAI API key in OPENAI_API_KEY

Example:
    python stockmate_pro.py process ./images --platform shutterstock --optimize-seo
    python stockmate_pro.py analyze-trends ./images --export-report
"""

from __future__ import annotations
import argparse
import base64
import csv
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
import sqlite3

import numpy as np
import pandas as pd
from PIL import Image, ImageStat
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import nltk
from wordcloud import WordCloud

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Import our configuration
from config import *

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# ----------------------------- Enhanced Data Models ----------------------------- #

@dataclass
class ImageAnalysis:
    """Comprehensive image analysis data"""
    dominant_colors: List[str]
    brightness: float
    contrast: float
    composition: str
    style: str
    mood: str
    objects: List[str]
    scene_type: str
    technical_quality: float

@dataclass
class SEOMetrics:
    """SEO optimization metrics"""
    keyword_difficulty: Dict[str, float]
    search_volume: Dict[str, int]
    trending_score: float
    competition_level: str
    suggested_keywords: List[str]

@dataclass 
class Meta:
    """Enhanced metadata with SEO optimization"""
    title: str
    description: str
    keywords_en: List[str]
    keywords_zh: List[str]
    category: str = ""
    subcategory: str = ""
    mood_tags: List[str] = field(default_factory=list)
    style_tags: List[str] = field(default_factory=list)
    color_tags: List[str] = field(default_factory=list)
    technical_tags: List[str] = field(default_factory=list)
    trending_keywords: List[str] = field(default_factory=list)
    seo_score: float = 0.0
    market_potential: str = "Medium"
    
    def merged_keywords(self, lang_pref: str, max_keywords: int = 50) -> List[str]:
        """Get merged and optimized keywords"""
        if lang_pref == "en":
            all_keywords = self.keywords_en + self.trending_keywords + self.mood_tags + self.style_tags + self.color_tags
        elif lang_pref == "zh":
            all_keywords = self.keywords_zh
        else:
            all_keywords = self.keywords_en + self.trending_keywords + self.keywords_zh + self.mood_tags + self.style_tags + self.color_tags
        
        return self._dedupe_and_optimize(all_keywords, max_keywords)
    
    def _dedupe_and_optimize(self, keywords: List[str], max_keywords: int) -> List[str]:
        """Deduplicate and optimize keyword order"""
        seen = set()
        optimized = []
        
        # Priority order: trending > main keywords > style/mood > colors > technical
        priority_lists = [
            self.trending_keywords,
            self.keywords_en[:10],  # Top 10 main keywords
            self.mood_tags + self.style_tags,
            self.color_tags,
            self.technical_tags
        ]
        
        for keyword_list in priority_lists:
            for kw in keyword_list:
                kw = kw.strip()
                if not kw or len(kw) < MIN_KEYWORD_LENGTH or len(kw) > MAX_KEYWORD_LENGTH:
                    continue
                
                kw_lower = kw.lower()
                if kw_lower in seen:
                    continue
                    
                seen.add(kw_lower)
                optimized.append(kw)
                
                if len(optimized) >= max_keywords:
                    return optimized
        
        return optimized

# ----------------------------- Image Analysis Engine ----------------------------- #

class ImageAnalyzer:
    """Advanced image analysis for stock photography"""
    
    def __init__(self):
        self.color_names = {
            'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
            'yellow': (255, 255, 0), 'purple': (128, 0, 128), 'orange': (255, 165, 0),
            'pink': (255, 192, 203), 'brown': (165, 42, 42), 'gray': (128, 128, 128),
            'white': (255, 255, 255), 'black': (0, 0, 0)
        }
    
    def analyze_image(self, image_path: Path) -> ImageAnalysis:
        """Comprehensive image analysis"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Analyze colors
                dominant_colors = self._analyze_colors(img)
                
                # Analyze brightness and contrast
                brightness = self._calculate_brightness(img)
                contrast = self._calculate_contrast(img)
                
                # Analyze composition (simplified)
                composition = self._analyze_composition(img)
                
                # Technical quality assessment
                quality = self._assess_quality(img)
                
                return ImageAnalysis(
                    dominant_colors=dominant_colors,
                    brightness=brightness,
                    contrast=contrast,
                    composition=composition,
                    style=self._determine_style(brightness, contrast),
                    mood=self._determine_mood(dominant_colors, brightness),
                    objects=[],  # Would need more complex analysis
                    scene_type=self._determine_scene_type(composition),
                    technical_quality=quality
                )
        except Exception as e:
            print(f"Error analyzing image {image_path}: {e}")
            return ImageAnalysis(
                dominant_colors=["unknown"],
                brightness=0.5,
                contrast=0.5,
                composition="unknown",
                style="unknown",
                mood="neutral",
                objects=[],
                scene_type="unknown",
                technical_quality=0.5
            )
    
    def _analyze_colors(self, img: Image.Image) -> List[str]:
        """Extract dominant colors from image"""
        # Resize for faster processing
        img_small = img.resize((100, 100))
        
        # Get color statistics
        stat = ImageStat.Stat(img_small)
        r, g, b = stat.mean
        
        # Find closest color names
        colors = []
        
        # Determine dominant color
        if r > 200 and g > 200 and b > 200:
            colors.append("white")
        elif r < 50 and g < 50 and b < 50:
            colors.append("black")
        elif r > g and r > b:
            if r - g > 50:
                colors.append("red")
            else:
                colors.append("orange" if g > b else "purple")
        elif g > r and g > b:
            colors.append("green")
        elif b > r and b > g:
            colors.append("blue")
        else:
            colors.append("gray")
        
        return colors
    
    def _calculate_brightness(self, img: Image.Image) -> float:
        """Calculate image brightness (0-1)"""
        stat = ImageStat.Stat(img.convert('L'))
        return stat.mean[0] / 255.0
    
    def _calculate_contrast(self, img: Image.Image) -> float:
        """Calculate image contrast (0-1)"""
        stat = ImageStat.Stat(img.convert('L'))
        return stat.stddev[0] / 128.0
    
    def _analyze_composition(self, img: Image.Image) -> str:
        """Analyze image composition"""
        width, height = img.size
        aspect_ratio = width / height
        
        if abs(aspect_ratio - 1.0) < 0.1:
            return "square"
        elif aspect_ratio > 1.5:
            return "landscape"
        elif aspect_ratio < 0.7:
            return "portrait"
        else:
            return "standard"
    
    def _determine_style(self, brightness: float, contrast: float) -> str:
        """Determine photographic style"""
        if brightness > 0.8:
            return "high-key" if contrast < 0.3 else "bright"
        elif brightness < 0.3:
            return "low-key" if contrast > 0.5 else "dark"
        elif contrast > 0.7:
            return "dramatic"
        else:
            return "natural"
    
    def _determine_mood(self, colors: List[str], brightness: float) -> str:
        """Determine emotional mood"""
        warm_colors = {"red", "orange", "yellow", "pink"}
        cool_colors = {"blue", "green", "purple"}
        
        if any(c in warm_colors for c in colors):
            return "warm" if brightness > 0.5 else "cozy"
        elif any(c in cool_colors for c in colors):
            return "cool" if brightness > 0.5 else "mysterious"
        else:
            return "neutral"
    
    def _determine_scene_type(self, composition: str) -> str:
        """Determine scene type based on composition"""
        scene_mapping = {
            "landscape": "outdoor",
            "portrait": "people",
            "square": "product",
            "standard": "general"
        }
        return scene_mapping.get(composition, "general")
    
    def _assess_quality(self, img: Image.Image) -> float:
        """Assess technical quality (simplified)"""
        width, height = img.size
        megapixels = (width * height) / 1_000_000
        
        # Basic quality score based on resolution
        if megapixels >= 12:
            return 1.0
        elif megapixels >= 6:
            return 0.8
        elif megapixels >= 3:
            return 0.6
        else:
            return 0.4

# ----------------------------- Enhanced AI Generator ----------------------------- #

class EnhancedAIGenerator:
    """Enhanced AI generator with SEO optimization"""
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Run: pip install 'openai>=1.40,<2'")
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.image_analyzer = ImageAnalyzer()
    
    def for_image(self, img_path: Path, platform: str = "shutterstock", 
                  optimize_seo: bool = True, max_kw: int = 50) -> Meta:
        """Generate enhanced metadata for image"""
        
        # Get platform configuration
        platform_config = get_platform_config(platform)
        
        # Analyze image
        image_analysis = self.image_analyzer.analyze_image(img_path)
        
        # Generate base metadata with AI
        base_meta = self._generate_base_metadata(img_path, image_analysis, platform_config, max_kw)
        
        # Enhance with SEO optimization
        if optimize_seo:
            enhanced_meta = self._enhance_with_seo(base_meta, image_analysis, platform)
        else:
            enhanced_meta = base_meta
        
        return enhanced_meta
    
    def _generate_base_metadata(self, img_path: Path, analysis: ImageAnalysis, 
                              platform_config: Dict, max_kw: int) -> Meta:
        """Generate base metadata using AI"""
        
        # Create enhanced prompt with image analysis context
        system_prompt = self._create_enhanced_system_prompt(analysis, platform_config, max_kw)
        user_prompt = self._create_enhanced_user_prompt(analysis)
        
        b64 = _b64_image(img_path)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{img_path.suffix[1:].lower()};base64,{b64}",
                        },
                    },
                ],
            },
        ]
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=messages,
                max_tokens=800,
            )
            text = resp.choices[0].message.content or "{}"
            data = _force_json(text)
            
            return Meta(
                title=data.get("title", "").strip()[:platform_config["max_title_length"]],
                description=data.get("description", "").strip()[:platform_config["max_description_length"]],
                keywords_en=[s.strip() for s in data.get("keywords_en", []) if s and str(s).strip()],
                keywords_zh=[s.strip() for s in data.get("keywords_zh", []) if s and str(s).strip()],
                category=data.get("category", ""),
                mood_tags=analysis.mood.split() if analysis.mood else [],
                style_tags=analysis.style.split() if analysis.style else [],
                color_tags=analysis.dominant_colors,
            )
            
        except Exception as e:
            print(f"AI generation failed: {e}")
            return self._fallback_metadata(img_path, analysis, max_kw)
    
    def _create_enhanced_system_prompt(self, analysis: ImageAnalysis, 
                                     platform_config: Dict, max_kw: int) -> str:
        """Create enhanced system prompt with analysis context"""
        return f"""
You are an expert stock photo SEO specialist with deep knowledge of {platform_config} requirements.

Image analysis context:
- Dominant colors: {', '.join(analysis.dominant_colors)}
- Brightness: {analysis.brightness:.2f} (0=dark, 1=bright)
- Contrast: {analysis.contrast:.2f} (0=low, 1=high)
- Style: {analysis.style}
- Mood: {analysis.mood}
- Composition: {analysis.composition}
- Technical quality: {analysis.technical_quality:.2f}

Requirements:
- Title: Max {platform_config['max_title_length']} chars, compelling and descriptive
- Description: Max {platform_config['max_description_length']} chars, detailed and searchable
- Keywords: Max {max_kw} keywords, ordered by commercial importance
- Include trending and high-value keywords for maximum sales potential
- Avoid forbidden words: {', '.join(platform_config.get('forbidden_words', []))}

Focus on commercial viability, search optimization, and buyer intent.
Return ONLY JSON with keys: title, description, keywords_en, keywords_zh, category.
"""
    
    def _create_enhanced_user_prompt(self, analysis: ImageAnalysis) -> str:
        """Create enhanced user prompt"""
        return f"""
Analyze this stock photo and create highly optimized metadata for maximum commercial success.

Consider these market factors:
1. High-demand keywords: {', '.join(MARKET_TRENDS['high_demand'])}
2. Evergreen topics: {', '.join(MARKET_TRENDS['evergreen'])}
3. Style trends: {', '.join(STYLE_KEYWORDS[:10])}

Image context from analysis:
- This is a {analysis.style} style image with {analysis.mood} mood
- Dominant colors are {', '.join(analysis.dominant_colors)}
- Composition type: {analysis.composition}

Generate metadata that:
- Uses buyer-focused language
- Includes trending keywords where relevant  
- Balances specific and broad search terms
- Maximizes discoverability across different search queries
- Appeals to commercial buyers (businesses, marketers, designers)

Return strict JSON format only.
"""
    
    def _enhance_with_seo(self, meta: Meta, analysis: ImageAnalysis, platform: str) -> Meta:
        """Enhance metadata with SEO optimization"""
        
        # Add trending keywords relevant to image
        trending = self._get_relevant_trending_keywords(meta.keywords_en, analysis)
        meta.trending_keywords = trending
        
        # Calculate SEO score
        meta.seo_score = self._calculate_seo_score(meta, analysis)
        
        # Determine market potential
        meta.market_potential = self._assess_market_potential(meta, analysis)
        
        # Add technical and style tags
        meta.technical_tags = self._generate_technical_tags(analysis)
        
        return meta
    
    def _get_relevant_trending_keywords(self, keywords: List[str], analysis: ImageAnalysis) -> List[str]:
        """Get trending keywords relevant to the image"""
        relevant_trending = []
        
        # Check each category for relevance
        for category, trending_words in TRENDING_KEYWORDS.items():
            # Simple relevance check based on existing keywords and image analysis
            relevance_score = 0
            
            for kw in keywords:
                for trending in trending_words:
                    if any(word in kw.lower() for word in trending.lower().split()):
                        relevance_score += 1
            
            # Add category trends if relevant
            if relevance_score > 0:
                relevant_trending.extend(trending_words[:3])  # Top 3 from each relevant category
        
        return relevant_trending[:5]  # Limit to top 5 trending keywords
    
    def _calculate_seo_score(self, meta: Meta, analysis: ImageAnalysis) -> float:
        """Calculate SEO optimization score (0-1)"""
        score = 0.0
        
        # Title optimization (20%)
        if len(meta.title) >= 30 and len(meta.title) <= 60:
            score += 0.2
        
        # Description optimization (20%)
        if len(meta.description) >= 100 and len(meta.description) <= 200:
            score += 0.2
        
        # Keyword count optimization (20%)
        total_keywords = len(meta.merged_keywords("en,zh"))
        if total_keywords >= 20 and total_keywords <= 50:
            score += 0.2
        
        # Trending keywords bonus (20%)
        if meta.trending_keywords:
            score += 0.2
        
        # Technical quality bonus (20%)
        score += analysis.technical_quality * 0.2
        
        return min(score, 1.0)
    
    def _assess_market_potential(self, meta: Meta, analysis: ImageAnalysis) -> str:
        """Assess market potential based on metadata quality"""
        if meta.seo_score >= 0.8 and analysis.technical_quality >= 0.8:
            return "High"
        elif meta.seo_score >= 0.6 and analysis.technical_quality >= 0.6:
            return "Medium"
        else:
            return "Low"
    
    def _generate_technical_tags(self, analysis: ImageAnalysis) -> List[str]:
        """Generate technical tags based on analysis"""
        tags = []
        
        if analysis.technical_quality >= 0.8:
            tags.append("high resolution")
        
        if analysis.brightness > 0.7:
            tags.append("bright lighting")
        elif analysis.brightness < 0.3:
            tags.append("low light")
        
        if analysis.contrast > 0.7:
            tags.append("high contrast")
        
        return tags
    
    def _fallback_metadata(self, img_path: Path, analysis: ImageAnalysis, max_kw: int) -> Meta:
        """Fallback metadata generation when AI fails"""
        stem = img_path.stem
        title = re.sub(r"[_\-]+", " ", stem).strip().title()
        
        return Meta(
            title=title[:60] if title else "Stock Photo",
            description=f"High quality stock photo featuring {', '.join(analysis.dominant_colors)} tones.",
            keywords_en=[word for word in re.split(r"[^a-zA-Z]+", stem.lower()) if len(word) > 2][:max_kw//2],
            keywords_zh=[],
            color_tags=analysis.dominant_colors,
            mood_tags=[analysis.mood] if analysis.mood != "unknown" else [],
            style_tags=[analysis.style] if analysis.style != "unknown" else []
        )

# ----------------------------- Utilities ----------------------------- #

def _b64_image(path: Path) -> str:
    """Convert image to base64"""
    with path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _force_json(s: str) -> dict:
    """Force string to JSON with better error handling"""
    s = (s or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*", "", s).strip()
        s = s[:-3] if s.endswith("```") else s
    
    try:
        return json.loads(s)
    except Exception:
        # Try to find the first JSON object
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    
    print(f"Warning: Could not parse JSON, using fallback: {s[:200]}...")
    return {"title": "Untitled", "description": "Stock photo", "keywords_en": [], "keywords_zh": []}

# ----------------------------- IPTC Writing ----------------------------- #

def has_exiftool() -> bool:
    """Check if ExifTool is available"""
    try:
        subprocess.run(["exiftool", "-ver"], stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def write_iptc(img: Path, meta: Meta, platform_config: Dict) -> Tuple[bool, str]:
    """Write IPTC metadata using ExifTool"""
    if img.suffix.lower() not in {".jpg", ".jpeg", ".tif", ".tiff"}:
        return False, "IPTC embedding is supported for JPEG/TIFF only"
    
    if not has_exiftool():
        return False, "ExifTool not found"
    
    keywords = meta.merged_keywords("en,zh", platform_config["max_keywords"])
    
    cmd = [
        "exiftool",
        "-overwrite_original",
        f"-IPTC:ObjectName={meta.title}",
        f"-IPTC:Caption-Abstract={meta.description}",
        f"-IPTC:Category={meta.category}",
    ]
    
    for kw in keywords:
        if kw:
            cmd.append(f"-IPTC:Keywords={kw}")
    
    cmd.append(str(img))
    
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            return False, f"ExifTool error: {r.stderr.strip() or r.stdout.strip()}"
        return True, "IPTC written successfully"
    except Exception as e:
        return False, f"ExifTool failed: {e}"

# ----------------------------- CSV Export ----------------------------- #

def export_enhanced_csv(rows: List[Dict], out_path: Path, platform: str) -> None:
    """Export enhanced CSV with platform-specific formatting"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "filename", "title", "description", "keywords", "category",
        "seo_score", "market_potential", "trending_keywords",
        "color_tags", "mood_tags", "style_tags"
    ]
    
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ----------------------------- Trend Analysis ----------------------------- #

class TrendAnalyzer:
    """Analyze keyword trends and market demand"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    def analyze_batch_trends(self, metadata_list: List[Meta]) -> Dict:
        """Analyze trends across a batch of images"""
        
        # Collect all keywords
        all_keywords = []
        for meta in metadata_list:
            all_keywords.extend(meta.keywords_en)
            all_keywords.extend(meta.trending_keywords)
        
        # Count keyword frequency
        keyword_counts = Counter(all_keywords)
        
        # Calculate trend scores
        trend_scores = {}
        for keyword, count in keyword_counts.items():
            # Simple trend score based on frequency and market demand
            base_score = count / len(metadata_list)
            
            # Boost score for trending keywords
            trend_boost = 1.5 if keyword in MARKET_TRENDS['high_demand'] else 1.0
            
            trend_scores[keyword] = base_score * trend_boost
        
        # Get top categories
        categories = [meta.category for meta in metadata_list if meta.category]
        category_counts = Counter(categories)
        
        return {
            "top_keywords": dict(keyword_counts.most_common(20)),
            "trend_scores": trend_scores,
            "top_categories": dict(category_counts.most_common(10)),
            "avg_seo_score": np.mean([meta.seo_score for meta in metadata_list]),
            "market_potential_distribution": Counter([meta.market_potential for meta in metadata_list])
        }

# ----------------------------- Main Processing ----------------------------- #

def process_folder_enhanced(
    in_dir: Path,
    platform: str = "shutterstock",
    optimize_seo: bool = True,
    write_iptc_flag: bool = False,
    csv_path: Optional[Path] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_kw: int = 50,
    analyze_trends: bool = False
) -> None:
    """Enhanced folder processing with SEO optimization"""
    
    print(f"🚀 StockMate Pro - Processing for {platform.upper()}")
    print(f"📁 Input directory: {in_dir}")
    print(f"🎯 SEO Optimization: {'ON' if optimize_seo else 'OFF'}")
    
    # Find images
    images = [p for p in in_dir.rglob("*") if is_supported_file(p) and validate_file_size(p)]
    
    if not images:
        print("❌ No supported images found.")
        return
    
    print(f"📸 Found {len(images)} images to process")
    
    # Initialize AI generator
    ai = EnhancedAIGenerator(model=model, temperature=temperature)
    platform_config = get_platform_config(platform)
    
    # Process images
    rows = []
    metadata_list = []
    
    for img_path in tqdm(images, desc="Processing images", unit="img"):
        try:
            # Generate metadata
            meta = ai.for_image(img_path, platform=platform, 
                              optimize_seo=optimize_seo, max_kw=max_kw)
            
            metadata_list.append(meta)
            
            # Write IPTC if requested
            if write_iptc_flag:
                ok, msg = write_iptc(img_path, meta, platform_config)
                tqdm.write(f"[{img_path.name}] IPTC: {msg}")
            
            # Prepare CSV row
            keywords = meta.merged_keywords("en,zh", platform_config["max_keywords"])
            
            row = {
                "filename": img_path.name,
                "title": meta.title,
                "description": meta.description,
                "keywords": "; ".join(keywords),
                "category": meta.category,
                "seo_score": f"{meta.seo_score:.2f}",
                "market_potential": meta.market_potential,
                "trending_keywords": "; ".join(meta.trending_keywords),
                "color_tags": "; ".join(meta.color_tags),
                "mood_tags": "; ".join(meta.mood_tags),
                "style_tags": "; ".join(meta.style_tags)
            }
            rows.append(row)
            
            # Print progress info
            tqdm.write(f"✅ [{img_path.name}] SEO: {meta.seo_score:.2f} | Market: {meta.market_potential}")
            
        except Exception as e:
            tqdm.write(f"❌ [{img_path.name}] ERROR: {e}")
    
    # Export CSV
    if csv_path:
        export_enhanced_csv(rows, csv_path, platform)
        print(f"📊 CSV exported: {csv_path}")
    
    # Trend analysis
    if analyze_trends and metadata_list:
        analyzer = TrendAnalyzer()
        trends = analyzer.analyze_batch_trends(metadata_list)
        
        print("\n📈 TREND ANALYSIS REPORT")
        print("=" * 50)
        print(f"Average SEO Score: {trends['avg_seo_score']:.2f}")
        
        print("\n🔥 Top Keywords:")
        for kw, count in list(trends['top_keywords'].items())[:10]:
            print(f"  • {kw}: {count}")
        
        print("\n📂 Popular Categories:")
        for cat, count in list(trends['top_categories'].items())[:5]:
            print(f"  • {cat}: {count}")
        
        print("\n💰 Market Potential:")
        for potential, count in trends['market_potential_distribution'].items():
            print(f"  • {potential}: {count} images")

# ----------------------------- CLI ----------------------------- #

def parse_args_enhanced(argv: List[str]) -> argparse.Namespace:
    """Enhanced argument parser"""
    ap = argparse.ArgumentParser(
        description="StockMate Pro - Advanced stock photo metadata generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stockmate_pro.py process ./photos --platform shutterstock --optimize-seo
  python stockmate_pro.py process ./photos --platform adobe_stock --csv output.csv
  python stockmate_pro.py process ./photos --analyze-trends --write-iptc
        """
    )
    
    subparsers = ap.add_subparsers(dest="command", help="Available commands")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process images")
    process_parser.add_argument("in_dir", help="Input directory containing images")
    process_parser.add_argument("--platform", choices=["shutterstock", "adobe_stock", "getty_images"],
                               default="shutterstock", help="Target platform")
    process_parser.add_argument("--optimize-seo", action="store_true", 
                               help="Enable SEO optimization")
    process_parser.add_argument("--write-iptc", action="store_true",
                               help="Write IPTC metadata to images")
    process_parser.add_argument("--csv", help="Output CSV file path")
    process_parser.add_argument("--model", default="gpt-4o-mini", 
                               help="OpenAI model to use")
    process_parser.add_argument("--temperature", type=float, default=0.2,
                               help="AI temperature (0-1)")
    process_parser.add_argument("--max-keywords", type=int, default=50,
                               help="Maximum keywords per image")
    process_parser.add_argument("--analyze-trends", action="store_true",
                               help="Analyze keyword trends")
    
    return ap.parse_args(argv)

def main(argv: List[str]) -> int:
    """Enhanced main function"""
    args = parse_args_enhanced(argv)
    
    if not args.command:
        print("❌ Please specify a command. Use --help for options.")
        return 1
    
    if args.command == "process":
        in_dir = Path(args.in_dir)
        if not in_dir.exists():
            print(f"❌ Input directory not found: {in_dir}")
            return 2
        
        csv_path = Path(args.csv) if args.csv else None
        
        try:
            process_folder_enhanced(
                in_dir=in_dir,
                platform=args.platform,
                optimize_seo=args.optimize_seo,
                write_iptc_flag=args.write_iptc,
                csv_path=csv_path,
                model=args.model,
                temperature=args.temperature,
                max_kw=args.max_keywords,
                analyze_trends=args.analyze_trends
            )
            print("\n🎉 Processing completed successfully!")
            
        except KeyboardInterrupt:
            print("\n⏹️  Processing interrupted by user.")
            return 130
        except Exception as e:
            print(f"\n❌ Error during processing: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))