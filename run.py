#!/usr/bin/env python3
"""
Enhanced StockMate Launcher
"""

import sys
import os
from pathlib import Path

def main():
    """Main launcher function"""
    print("Enhanced StockMate - 图库上传助手")
    print("=" * 50)
    
    # Check if GUI is available
    try:
        import tkinter
        gui_available = True
    except ImportError:
        gui_available = False
        print("警告: tkinter未安装，图形界面不可用")
    
    # Show menu
    print("\n请选择运行模式:")
    print("1. 图形界面模式 (GUI)")
    print("2. 命令行模式")
    print("3. 查看帮助")
    print("4. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == "1":
                if gui_available:
                    print("启动图形界面...")
                    from gui import main as gui_main
                    gui_main()
                else:
                    print("图形界面不可用，请选择命令行模式")
                break
                
            elif choice == "2":
                print("命令行模式")
                print("示例命令:")
                print("  python enhanced_stockmate.py ./images --platform shutterstock --csv output.csv")
                print("  python enhanced_stockmate.py ./images --platform adobe_stock --auto-upload")
                print("\n使用 --help 查看完整帮助")
                break
                
            elif choice == "3":
                print("\nEnhanced StockMate 帮助:")
                print("-" * 30)
                print("这是一个强大的图库上传助手软件，能够自动生成关键词、图片描述和标题。")
                print("\n主要功能:")
                print("• AI智能生成标题、描述和关键词")
                print("• 支持多平台 (Shutterstock, Adobe Stock, iStock, Getty)")
                print("• 批量处理和自动上传")
                print("• IPTC元数据嵌入")
                print("• CSV导出和图形界面")
                print("\n快速开始:")
                print("1. 安装依赖: pip install -r requirements.txt")
                print("2. 设置API密钥: export OPENAI_API_KEY='your-key'")
                print("3. 运行: python enhanced_stockmate.py ./images --platform shutterstock")
                
            elif choice == "4":
                print("退出程序")
                break
                
            else:
                print("无效选择，请输入1-4")
                
        except KeyboardInterrupt:
            print("\n退出程序")
            break
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    main()