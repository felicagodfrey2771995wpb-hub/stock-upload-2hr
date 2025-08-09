# 🚀 Enhanced StockMate 快速开始指南

## 📋 前置要求

1. **Python 3.8+** ✅ 已安装
2. **依赖包** ✅ 已安装
3. **OpenAI API密钥**（可选，用于AI生成）

## 🎯 第一步：设置API密钥（可选）

如果您想使用AI生成功能，需要设置OpenAI API密钥：

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## 🎯 第二步：准备图片

1. 创建一个文件夹存放您的图片：
```bash
mkdir my_images
```

2. 将您的图片复制到文件夹：
```bash
cp /path/to/your/images/*.jpg my_images/
```

## 🎯 第三步：基本使用

### 3.1 生成CSV文件（推荐）

```bash
# 使用模拟AI（测试用）
python3 enhanced_stockmate.py my_images --platform shutterstock --mock-ai --csv output.csv

# 使用真实AI（需要API密钥）
python3 enhanced_stockmate.py my_images --platform shutterstock --csv output.csv
```

### 3.2 查看生成结果

```bash
# 查看CSV文件内容
cat output.csv
```

## 🎯 第四步：高级功能

### 4.1 多语言支持

```bash
# 生成中英文关键词
python3 enhanced_stockmate.py my_images --platform shutterstock --lang en,zh --csv multilingual.csv
```

### 4.2 自定义关键词数量

```bash
# 生成40个关键词
python3 enhanced_stockmate.py my_images --platform shutterstock --max-keywords 40 --csv output.csv
```

### 4.3 嵌入IPTC元数据

```bash
# 将元数据嵌入到图片文件中
python3 enhanced_stockmate.py my_images --platform shutterstock --write-iptc --csv output.csv
```

### 4.4 自动上传（需要凭据）

```bash
# 自动上传到Shutterstock
python3 enhanced_stockmate.py my_images --platform shutterstock --auto-upload --username your-username --password your-password
```

## 🎯 第五步：查看结果

生成的CSV文件包含以下信息：
- `filename`: 图片文件名
- `title`: 生成的标题
- `description`: 生成的描述
- `keywords`: 生成的关键词（分号分隔）
- `platform`: 目标平台
- `processed_at`: 处理时间

## 🎯 第六步：平台特定格式

### Shutterstock格式
```bash
python3 enhanced_stockmate.py my_images --platform shutterstock --csv shutterstock.csv
```

### Adobe Stock格式
```bash
python3 enhanced_stockmate.py my_images --platform adobe_stock --csv adobe.csv
```

## 🎯 第七步：故障排除

### 常见问题

1. **模块导入错误**
   ```bash
   pip3 install --break-system-packages -r requirements.txt
   ```

2. **API密钥错误**
   - 检查API密钥是否正确设置
   - 确认账户有足够余额

3. **图片格式不支持**
   - 支持的格式：JPG, JPEG, PNG, TIF, TIFF

4. **权限错误**
   - 确保对图片文件夹有读取权限
   - 确保对输出目录有写入权限

## 🎯 第八步：获取帮助

```bash
# 查看完整帮助
python3 enhanced_stockmate.py --help

# 查看支持的平台
python3 -c "from platforms import PlatformManager; pm = PlatformManager(); print('支持的平台:', pm.get_supported_platforms())"

# 运行测试
python3 test.py
```

## 🎯 第九步：示例文件

项目包含演示文件，可以用于测试：

```bash
# 处理演示图片
python3 enhanced_stockmate.py demo --platform shutterstock --mock-ai --csv demo_output.csv

# 查看结果
cat demo_output.csv
```

## 🎯 第十步：下一步

1. **批量处理**：将大量图片放在一个文件夹中
2. **自动化**：设置定时任务自动处理新图片
3. **集成**：将CSV文件导入到图库平台
4. **优化**：根据平台要求调整关键词和描述

## 📞 支持

如果遇到问题，请：
1. 查看日志文件：`stockmate.log`
2. 运行测试：`python3 test.py`
3. 检查帮助：`python3 enhanced_stockmate.py --help`

---

**祝您使用愉快！** 🎉