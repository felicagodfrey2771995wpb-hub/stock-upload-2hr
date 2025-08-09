# 📸 StockMate Pro

> **AI驱动的图库照片元数据生成与上传工具**

一个强大的工具，能够自动分析图片内容，生成高质量的标题、描述和关键词，并支持直接上传到Shutterstock、Adobe Stock等主流图库平台。通过AI技术和SEO优化，最大化您图片的曝光量和销售潜力。

![StockMate Pro](https://img.shields.io/badge/StockMate-Pro-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![AI](https://img.shields.io/badge/AI-GPT--4o-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 核心功能

### 🤖 AI智能分析
- **GPT-4o视觉模型**：先进的图像理解和内容分析
- **智能关键词生成**：基于图片内容自动生成相关关键词
- **多语言支持**：同时生成英文和中文关键词
- **内容理解**：识别物体、场景、情绪、风格和色彩

### 📈 SEO优化
- **市场趋势分析**：集成最新的市场热点和趋势关键词
- **关键词排序**：按商业价值和搜索量智能排序
- **平台优化**：针对不同平台的特定要求优化元数据
- **性能评分**：实时SEO评分和改进建议

### 🌐 多平台支持
- **Shutterstock**：完整的API集成和自动上传
- **Adobe Stock**：支持Adobe Stock的上传流程
- **Getty Images**：Getty Images平台集成
- **IPTC元数据**：自动写入图片EXIF数据

### 💻 现代化界面
- **Web应用**：基于Streamlit的现代化Web界面
- **拖拽上传**：支持拖拽多文件上传
- **实时预览**：上传后即时图片预览
- **批量处理**：高效处理大量图片

### 📊 分析报告
- **性能仪表板**：详细的SEO和性能分析
- **关键词分析**：热门关键词和趋势分析
- **市场洞察**：基于数据的市场潜力评估
- **导出功能**：CSV、JSON格式数据导出

## 📋 系统要求

- **Python**: 3.8+
- **操作系统**: Windows, macOS, Linux
- **内存**: 4GB+ 推荐
- **存储**: 2GB+ 可用空间
- **网络**: 稳定的互联网连接

## 🛠️ 安装指南

### 1. 克隆项目
```bash
git clone https://github.com/your-username/stockmate-pro.git
cd stockmate-pro
```

### 2. 创建虚拟环境
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
复制环境变量模板并配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，添加您的API密钥：
```env
# 必需：OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key_here

# 可选：图库平台API密钥
SHUTTERSTOCK_API_KEY=your_shutterstock_api_key
SHUTTERSTOCK_SECRET=your_shutterstock_secret

ADOBE_STOCK_API_KEY=your_adobe_stock_api_key
ADOBE_STOCK_SECRET=your_adobe_stock_secret
```

### 5. 安装ExifTool（可选，用于IPTC写入）
- **Windows**: 下载并安装 [ExifTool](https://exiftool.org/)
- **macOS**: `brew install exiftool`
- **Linux**: `sudo apt-get install libimage-exiftool-perl`

## 🚀 快速开始

### 命令行版本
```bash
# 基础处理
python stockmate_pro.py process ./images --platform shutterstock --optimize-seo

# 高级选项
python stockmate_pro.py process ./images \
  --platform adobe_stock \
  --optimize-seo \
  --write-iptc \
  --csv output.csv \
  --max-keywords 40 \
  --analyze-trends
```

### Web界面版本
```bash
# 启动Web应用
streamlit run app.py
```

然后在浏览器中打开 `http://localhost:8501`

## 📖 详细使用说明

### Web界面使用流程

#### 1. 🏠 首页
- 查看功能概览和系统状态
- 显示已处理图片的统计信息

#### 2. 📤 上传与处理
1. **配置设置**：选择目标平台、AI模型、语言等
2. **上传图片**：拖拽或选择多个图片文件
3. **开始处理**：点击"处理图片"开始AI分析
4. **查看结果**：实时查看处理进度和结果
5. **导出数据**：下载CSV或JSON格式的元数据

#### 3. 🔍 SEO分析
- **性能概览**：SEO评分分布和市场潜力分析
- **关键词分析**：热门关键词和趋势关键词统计
- **优化建议**：基于分析结果的改进建议

#### 4. 🚀 平台上传
1. **平台配置**：检查API配置状态
2. **选择图片**：从已处理的图片中选择要上传的
3. **选择平台**：选择目标上传平台
4. **执行上传**：监控上传进度和结果

#### 5. 📊 数据分析
- **关键指标**：总体性能指标概览
- **趋势分析**：关键词趋势和市场分析
- **详细报告**：可导出的完整分析报告

### 命令行使用

#### 基础命令
```bash
# 处理单个文件夹
python stockmate_pro.py process /path/to/images

# 指定平台优化
python stockmate_pro.py process /path/to/images --platform shutterstock

# 启用SEO优化
python stockmate_pro.py process /path/to/images --optimize-seo
```

#### 高级选项
```bash
# 完整配置示例
python stockmate_pro.py process /path/to/images \
  --platform adobe_stock \
  --optimize-seo \
  --write-iptc \
  --csv exports/metadata.csv \
  --model gpt-4o \
  --temperature 0.1 \
  --max-keywords 49 \
  --analyze-trends
```

## 🎯 平台特定配置

### Shutterstock
- **关键词限制**: 最多50个
- **标题长度**: 最多200字符
- **描述长度**: 最多1000字符
- **禁用词汇**: "shutterstock", "watermark", "copyright"

### Adobe Stock  
- **关键词限制**: 最多49个
- **最少关键词**: 至少7个
- **标题长度**: 最多200字符
- **禁用词汇**: "adobe", "stock", "watermark"

### Getty Images
- **关键词限制**: 最多50个
- **标题长度**: 最多150字符
- **描述长度**: 最多800字符

## 📊 SEO优化策略

### 关键词优化
1. **主要关键词**: 描述图片核心内容的关键词
2. **趋势关键词**: 当前市场热门的搜索词
3. **长尾关键词**: 更具体、竞争较小的关键词
4. **情感关键词**: 描述情绪和氛围的词汇
5. **技术关键词**: 摄影技术和风格描述

### 市场趋势集成
- **高需求关键词**: 远程工作、可持续发展、人工智能等
- **季节性关键词**: 春夏秋冬相关的主题词汇
- **常青关键词**: 商业、科技、自然等永久性主题

### 评分系统
- **标题优化** (20%): 长度和描述性
- **描述优化** (20%): 详细程度和相关性
- **关键词数量** (20%): 适当的关键词数量
- **趋势整合** (20%): 热门关键词的使用
- **技术质量** (20%): 图片分辨率和质量

## 🔧 API配置指南

### OpenAI API
1. 注册 [OpenAI账户](https://platform.openai.com/)
2. 创建API密钥
3. 设置环境变量 `OPENAI_API_KEY`

### Shutterstock API
1. 申请 [Shutterstock开发者账户](https://www.shutterstock.com/developers)
2. 创建应用并获取API密钥
3. 设置 `SHUTTERSTOCK_API_KEY` 和 `SHUTTERSTOCK_SECRET`

### Adobe Stock API
1. 注册 [Adobe开发者账户](https://developer.adobe.com/)
2. 创建Adobe Stock应用
3. 获取API密钥和访问令牌
4. 设置相应的环境变量

## 📝 输出格式

### CSV格式
```csv
filename,title,description,keywords,category,seo_score,market_potential
image1.jpg,"商务团队会议讨论","现代办公室中的商务团队正在进行会议讨论","business;meeting;team;office;discussion",Business,0.85,High
```

### JSON格式
```json
{
  "export_timestamp": 1699999999,
  "platform": "shutterstock", 
  "settings": {
    "seo_enabled": true,
    "max_keywords": 30,
    "language": "en,zh"
  },
  "images": [
    {
      "filename": "image1.jpg",
      "title": "商务团队会议讨论",
      "description": "现代办公室中的商务团队正在进行会议讨论",
      "keywords": ["business", "meeting", "team"],
      "seo_score": 0.85,
      "market_potential": "High"
    }
  ]
}
```

## 🚨 常见问题

### Q: 为什么需要OpenAI API密钥？
A: 我们使用GPT-4o视觉模型来分析图片内容并生成高质量的元数据。这需要OpenAI的API服务。

### Q: 可以离线使用吗？
A: 核心的AI分析功能需要网络连接调用OpenAI API。但您可以使用`--mock`参数进行离线测试。

### Q: 支持哪些图片格式？
A: 支持JPEG、PNG、TIFF等常见格式。建议使用高分辨率的JPEG格式以获得最佳效果。

### Q: 生成的关键词准确吗？
A: AI生成的关键词经过优化，结合了图片内容分析和市场趋势。建议在上传前手动审核关键词。

### Q: 可以批量处理多少图片？
A: 理论上没有限制，但建议单次处理不超过100张图片以确保稳定性。

## 🤝 贡献指南

我们欢迎社区贡献！请参考以下步骤：

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供强大的GPT-4o视觉模型
- [Streamlit](https://streamlit.io/) - 优秀的Web应用框架
- [Shutterstock](https://www.shutterstock.com/) - 图库平台API支持
- [Adobe Stock](https://stock.adobe.com/) - 图库平台API支持

## 📞 支持与联系

- **问题报告**: [GitHub Issues](https://github.com/your-username/stockmate-pro/issues)
- **功能请求**: [GitHub Discussions](https://github.com/your-username/stockmate-pro/discussions)
- **邮箱支持**: support@stockmate-pro.com

---

**StockMate Pro** - 让AI为您的图库业务增值 📸✨