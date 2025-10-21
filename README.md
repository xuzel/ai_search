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
│   └── utils/
│       ├── __init__.py
│       ├── config.py           # 配置管理
│       └── logger.py           # 日志
├── config/
│   └── config.yaml             # 主配置文件
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

## 📚 文档

详细的文档位于 `docs/` 文件夹。主要文档包括：

### 快速开始
- [QUICKSTART.md](docs/QUICKSTART.md) - 快速开始指南
- [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - 快速参考卡片

### 系统架构与设计
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 系统架构概览
- [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - 实现总结

### 功能指南
- [USAGE_GUIDE.md](docs/USAGE_GUIDE.md) - 使用指南
- [API_ENDPOINTS_GUIDE.md](docs/API_ENDPOINTS_GUIDE.md) - API端点指南

### 路由系统
- [ROUTER_UPGRADE_SUMMARY.md](docs/ROUTER_UPGRADE_SUMMARY.md) - 路由系统升级总结
- [LLM_ROUTING_GUIDE.md](docs/LLM_ROUTING_GUIDE.md) - LLM 路由详细指南
- [ROUTING_IMPROVEMENTS.md](docs/ROUTING_IMPROVEMENTS.md) - 路由改进说明

### 配置指南
- [CLAUDE.md](docs/CLAUDE.md) - Claude Code 开发指南
- [MODEL_SELECTION_GUIDE.md](docs/MODEL_SELECTION_GUIDE.md) - 模型选择指南
- [CUSTOM_URL_SETUP.md](docs/CUSTOM_URL_SETUP.md) - 自定义URL设置
- [ALIYUN_DASHSCOPE_SETUP.md](docs/ALIYUN_DASHSCOPE_SETUP.md) - 阿里云DashScope设置

### 参考资料
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排除
- [FILE_MANIFEST.md](docs/FILE_MANIFEST.md) - 文件清单
- [PROJECT_COMPLETION_REPORT.md](docs/PROJECT_COMPLETION_REPORT.md) - 项目完成报告
- [CUSTOM_API_SUMMARY.md](docs/CUSTOM_API_SUMMARY.md) - 自定义API总结
- [DASHSCOPE_SETUP_GUIDE.md](docs/DASHSCOPE_SETUP_GUIDE.md) - DashScope设置指南
