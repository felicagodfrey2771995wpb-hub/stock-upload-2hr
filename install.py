#!/usr/bin/env python3
"""
Enhanced StockMate Installation Script
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True

def install_requirements():
    """Install required packages"""
    print("安装Python依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_exiftool():
    """Check if ExifTool is installed"""
    try:
        result = subprocess.run(["exiftool", "-ver"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ExifTool已安装 (版本: {result.stdout.strip()})")
            return True
        else:
            print("⚠️  ExifTool未安装或不在PATH中")
            return False
    except FileNotFoundError:
        print("⚠️  ExifTool未安装")
        print("   请手动安装ExifTool:")
        print("   - Windows: 下载并安装 https://exiftool.org/")
        print("   - macOS: brew install exiftool")
        print("   - Linux: sudo apt-get install exiftool")
        return False

def setup_config():
    """Setup configuration directory"""
    config_dir = Path.home() / ".stockmate"
    config_dir.mkdir(exist_ok=True)
    print(f"✅ 配置目录已创建: {config_dir}")
    return True

def check_openai_key():
    """Check if OpenAI API key is set"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API密钥已设置")
        return True
    else:
        print("⚠️  OpenAI API密钥未设置")
        print("   请设置环境变量:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False

def main():
    """Main installation function"""
    print("Enhanced StockMate 安装程序")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install requirements
    if not install_requirements():
        return 1
    
    # Check ExifTool
    check_exiftool()
    
    # Setup config
    if not setup_config():
        return 1
    
    # Check OpenAI key
    check_openai_key()
    
    print("\n🎉 安装完成!")
    print("\n下一步:")
    print("1. 设置OpenAI API密钥: export OPENAI_API_KEY='your-key'")
    print("2. 运行程序: python run.py")
    print("3. 或直接运行: python enhanced_stockmate.py --help")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())