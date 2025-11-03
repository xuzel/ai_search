# 📦 完整安装与配置指南

> **目标**: 详细的系统安装、环境配置和API密钥设置指南

本文档提供AI Search Engine的完整安装流程。

---

## 📐 系统要求

### 最低要求
- **操作系统**: Linux, macOS, Windows 10+
- **Python**: 3.8+ (推荐 3.10+)
- **内存**: 2GB RAM
- **磁盘**: 500MB
- **网络**: 稳定的互联网连接

### 推荐配置
- **Python**: 3.11+
- **内存**: 4GB+ RAM
- **磁盘**: 5GB+
- **GPU**: 可选

---

## 🚀 核心安装

### 1. 获取源代码

```bash
git clone https://github.com/your-org/ai_search.git
cd ai_search
```

### 2. 创建虚拟环境

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt

# 使用国内镜像(可选)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 🔑 API密钥配置

### 方式1: .env 文件 (推荐)

创建 `.env` 文件:

```bash
# LLM API密钥
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# 搜索API
SERPAPI_API_KEY=your_serpapi_key_here

# 可选API
OPENWEATHERMAP_API_KEY=your_weather_key
ALPHA_VANTAGE_API_KEY=your_finance_key
GOOGLE_API_KEY=your_google_key
```

### 方式2: 修改 config.yaml

编辑 `config/config.yaml`:

```yaml
llm:
  dashscope:
    enabled: true
    api_key: "sk-your-key"
    model: qwen3-max

search:
  serpapi_key: "your-serpapi-key"
```

---

## 🧩 获取API密钥

### 1. 阿里云DashScope

1. 访问 https://dashscope.aliyun.com/
2. 注册/登录
3. 创建API Key
4. 复制到 `.env`

### 2. SerpAPI

1. 访问 https://serpapi.com/
2. 注册免费账号
3. 获取API Key
4. 免费额度: 每月100次

---

## ✅ 环境验证

```bash
# 检查系统信息
python -m src.main info

# 测试研究模式
python -m src.main search "Python编程"

# 测试代码模式
python -m src.main solve "计算圆周率"
```

---

## 🐳 Docker部署

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ai-search:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

启动:

```bash
docker-compose up -d
```

---

## 🔧 故障排查

### 问题1: pip安装超时

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2: 端口被占用

```bash
export WEB_PORT=8080
python -m src.web.app
```

### 问题3: API密钥未生效

```bash
# 检查环境变量
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DASHSCOPE_API_KEY'))"
```

---

## 📌 下一步

- [10-ARCHITECTURE.md](10-ARCHITECTURE.md) - 系统架构
- [60-CONFIGURATION-LLM.md](60-CONFIGURATION-LLM.md) - LLM配置
- [70-DEVELOPMENT-GUIDE.md](70-DEVELOPMENT-GUIDE.md) - 开发指南

---

**安装完成! 🎉**
