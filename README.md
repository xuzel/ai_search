# AI Search Engine

一个由大型语言模型驱动的AI搜索引擎，具有网络研究、代码执行和对话功能。

## 功能特性

### 1. 🔍 研究模式 (Research Mode)
- 自动生成搜索查询计划
- 并发执行多个搜索查询
- 从顶部结果中爬取内容
- 使用LLM综合信息并生成答案
- 支持引用来源

### 2. 💻 代码执行模式 (Code Mode)
- 自动生成Python代码解决数学问题
- 安全的沙箱代码执行环境
- 执行超时和资源限制
- 自动解释结果

### 3. 💬 对话模式 (Chat Mode)
- 与AI助手进行自然对话
- 保持对话历史
- 支持多轮交互

### 4. 🔀 智能路由 (Smart Routing)
- 自动检测查询类型
- 根据内容将请求路由到合适的代理
- 支持手动模式选择

## 系统要求

- Python 3.8+
- 网络连接
- LLM API密钥（OpenAI、Anthropic等）
- 搜索API密钥（SerpAPI或Google搜索）

## 安装

### 1. 克隆/创建项目
```bash
cd /Users/sudo/PycharmProjects/ai_search
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # 在Windows上: venv\Scripts\activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置API密钥

复制 `.env.example` 到 `.env` 并填入你的API密钥：
```bash
cp .env.example .env
```

或直接编辑 `config/config.yaml`：
```yaml
llm:
  openai:
    api_key: "your-api-key"

search:
  serpapi_key: "your-serpapi-key"
```

## 使用方法

### Web 界面（推荐）

启动 Web 服务器：

```bash
# 方式 1: 使用 Python 模块
python -m src.web.app

# 方式 2: 使用 uvicorn
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
```

然后在浏览器中打开 `http://localhost:8000`

#### Web UI 功能

- **🏠 首页**：统一搜索入口，自动智能路由
- **🔍 研究模式**：网络搜索，显示来源和摘要（Markdown 渲染）
- **💻 代码模式**：代码生成和执行，语法高亮，一键复制
- **💬 聊天模式**：对话界面，支持流式输出（打字机效果）
- **📚 历史记录**：查看、搜索、管理所有对话历史
- **🎨 设计风格**：温暖中性色调，优雅简约

#### Web 配置

通过环境变量配置：

```bash
export WEB_HOST="0.0.0.0"  # 默认 0.0.0.0
export WEB_PORT="8000"      # 默认 8000
```

### 命令行界面

#### 1. 研究模式
```bash
python -m src.main search "人工智能的最新进展"
python -m src.main search "What is quantum computing?"
```

#### 2. 代码执行模式
```bash
python -m src.main solve "计算1到100的质数"
python -m src.main solve "Solve: x^2 + 5x + 6 = 0"
```

#### 3. 自动检测模式
```bash
python -m src.main ask "2的10次方是多少？" --auto
python -m src.main ask "最近的人工智能突破是什么？" --auto
```

#### 4. 交互式聊天模式
```bash
python -m src.main chat
```

#### 5. 查看系统信息
```bash
python -m src.main info
```

### Python API

```python
import asyncio
from src.agents import ResearchAgent, CodeAgent
from src.llm import LLMManager
from src.tools import SearchTool, ScraperTool, CodeExecutor
from src.utils import get_config

# 初始化
config = get_config()
llm_manager = LLMManager(config=config)
search_tool = SearchTool(provider="serpapi", api_key=config.search.serpapi_key)
scraper_tool = ScraperTool()
code_executor = CodeExecutor()

# 创建代理
research_agent = ResearchAgent(llm_manager, search_tool, scraper_tool, config)
code_agent = CodeAgent(llm_manager, code_executor, config)

# 使用代理
async def main():
    # 研究
    result = await research_agent.research("人工智能应用")
    print(result["summary"])

    # 代码执行
    result = await code_agent.solve("计算斐波那契数列前10项")
    print(result["output"])

asyncio.run(main())
```

## 项目结构

```
ai_search/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI入口点
│   ├── router.py               # 任务路由器
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── research_agent.py   # 研究代理
│   │   ├── code_agent.py       # 代码执行代理
│   │   └── chat_agent.py       # 聊天代理
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py             # 基类
│   │   ├── manager.py          # LLM管理器
│   │   ├── openai_client.py    # OpenAI客户端
│   │   └── ollama_client.py    # Ollama客户端
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search.py           # 搜索工具
│   │   ├── scraper.py          # 网页爬虫
│   │   └── code_executor.py    # 代码执行器
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   └── logger.py           # 日志
│   └── web/                    # 🌐 Web UI (NEW)
│       ├── __init__.py
│       ├── app.py              # FastAPI 主应用
│       ├── database.py         # 历史记录数据库
│       ├── routers/            # 路由模块
│       │   ├── main.py         # 首页
│       │   ├── search.py       # 研究模式
│       │   ├── code.py         # 代码模式
│       │   ├── chat.py         # 聊天模式
│       │   └── history.py      # 历史记录
│       ├── static/             # 静态资源
│       │   ├── css/style.css   # 样式表
│       │   └── js/main.js      # JavaScript
│       └── templates/          # Jinja2 模板
│           ├── base.html
│           ├── index.html
│           ├── search_result.html
│           ├── code_result.html
│           ├── chat.html
│           ├── history.html
│           └── components/
├── config/
│   └── config.yaml             # 主配置文件
├── data/                       # 数据文件夹
│   └── history.db              # SQLite 历史记录
├── docs/                       # 📚 文档文件夹
│   ├── QUICKSTART.md           # 快速开始
│   ├── ARCHITECTURE.md         # 架构设计
│   ├── LLM_ROUTING_GUIDE.md    # 路由系统指南
│   └── ... (其他文档)
├── requirements.txt            # 项目依赖
├── .env.example                # 环境变量示例
├── README.md                   # 项目首页
└── CLAUDE.md                   # Claude Code 开发指南
```

## 配置详解

### config/config.yaml

#### LLM配置
```yaml
llm:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 2000

  ollama:
    enabled: false
    base_url: http://localhost:11434
    model: llama2
```

#### 搜索配置
```yaml
search:
  provider: serpapi      # Options: serpapi, google_search, bing
  serpapi_key: ${SERPAPI_API_KEY}
  results_per_query: 5
  timeout: 10
```

#### 代码执行配置
```yaml
code_execution:
  timeout: 30            # 执行超时（秒）
  max_output_lines: 1000 # 最大输出行数
  allowed_imports:       # 允许的导入模块
    - numpy
    - pandas
    - scipy
    - matplotlib
    - sympy
```

## 支持的LLM提供商

- **OpenAI**: GPT-3.5, GPT-4
- **Anthropic**: Claude
- **本地模型**: 通过Ollama支持Llama 2等
- **其他API**: 支持自定义集成

## 搜索提供商

- **SerpAPI**: 推荐使用，API稳定
- **Google搜索**: 需要google-search-results库
- **Bing**: 可通过自定义扩展

## 代码执行安全性

代码执行器包含以下安全措施：

1. **执行超时**: 默认30秒超时
2. **资源限制**: 限制输出行数
3. **导入限制**: 只允许指定的安全模块
4. **模式检测**: 检测危险的代码模式
5. **沙箱执行**: 在隔离的子进程中运行

## 常见问题

### Q1: 如何设置代理？
编辑 `config/config.yaml` 中的相应配置：
```yaml
llm:
  openai:
    enabled: true
    api_key: "your-key"
```

### Q2: 研究模式需要哪些API？
- OpenAI API（或其他LLM）
- SerpAPI 或 Google搜索API

### Q3: 如何使用本地模型？
1. 安装Ollama
2. 在config.yaml中启用Ollama
3. 下载模型：`ollama pull llama2`

### Q4: 代码执行是否安全？
是的，代码在隔离的子进程中运行，具有超时和资源限制。但建议不要执行不信任的代码。

## 开发

### 运行测试
```bash
pytest tests/
```

### 添加新的LLM提供商
1. 继承 `BaseLLM` 类
2. 实现 `complete()` 和 `is_available()` 方法
3. 在 `LLMManager` 中注册

### 添加新的搜索提供商
1. 在 `SearchTool` 中添加新的 `_search_xxx()` 方法
2. 更新路由逻辑

## 许可证

MIT License

## 贡献

欢迎贡献！请提交Pull Request。

## 支持

如有问题，请创建Issue或联系开发者。

---

## 📚 完整文档系统

详细的文档位于 `docs/` 文件夹。我们提供了一套完整的29份文档，包括快速开始、架构设计、功能指南、API参考等。

**👉 [文档导航中心 (00-INDEX.md)](docs/00-INDEX.md)** - 推荐首先查看此文档获得完整导航

### 📗 快速开始层 (3份文档)
- [01-QUICKSTART.md](docs/01-QUICKSTART.md) - 5分钟快速上手
- [02-INSTALLATION.md](docs/02-INSTALLATION.md) - 完整安装与配置指南
- [00-INDEX.md](docs/00-INDEX.md) - 文档导航中心

### 📘 核心概念层 (4份文档)
- [10-ARCHITECTURE.md](docs/10-ARCHITECTURE.md) - 系统架构设计
- [11-INTELLIGENT-ROUTING.md](docs/11-INTELLIGENT-ROUTING.md) - 智能路由与分类器
- [12-AGENT-SYSTEM.md](docs/12-AGENT-SYSTEM.md) - Agent系统详解
- [13-DATA-FLOW.md](docs/13-DATA-FLOW.md) - 数据流程架构

### 📙 功能指南层 (11份文档)
- [20-FEATURE-RESEARCH.md](docs/20-FEATURE-RESEARCH.md) - 网页搜索与研究模式
- [21-FEATURE-CODE.md](docs/21-FEATURE-CODE.md) - 代码生成与执行
- [22-FEATURE-CHAT.md](docs/22-FEATURE-CHAT.md) - 对话聊天模式
- [23-FEATURE-RAG.md](docs/23-FEATURE-RAG.md) - RAG文档检索系统
- [24-FEATURE-RERANKING.md](docs/24-FEATURE-RERANKING.md) - 结果重排序器
- [25-FEATURE-WEATHER.md](docs/25-FEATURE-WEATHER.md) - 天气查询功能
- [26-FEATURE-FINANCE.md](docs/26-FEATURE-FINANCE.md) - 金融数据工具
- [27-FEATURE-ROUTING.md](docs/27-FEATURE-ROUTING.md) - 查询路由器
- [28-FEATURE-OCR.md](docs/28-FEATURE-OCR.md) - OCR图片文字识别
- [29-FEATURE-VISION.md](docs/29-FEATURE-VISION.md) - Vision图像理解
- [30-FEATURE-WORKFLOW.md](docs/30-FEATURE-WORKFLOW.md) - 工作流编排器

### 📕 API参考层 (3份文档)
- [40-API-AGENTS.md](docs/40-API-AGENTS.md) - Agents API完整文档
- [41-API-TOOLS.md](docs/41-API-TOOLS.md) - Tools API完整文档
- [42-API-WEB-ENDPOINTS.md](docs/42-API-WEB-ENDPOINTS.md) - Web端点接口文档

### 📺 Web UI层 (2份文档)
- [50-WEB-UI-OVERVIEW.md](docs/50-WEB-UI-OVERVIEW.md) - Web界面总览
- [51-WEB-UI-HTMX.md](docs/51-WEB-UI-HTMX.md) - HTMX交互开发

### ⚙️ 配置层 (2份文档)
- [60-CONFIGURATION-LLM.md](docs/60-CONFIGURATION-LLM.md) - LLM提供商配置
- [61-CONFIGURATION-APIS.md](docs/61-CONFIGURATION-APIS.md) - 外部API密钥配置

### 🔧 开发层 (2份文档)
- [70-DEVELOPMENT-GUIDE.md](docs/70-DEVELOPMENT-GUIDE.md) - 开发者指南
- [71-TESTING-GUIDE.md](docs/71-TESTING-GUIDE.md) - 测试指南

### 📚 参考层 (2份文档)
- [80-TROUBLESHOOTING.md](docs/80-TROUBLESHOOTING.md) - 故障排查手册
- [81-FAQ.md](docs/81-FAQ.md) - 常见问题解答

---

### 快速链接

**新手入门**: [01-QUICKSTART.md](docs/01-QUICKSTART.md) → [50-WEB-UI-OVERVIEW.md](docs/50-WEB-UI-OVERVIEW.md)

**深入学习**: [10-ARCHITECTURE.md](docs/10-ARCHITECTURE.md) → [12-AGENT-SYSTEM.md](docs/12-AGENT-SYSTEM.md) → [70-DEVELOPMENT-GUIDE.md](docs/70-DEVELOPMENT-GUIDE.md)

**遇到问题**: [80-TROUBLESHOOTING.md](docs/80-TROUBLESHOOTING.md) → [81-FAQ.md](docs/81-FAQ.md)
