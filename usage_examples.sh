#!/bin/bash

# Enhanced StockMate 使用示例脚本

echo "🎯 Enhanced StockMate 使用示例"
echo "================================"

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "enhanced_stockmate.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

echo "✅ 环境检查通过"

# 示例1：处理演示图片
echo ""
echo "📸 示例1：处理演示图片"
echo "命令：python3 enhanced_stockmate.py demo --platform shutterstock --mock-ai --csv demo_output.csv"
python3 enhanced_stockmate.py demo --platform shutterstock --mock-ai --csv demo_output.csv

# 示例2：处理演示图片（Adobe Stock格式）
echo ""
echo "📸 示例2：处理演示图片（Adobe Stock格式）"
echo "命令：python3 enhanced_stockmate.py demo --platform adobe_stock --mock-ai --csv adobe_output.csv"
python3 enhanced_stockmate.py demo --platform adobe_stock --mock-ai --csv adobe_output.csv

# 示例3：多语言处理
echo ""
echo "📸 示例3：多语言处理"
echo "命令：python3 enhanced_stockmate.py demo --platform shutterstock --lang en,zh --mock-ai --csv multilingual_output.csv"
python3 enhanced_stockmate.py demo --platform shutterstock --lang en,zh --mock-ai --csv multilingual_output.csv

echo ""
echo "🎉 示例完成！"
echo ""
echo "生成的文件："
echo "- demo_output.csv (Shutterstock格式)"
echo "- adobe_output.csv (Adobe Stock格式)"
echo "- multilingual_output.csv (多语言格式)"
echo ""
echo "📝 使用说明："
echo "1. 将您的图片放在一个文件夹中"
echo "2. 运行：python3 enhanced_stockmate.py your_folder --platform shutterstock --csv output.csv"
echo "3. 查看生成的CSV文件"
echo ""
echo "🔧 高级功能："
echo "- 使用 --write-iptc 嵌入元数据到图片"
echo "- 使用 --auto-upload 自动上传（需要凭据）"
echo "- 使用 --max-keywords 40 自定义关键词数量"
echo "- 使用 --lang en,zh 多语言支持"