# 🚀 快速开始指南

> **目标**: 5分钟内启动AI Search Engine并完成第一次查询

本指南将带你快速完成系统安装、基本配置和第一次查询，让你快速体验AI搜索引擎的强大功能。

---

## 📋 前置条件

在开始之前，请确保你的系统满足以下要求:

- ✅ **Python 3.8+** (推荐 Python 3.10+)
- ✅ **网络连接** (用于访问LLM API和搜索API)
- ✅ **至少一个LLM API密钥** (阿里云DashScope、OpenAI、DeepSeek等)
- ✅ **命令行基础知识**

**检查Python版本**:
```bash
python --version  # 或 python3 --version
```

---

## 🎯 快速启动 (3步骤)

### 步骤 1: 安装依赖

```bash
# 克隆或进入项目目录
cd /path/to/ai_search

# 创建虚拟环境 (推荐)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt
```

**安装时间**: 约2-3分钟

---

### 步骤 2: 配置API密钥

创建 `.env` 文件并添加API密钥:

```bash
# 创建 .env 文件
touch .env

# 添加以下内容:
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
SERPAPI_API_KEY=your_serpapi_key_here
```

**免费API获取**:
- 阿里云DashScope: https://dashscope.aliyun.com/
- SerpAPI: https://serpapi.com/

---

### 步骤 3: 启动Web界面

```bash
# 启动Web服务器
python -m src.web.app
```

打开浏览器访问: **http://localhost:8000**

---

## 🎉 第一次查询

### 使用Web界面

1. 打开首页: http://localhost:8000
2. 在搜索框输入问题
3. 点击"搜索"按钮
4. 等待结果 (通常5-15秒)

### 使用命令行

```bash
# 研究模式
python -m src.main search "人工智能的最新进展"

# 代码模式
python -m src.main solve "计算1到100之间的所有质数"

# 自动模式
python -m src.main ask "2的10次方是多少?" --auto
```

---

## ✅ 验证安装

```bash
python -m src.main info
```

---

## 🛠️ 常见问题

### 问题1: "No LLM providers available"

**解决方案**:
1. 检查 `.env` 文件是否存在
2. 确认API密钥格式正确
3. 验证config.yaml中enabled: true

### 问题2: Web界面无法访问

**解决方案**:
```bash
# 使用不同端口
export WEB_PORT=8080
python -m src.web.app
```

---

## 📌 下一步

- [02-INSTALLATION.md](02-INSTALLATION.md) - 完整安装指南
- [10-ARCHITECTURE.md](10-ARCHITECTURE.md) - 系统架构
- [20-FEATURE-RESEARCH.md](20-FEATURE-RESEARCH.md) - 研究模式详解

---

**准备好了吗? 开始你的AI搜索之旅! 🚀**
