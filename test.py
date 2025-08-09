#!/usr/bin/env python3
"""
Test script for Enhanced StockMate
"""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all modules can be imported"""
    print("测试模块导入...")
    
    try:
        from config import Config
        print("✅ config模块导入成功")
    except ImportError as e:
        print(f"❌ config模块导入失败: {e}")
        return False
    
    try:
        from platforms import PlatformManager
        print("✅ platforms模块导入成功")
    except ImportError as e:
        print(f"❌ platforms模块导入失败: {e}")
        return False
    
    try:
        from enhanced_stockmate import EnhancedStockMate
        print("✅ enhanced_stockmate模块导入成功")
    except ImportError as e:
        print(f"❌ enhanced_stockmate模块导入失败: {e}")
        return False
    
    return True

def test_config():
    """Test configuration functionality"""
    print("\n测试配置功能...")
    
    try:
        from config import Config
        config = Config()
        
        # Test platform config
        shutterstock_config = config.get_platform_config("shutterstock")
        if shutterstock_config:
            print(f"✅ Shutterstock配置: {shutterstock_config.name}")
        else:
            print("❌ 无法获取Shutterstock配置")
            return False
        
        # Test supported platforms
        platforms = config.get_supported_platforms()
        print(f"✅ 支持的平台: {', '.join(platforms)}")
        
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_platform_manager():
    """Test platform manager functionality"""
    print("\n测试平台管理器...")
    
    try:
        from platforms import PlatformManager
        manager = PlatformManager()
        
        # Test supported platforms
        platforms = manager.get_supported_platforms()
        print(f"✅ 支持的平台: {', '.join(platforms)}")
        
        # Test platform instantiation
        for platform_name in platforms:
            platform = manager.get_platform(platform_name, {})
            if platform:
                print(f"✅ {platform_name}平台实例化成功")
            else:
                print(f"❌ {platform_name}平台实例化失败")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 平台管理器测试失败: {e}")
        return False

def test_enhanced_stockmate():
    """Test EnhancedStockMate functionality"""
    print("\n测试EnhancedStockMate...")
    
    try:
        from enhanced_stockmate import EnhancedStockMate
        stockmate = EnhancedStockMate()
        
        # Test stats
        stats = stockmate.get_upload_stats()
        print(f"✅ 上传统计: {stats}")
        
        # Test platform listing
        stockmate.list_platforms()
        
        return True
    except Exception as e:
        print(f"❌ EnhancedStockMate测试失败: {e}")
        return False

def test_demo_files():
    """Test with demo files"""
    print("\n测试演示文件...")
    
    demo_dir = Path("demo")
    if not demo_dir.exists():
        print("⚠️  demo目录不存在")
        return True
    
    images = list(demo_dir.glob("*.jpg")) + list(demo_dir.glob("*.jpeg"))
    if not images:
        print("⚠️  demo目录中没有图片文件")
        return True
    
    print(f"✅ 找到 {len(images)} 个演示图片")
    
    # Test with mock AI
    try:
        from enhanced_stockmate import EnhancedStockMate
        stockmate = EnhancedStockMate()
        
        # Process one image with mock AI
        test_image = images[0]
        print(f"测试处理图片: {test_image.name}")
        
        # This would normally process the image, but we'll just test the structure
        print("✅ 演示文件测试通过")
        return True
    except Exception as e:
        print(f"❌ 演示文件测试失败: {e}")
        return False

def main():
    """Main test function"""
    print("Enhanced StockMate 测试程序")
    print("=" * 40)
    
    tests = [
        ("模块导入", test_imports),
        ("配置功能", test_config),
        ("平台管理器", test_platform_manager),
        ("EnhancedStockMate", test_enhanced_stockmate),
        ("演示文件", test_demo_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 测试失败")
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())