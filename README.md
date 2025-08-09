# Enhanced StockMate - 图库上传助手

一个强大的图库上传助手软件，能够自动生成关键词、图片描述和标题，并支持批量上传到Shutterstock、Adobe Stock等主流图库平台。

## 🌟 主要功能

- **AI智能生成**：使用OpenAI GPT-4 Vision模型自动生成高质量的标题、描述和关键词
- **多平台支持**：支持Shutterstock、Adobe Stock、iStock、Getty Images等主流图库平台
- **批量处理**：支持批量处理大量图片，提高工作效率
- **自动上传**：通过Web自动化技术实现自动上传功能
- **IPTC元数据**：自动将生成的元数据嵌入到图片文件中
- **CSV导出**：支持导出CSV文件用于手动上传
- **图形界面**：提供友好的图形用户界面
- **上传历史**：记录和管理上传历史
- **多语言支持**：支持中英文关键词生成

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装ExifTool（可选，用于IPTC元数据写入）
# Windows: 下载并安装 https://exiftool.org/
# macOS: brew install exiftool
# Linux: sudo apt-get install exiftool
```

### 2. 配置OpenAI API

```bash
# 设置OpenAI API密钥
export OPENAI_API_KEY="your-api-key-here"
```

### 3. 基本使用

#### 命令行模式

```bash
# 处理图片并生成CSV文件
python enhanced_stockmate.py ./images --platform shutterstock --csv output.csv

# 自动上传到Adobe Stock（需要提供用户名和密码）
python enhanced_stockmate.py ./images --platform adobe_stock --auto-upload --username user@example.com --password pass123

# 使用IPTC元数据嵌入
python enhanced_stockmate.py ./images --platform shutterstock --write-iptc --csv output.csv

# 使用模拟AI进行测试
python enhanced_stockmate.py ./images --platform shutterstock --mock-ai --csv output.csv
```

#### 图形界面模式

```bash
# 启动图形界面
python gui.py
```

## 📁 项目结构

```
stockmate/
├── enhanced_stockmate.py    # 主程序
├── stockmate.py            # 原始StockMate核心功能
├── config.py               # 配置管理
├── platforms.py            # 平台支持模块
├── gui.py                  # 图形用户界面
├── requirements.txt        # 依赖列表
├── README.md              # 项目文档
└── demo/                  # 示例文件
    ├── city_night_street_blue.jpg
    ├── sunset_mountain_landscape.jpg
    └── preview.csv
```

## 🔧 配置选项

### 平台配置

每个平台都有特定的配置选项：

- **Shutterstock**：最多50个关键词，标题60字符，描述220字符
- **Adobe Stock**：最多49个关键词，标题60字符，描述220字符
- **iStock**：最多50个关键词，标题60字符，描述220字符
- **Getty Images**：最多50个关键词，标题60字符，描述220字符

### AI配置

- **模型**：默认使用`gpt-4o-mini`
- **温度**：默认0.2（较低温度产生更一致的结果）
- **最大令牌数**：默认500

## 📊 使用示例

### 示例1：批量处理图片

```bash
# 处理images目录中的所有图片，生成Shutterstock格式的CSV
python enhanced_stockmate.py ./images \
    --platform shutterstock \
    --lang en,zh \
    --max-keywords 30 \
    --csv shutterstock_export.csv
```

### 示例2：自动上传

```bash
# 自动上传到Adobe Stock（需要先登录）
python enhanced_stockmate.py ./images \
    --platform adobe_stock \
    --auto-upload \
    --username your-email@example.com \
    --password your-password \
    --write-iptc
```

### 示例3：使用图形界面

1. 运行 `python gui.py`
2. 选择输入目录
3. 选择目标平台
4. 配置选项（语言、关键词数量等）
5. 点击"Process Images"开始处理

## 🔍 功能详解

### AI智能生成

- **标题生成**：基于图片内容生成简洁、描述性的标题
- **描述生成**：生成详细的图片描述，包含关键信息
- **关键词生成**：生成相关性强、搜索友好的关键词
- **多语言支持**：支持中英文关键词生成

### 平台集成

- **Shutterstock**：完整的API集成和Web自动化支持
- **Adobe Stock**：Web自动化上传功能
- **iStock**：CSV导出格式支持
- **Getty Images**：CSV导出格式支持

### 元数据管理

- **IPTC嵌入**：将生成的元数据直接嵌入到图片文件中
- **CSV导出**：导出标准格式的CSV文件
- **批量处理**：支持大量图片的批量处理

## 🛠️ 高级功能

### 自定义配置

```python
# 自定义平台配置
from config import Config

config = Config()
config.update_platform_config("shutterstock", max_keywords=40)
config.save_config()
```

### 上传历史

```python
# 查看上传统计
from enhanced_stockmate import EnhancedStockMate

stockmate = EnhancedStockMate()
stats = stockmate.get_upload_stats()
print(f"成功上传: {stats['successful_uploads']}")
print(f"成功率: {stats['success_rate']:.1f}%")
```

## 🔒 安全注意事项

- **API密钥**：请妥善保管OpenAI API密钥，不要提交到版本控制系统
- **登录凭据**：自动上传功能需要提供平台登录凭据，请确保安全
- **图片隐私**：上传前请确保图片不包含敏感信息

## 🐛 故障排除

### 常见问题

1. **OpenAI API错误**
   - 检查API密钥是否正确设置
   - 确认账户有足够的余额

2. **ExifTool未找到**
   - 安装ExifTool：`brew install exiftool` (macOS) 或 `sudo apt-get install exiftool` (Linux)

3. **上传失败**
   - 检查网络连接
   - 确认登录凭据正确
   - 查看日志文件获取详细错误信息

### 日志文件

程序运行时会生成 `stockmate.log` 日志文件，包含详细的运行信息和错误信息。

## 📈 性能优化

- **批量处理**：建议一次处理100-500张图片
- **网络优化**：使用稳定的网络连接
- **资源管理**：处理大量图片时注意内存使用

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License - 详见LICENSE文件

## 🙏 致谢

- 感谢OpenAI提供的GPT-4 Vision API
- 感谢所有图库平台提供的API和工具
- 感谢开源社区的贡献

---

**注意**：使用本软件时请遵守各图库平台的使用条款和政策。