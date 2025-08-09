#!/usr/bin/env python3
"""
Enhanced StockMate - Advanced Stock Photo Upload Assistant

A comprehensive tool for batch uploading images to stock photo platforms
with AI-powered metadata generation and automated upload capabilities.

Features:
- AI-powered title, description, and keyword generation
- Support for multiple platforms (Shutterstock, Adobe Stock, iStock, Getty)
- Batch processing with progress tracking
- IPTC metadata embedding
- CSV export for manual uploads
- Automated upload via web automation
- Configuration management
- Upload history tracking

Usage:
    python enhanced_stockmate.py --help
    python enhanced_stockmate.py ./images --platform shutterstock --auto-upload
    python enhanced_stockmate.py ./images --platform adobe_stock --csv output.csv
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Import our modules
from config import Config
from platforms import PlatformManager, UploadResult
from stockmate import AIGenerator, MockAIGenerator, Meta, process_folder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stockmate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedStockMate:
    """Enhanced StockMate with platform integration"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = Config(config_path)
        self.platform_manager = PlatformManager()
        self.upload_history = []
        self.history_file = Path.home() / ".stockmate" / "upload_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_upload_history()
    
    def load_upload_history(self):
        """Load upload history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.upload_history = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load upload history: {e}")
                self.upload_history = []
    
    def save_upload_history(self):
        """Save upload history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.upload_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save upload history: {e}")
    
    def add_upload_record(self, platform: str, image_path: Path, result: UploadResult):
        """Add upload record to history"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "image_path": str(image_path),
            "success": result.success,
            "message": result.message,
            "file_id": result.file_id,
            "url": result.url
        }
        self.upload_history.append(record)
        self.save_upload_history()
    
    def process_images(self, 
                      input_dir: Path,
                      platform: str,
                      lang: str = "en",
                      max_keywords: int = 30,
                      write_iptc: bool = False,
                      csv_path: Optional[Path] = None,
                      auto_upload: bool = False,
                      username: Optional[str] = None,
                      password: Optional[str] = None,
                      mock_ai: bool = False) -> None:
        """Process images with enhanced features"""
        
        # Get platform configuration
        platform_config = self.config.get_platform_config(platform)
        if not platform_config:
            logger.error(f"Unsupported platform: {platform}")
            return
        
        # Initialize AI generator
        if mock_ai:
            ai_generator = MockAIGenerator()
        else:
            try:
                ai_generator = AIGenerator(
                    model=self.config.ai_config.model,
                    temperature=self.config.ai_config.temperature
                )
            except Exception as e:
                logger.error(f"Failed to initialize AI generator: {e}")
                logger.info("Falling back to mock AI generator")
                ai_generator = MockAIGenerator()
        
        # Get platform instance for auto-upload
        platform_instance = None
        if auto_upload:
            platform_instance = self.platform_manager.get_platform(platform, {})
            if not platform_instance:
                logger.error(f"Platform {platform} not supported for auto-upload")
                return
            
            # Login if credentials provided
            if username and password:
                logger.info(f"Logging into {platform}...")
                if not platform_instance.login(username, password):
                    logger.error(f"Failed to login to {platform}")
                    return
                logger.info(f"Successfully logged into {platform}")
        
        # Process images
        images = [p for p in input_dir.rglob("*") 
                 if p.suffix.lower() in platform_config.supported_formats]
        
        if not images:
            logger.info("No supported images found.")
            return
        
        logger.info(f"Found {len(images)} images to process")
        
        results = []
        for image_path in images:
            try:
                logger.info(f"Processing {image_path.name}...")
                
                # Generate metadata
                meta = ai_generator.for_image(image_path, max_keywords)
                
                # Apply platform-specific limits
                keywords = meta.merged_keywords(lang)[:platform_config.max_keywords]
                title = meta.title[:platform_config.max_title_length]
                description = meta.description[:platform_config.max_description_length]
                
                # Write IPTC if requested
                if write_iptc:
                    from stockmate import write_iptc
                    ok, msg = write_iptc(image_path, title, description, keywords)
                    logger.info(f"IPTC write: {msg}")
                
                # Prepare metadata for upload
                metadata = {
                    "title": title,
                    "description": description,
                    "keywords": keywords
                }
                
                # Auto-upload if requested
                if auto_upload and platform_instance:
                    logger.info(f"Uploading {image_path.name} to {platform}...")
                    result = platform_instance.upload_image(image_path, metadata)
                    self.add_upload_record(platform, image_path, result)
                    
                    if result.success:
                        logger.info(f"Successfully uploaded {image_path.name}")
                    else:
                        logger.error(f"Failed to upload {image_path.name}: {result.message}")
                
                # Store result for CSV export
                results.append({
                    "filename": image_path.name,
                    "title": title,
                    "description": description,
                    "keywords": platform_config.keyword_separator.join(keywords),
                    "platform": platform,
                    "processed_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing {image_path.name}: {e}")
        
        # Export CSV if requested
        if csv_path:
            self.export_csv(results, csv_path)
            logger.info(f"CSV exported to {csv_path}")
        
        # Close platform driver
        if platform_instance:
            platform_instance.close_driver()
    
    def export_csv(self, results: List[Dict[str, Any]], csv_path: Path):
        """Export results to CSV"""
        import csv
        
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ["filename", "title", "description", "keywords", "platform", "processed_at"]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result)
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """Get upload statistics"""
        if not self.upload_history:
            return {"total_uploads": 0, "successful_uploads": 0, "failed_uploads": 0}
        
        total = len(self.upload_history)
        successful = sum(1 for record in self.upload_history if record.get("success", False))
        failed = total - successful
        
        return {
            "total_uploads": total,
            "successful_uploads": successful,
            "failed_uploads": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }
    
    def list_platforms(self):
        """List supported platforms"""
        platforms = self.platform_manager.get_supported_platforms()
        print("Supported platforms:")
        for platform in platforms:
            config = self.config.get_platform_config(platform)
            if config:
                print(f"  - {platform}: {config.name}")
    
    def show_stats(self):
        """Show upload statistics"""
        stats = self.get_upload_stats()
        print(f"Upload Statistics:")
        print(f"  Total uploads: {stats['total_uploads']}")
        print(f"  Successful: {stats['successful_uploads']}")
        print(f"  Failed: {stats['failed_uploads']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced StockMate - Advanced Stock Photo Upload Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process images and generate CSV for manual upload
  python enhanced_stockmate.py ./images --platform shutterstock --csv output.csv
  
  # Auto-upload to Adobe Stock (requires credentials)
  python enhanced_stockmate.py ./images --platform adobe_stock --auto-upload --username user@example.com --password pass123
  
  # Process with IPTC embedding
  python enhanced_stockmate.py ./images --platform shutterstock --write-iptc --csv output.csv
  
  # Use mock AI for testing
  python enhanced_stockmate.py ./images --platform shutterstock --mock-ai --csv output.csv
        """
    )
    
    parser.add_argument("input_dir", type=str, help="Input directory containing images")
    parser.add_argument("--platform", type=str, required=True, 
                       help="Target platform (shutterstock, adobe_stock, istock, getty)")
    parser.add_argument("--lang", type=str, default="en", 
                       help="Language preference (en, zh, en,zh)")
    parser.add_argument("--max-keywords", type=int, default=30,
                       help="Maximum keywords per image")
    parser.add_argument("--write-iptc", action="store_true",
                       help="Write IPTC metadata to images")
    parser.add_argument("--csv", type=str, help="Export results to CSV file")
    parser.add_argument("--auto-upload", action="store_true",
                       help="Automatically upload images to platform")
    parser.add_argument("--username", type=str, help="Platform username for auto-upload")
    parser.add_argument("--password", type=str, help="Platform password for auto-upload")
    parser.add_argument("--mock-ai", action="store_true",
                       help="Use mock AI generator (for testing)")
    parser.add_argument("--list-platforms", action="store_true",
                       help="List supported platforms")
    parser.add_argument("--stats", action="store_true",
                       help="Show upload statistics")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()
    
    # Initialize EnhancedStockMate
    config_path = Path(args.config) if args.config else None
    stockmate = EnhancedStockMate(config_path)
    
    # Handle special commands
    if args.list_platforms:
        stockmate.list_platforms()
        return 0
    
    if args.stats:
        stockmate.show_stats()
        return 0
    
    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return 1
    
    # Validate platform
    if args.platform not in stockmate.platform_manager.get_supported_platforms():
        logger.error(f"Unsupported platform: {args.platform}")
        logger.info("Use --list-platforms to see supported platforms")
        return 1
    
    # Process images
    try:
        stockmate.process_images(
            input_dir=input_dir,
            platform=args.platform,
            lang=args.lang,
            max_keywords=args.max_keywords,
            write_iptc=args.write_iptc,
            csv_path=Path(args.csv) if args.csv else None,
            auto_upload=args.auto_upload,
            username=args.username,
            password=args.password,
            mock_ai=args.mock_ai
        )
        
        logger.info("Processing completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())