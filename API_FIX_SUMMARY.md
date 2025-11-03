# API配置显示问题修复总结

## 问题描述

前端页面显示"API未配置"，即使所有API密钥都已在`.env`文件中正确配置。

## 根本原因

1. **未调用初始化函数**：`tools_page()` 和 `multimodal_page()` 在渲染页面时没有调用 `initialize_tools()` 或 `initialize_multimodal()`
2. **未检查enabled标志**：初始化函数没有检查 `config.yaml` 中的 `enabled` 标志就尝试初始化工具
3. **全局变量初始化**：工具的全局变量（`weather_tool`、`finance_tool` 等）在首次访问页面时为 `None`

## 修复内容

### 1. 修复 `src/web/routers/tools.py`

#### 修改1：在 `tools_page()` 中添加初始化调用
```python
@router.get("/tools", response_class=HTMLResponse)
async def tools_page(request: Request):
    """Render tools page"""
    templates = request.app.state.templates

    # Initialize tools to check availability
    try:
        await initialize_tools()
    except Exception as e:
        logger.warning(f"Failed to initialize tools: {e}")

    return templates.TemplateResponse(...)
```

#### 修改2：在初始化前检查 enabled 标志
```python
# Initialize Weather Tool
if config.domain_tools.weather.enabled:
    try:
        weather_tool = WeatherTool(api_key=config.domain_tools.weather.api_key)
        logger.info("WeatherTool initialized successfully")
    except Exception as e:
        logger.warning(f"WeatherTool initialization failed (optional): {e}")
        weather_tool = None
else:
    logger.info("WeatherTool disabled in config")
    weather_tool = None

# 同样的逻辑应用于 Finance Tool 和 Routing Tool
```

### 2. 修复 `src/web/routers/multimodal.py`

#### 修改1：在 `multimodal_page()` 中添加初始化调用
```python
@router.get("/multimodal", response_class=HTMLResponse)
async def multimodal_page(request: Request):
    """Render multimodal (OCR & Vision) page"""
    templates = request.app.state.templates

    # Initialize multimodal tools to check availability
    try:
        await initialize_multimodal()
    except Exception as e:
        logger.warning(f"Failed to initialize multimodal tools: {e}")

    return templates.TemplateResponse(...)
```

#### 修改2：在初始化前检查 enabled 标志
```python
# Initialize OCR Tool
if config.multimodal.ocr.enabled:
    try:
        ocr_tool = OCRTool()
        logger.info("OCRTool initialized successfully")
    except Exception as e:
        logger.warning(f"OCRTool initialization failed (optional): {e}")
        ocr_tool = None
else:
    logger.info("OCRTool disabled in config")
    ocr_tool = None

# 同样的逻辑应用于 Vision Tool
```

## 验证结果

运行 `python test_api_config.py` 验证所有API配置正确加载：

```
✅ Weather API: Configured
✅ Finance API: Configured
✅ Routing API: Configured
✅ Google Vision API: Configured
✅ DashScope API: Configured
✅ SerpAPI: Configured
```

## 测试步骤

1. **启动Web服务器**：
   ```bash
   python -m src.web.app
   ```

2. **访问Domain Tools页面**：
   - URL: http://localhost:8000/tools
   - 应该显示：✅ Weather Ready, ✅ Finance Ready, ✅ Routing Ready

3. **访问Multimodal页面**：
   - URL: http://localhost:8000/multimodal
   - 应该显示：✅ OCR Ready (如果PaddleOCR已安装), ✅ Vision Ready

## 配置要求

确保 `.env` 文件包含以下API密钥：

```bash
# Domain Tools
OPENWEATHERMAP_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here
OPENROUTESERVICE_API_KEY=your_key_here

# Multimodal
GOOGLE_API_KEY=your_key_here

# LLM (至少一个)
DASHSCOPE_API_KEY=your_key_here
# 或 OPENAI_API_KEY=your_key_here

# Search
SERPAPI_API_KEY=your_key_here
```

确保 `config/config.yaml` 中对应的工具设置为 `enabled: true`：

```yaml
domain_tools:
  weather:
    enabled: true
  finance:
    enabled: true
  routing:
    enabled: true

multimodal:
  ocr:
    enabled: true
  vision:
    enabled: true
```

## 注意事项

1. **OCR工具**：需要安装 PaddleOCR
   ```bash
   pip install paddleocr paddlepaddle
   ```

2. **首次加载可能较慢**：工具初始化（特别是OCR）可能需要几秒钟

3. **日志查看**：如果仍有问题，查看服务器日志了解具体错误信息

## 相关文件

- `src/web/routers/tools.py` - Domain Tools路由器
- `src/web/routers/multimodal.py` - Multimodal路由器
- `src/tools/weather_tool.py` - Weather工具
- `src/tools/finance_tool.py` - Finance工具
- `src/tools/routing_tool.py` - Routing工具
- `src/tools/ocr_tool.py` - OCR工具
- `src/tools/vision_tool.py` - Vision工具
- `config/config.yaml` - 主配置文件
- `.env` - 环境变量配置
