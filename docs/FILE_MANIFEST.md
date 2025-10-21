# AI Search Engine - 文件清单

完整的项目文件清单和描述。

## 📁 项目目录结构

```
ai_search/
├── 📄 文档文件
│   ├── README.md                      (6.5KB) 主要文档，功能介绍和安装指南
│   ├── QUICKSTART.md                  (4.4KB) 快速开始指南，5分钟上手
│   ├── USAGE_GUIDE.md                 (9.3KB) 完整使用手册，所有用例
│   ├── ARCHITECTURE.md                (9.8KB) 系统架构设计文档
│   ├── TROUBLESHOOTING.md             (7.1KB) 故障排除指南，常见问题解决
│   ├── IMPLEMENTATION_SUMMARY.md      (9.7KB) 实现总结，技术细节
│   ├── PROJECT_COMPLETION_REPORT.md   (8.8KB) 完成报告，项目统计
│   └── FILE_MANIFEST.md               本文件
│
├── 🔧 配置和环境
│   ├── config/
│   │   └── config.yaml                配置文件，所有系统设置
│   ├── .env.example                   环境变量模板
│   ├── requirements.txt               Python依赖列表
│   ├── pyproject.toml                 项目元数据和构建配置
│   └── __main__.py                    模块入口点
│
├── 📦 源代码 (src/)
│   ├── __init__.py                    包初始化
│   ├── main.py                   (400行) CLI主程序（typer框架）
│   ├── router.py                 (100行) 智能任务路由器
│   │
│   ├── llm/ - LLM集成模块
│   │   ├── __init__.py                模块导出
│   │   ├── base.py              (50行) 基础LLM接口
│   │   ├── manager.py           (150行) LLM管理器（支持fallback）
│   │   ├── openai_client.py     (100行) OpenAI GPT API客户端
│   │   └── ollama_client.py     (120行) Ollama本地模型客户端
│   │
│   ├── agents/ - 智能代理
│   │   ├── __init__.py                模块导出
│   │   ├── research_agent.py    (250行) 网络研究代理
│   │   ├── code_agent.py        (200行) 代码执行代理
│   │   └── chat_agent.py        (80行)  交互式聊天代理
│   │
│   ├── tools/ - 工具和实用程序
│   │   ├── __init__.py                模块导出
│   │   ├── search.py            (150行) 搜索工具（SerpAPI/Google）
│   │   ├── scraper.py           (200行) 网页爬虫工具（Trafilatura）
│   │   └── code_executor.py     (150行) 安全代码执行器
│   │
│   └── utils/ - 工具函数
│       ├── __init__.py                模块导出
│       ├── config.py            (300行) 配置管理系统
│       └── logger.py            (40行)  日志系统
│
├── 📚 示例和测试
│   ├── examples/
│   │   └── basic_usage.py       (200行) 基础使用示例
│   └── tests/
│       └── test_router.py       (50行)  单元测试
│
└── 📋 其他文件
    └── cache/                         缓存目录（运行时创建）
```

## 📄 文档文件详解

### README.md (主文档)
- 功能概述（研究、代码、聊天三种模式）
- 系统要求
- 安装步骤
- 基本使用方法
- 项目结构说明
- 配置详解
- 支持的LLM和搜索提供商
- 代码执行安全性
- 常见问题解答

### QUICKSTART.md (快速开始)
- 1. 安装（3步）
- 2. 配置（2步）
- 3. 快速测试（4个测试）
- 4. 常见使用场景（5个）
- 5. Python API使用示例
- 6. 故障排除（4个常见问题）
- 7. 性能提示
- 8. 下一步建议

### USAGE_GUIDE.md (完整使用指南)
- 安装详细步骤
- 配置指南（API密钥、配置文件）
- 基本使用（5种基本用法）
- 高级用法（Python API、自定义LLM）
- 常见任务（6个实际场景）
- 技巧和最佳实践（5个技巧+5个最佳实践）
- 故障排除快速参考
- 获得帮助

### ARCHITECTURE.md (架构设计)
- 系统架构图
- 核心组件详解
- 数据流程图
- 异步处理说明
- 错误处理机制
- 缓存机制
- 扩展点
- 依赖关系图
- 性能优化
- 安全考虑

### TROUBLESHOOTING.md (故障排除)
- 6大类常见错误
  - API和配置错误（2个）
  - 代码执行错误（3个）
  - 搜索和爬虫错误（3个）
  - 安装和依赖错误（2个）
  - 性能问题（1个）
  - 日志和调试（3个）
- 每个错误都包含原因、解决步骤和最佳实践
- 获得帮助的方法
- 进阶调试技巧

### IMPLEMENTATION_SUMMARY.md (实现总结)
- 项目完成情况检查清单
- 技术栈详解
- 主要功能说明
- API设计文档
- 配置系统说明
- 使用示例代码
- 关键特性列表
- 后续改进方向
- 测试覆盖情况
- 部署选项
- 文件大小和依赖统计

### PROJECT_COMPLETION_REPORT.md (完成报告)
- 项目概述和状态
- 文件清单和统计
- 功能完成度检查
- 技术实现说明
- 项目统计数据
- 快速开始指南
- 功能完成度表格
- 安全特性列表
- 学习资源推荐
- 扩展方向规划
- 项目检查清单
- 项目亮点
- 最终总结

## 🔧 配置文件详解

### config/config.yaml (主配置)
包含以下配置部分：
- `llm` - LLM提供商配置（OpenAI、Ollama）
- `search` - 搜索配置（提供商、结果数、超时）
- `scraper` - 网页爬虫配置（超时、并发数、User-Agent）
- `code_execution` - 代码执行配置（超时、输出限制、允许的导入）
- `research` - 研究模式配置（查询数、结果数、总结令牌数）
- `cache` - 缓存配置（启用、TTL、后端）
- `cli` - CLI配置（主题、详细模式、显示源）

### requirements.txt (依赖)
- 核心依赖: pydantic, typer, rich等
- LLM依赖: openai, aiohttp等
- 搜索依赖: google-search-results, beautifulsoup4, trafilatura等
- 开发依赖: pytest, black, mypy等

### pyproject.toml (项目配置)
- 项目元数据
- 依赖定义
- 可选依赖组
- 构建系统配置
- 工具配置（black, mypy等）

## 📦 源代码模块详解

### src/main.py (CLI主程序)
**主要功能**：
- 定义5个CLI命令
- 初始化所有组件
- 处理用户输入
- 显示格式化输出

**命令**：
- `search` - 网络研究
- `solve` - 代码执行
- `ask` - 自动路由
- `chat` - 交互式聊天
- `info` - 系统信息

### src/router.py (任务路由)
**主要类**：
- `TaskType` - 枚举：RESEARCH, CODE, CHAT
- `Router` - 分类和路由

**主要方法**：
- `classify()` - 分类查询
- `get_confidence()` - 计算置信度

### src/llm/ (LLM集成)

#### base.py - 基础接口
**主要类**：
- `BaseLLM` - 抽象基类

**抽象方法**：
- `complete()` - 生成完成
- `is_available()` - 检查可用性

#### manager.py - LLM管理
**主要类**：
- `LLMManager` - 统一LLM管理

**主要方法**：
- `complete()` - 使用fallback的生成
- `add_provider()` - 添加提供商
- `get_provider()` - 获取提供商

#### openai_client.py - OpenAI
**主要类**：
- `OpenAIClient` - OpenAI API客户端

**特性**：
- 支持GPT-3.5/GPT-4
- 自动重试（3次）
- 参数可配置

#### ollama_client.py - Ollama
**主要类**：
- `OllamaClient` - Ollama本地模型

**特性**：
- 本地模型支持
- 异步HTTP请求
- 可用性检查

### src/agents/ (智能代理)

#### research_agent.py
**主要类**：
- `ResearchAgent` - 网络研究代理

**主要方法**：
- `research()` - 执行研究流程
- `_generate_search_plan()` - 生成搜索计划
- `_synthesize_information()` - 综合信息

**流程**：
1. 生成搜索查询 (3-5个)
2. 并发执行搜索
3. 并发爬取内容
4. LLM综合信息
5. 返回带源的答案

#### code_agent.py
**主要类**：
- `CodeAgent` - 代码执行代理

**主要方法**：
- `solve()` - 解决问题
- `_generate_code()` - 生成代码
- `_explain_results()` - 解释结果

**流程**：
1. 分析问题
2. LLM生成代码
3. 验证代码
4. 执行代码
5. 解释结果

#### chat_agent.py
**主要类**：
- `ChatAgent` - 聊天代理

**主要方法**：
- `chat()` - 发送消息
- `clear_history()` - 清除历史
- `set_system_prompt()` - 设置系统提示

### src/tools/ (工具)

#### search.py
**主要类**：
- `SearchTool` - 搜索工具

**主要方法**：
- `search()` - 单次搜索
- `batch_search()` - 批量搜索

**支持**：
- SerpAPI
- Google搜索

#### scraper.py
**主要类**：
- `ScraperTool` - 网页爬虫

**主要方法**：
- `fetch_url()` - 获取URL
- `extract_content()` - 提取内容
- `scrape_url()` - 爬取URL
- `batch_scrape()` - 批量爬取

**特性**：
- Trafilatura内容提取
- 异步并发
- 超时保护

#### code_executor.py
**主要类**：
- `CodeExecutor` - 代码执行器

**主要方法**：
- `execute()` - 执行代码
- `validate_code()` - 验证代码

**安全特性**：
- 子进程隔离
- 超时保护
- 代码验证
- 导入限制

### src/utils/ (工具函数)

#### config.py
**主要类**：
- `Config` - 主配置类
- `LLMConfig`, `SearchConfig` - 子配置类
- 9个配置类总共

**主要方法**：
- `load_config()` - 加载配置
- `get_config()` - 获取全局配置

**特性**：
- YAML加载
- 环境变量覆盖
- Pydantic验证

#### logger.py
**主要函数**：
- `get_logger()` - 获取日志器

**特性**：
- 标准化日志
- 流处理器

## 📚 示例和测试

### examples/basic_usage.py
包含6个示例：
1. `example_code_execution()` - 基础代码执行
2. `example_chat()` - 聊天示例
3. `example_code_with_matplotlib()` - 绘图示例
4. `example_symbolic_math()` - 符号数学
5. `example_data_analysis()` - 数据分析
6. `example_research()` - 网络研究（需要SerpAPI）

### tests/test_router.py
包含4个测试类：
- `test_classify_research_query()` - 研究分类测试
- `test_classify_code_query()` - 代码分类测试
- `test_classify_chat_query()` - 聊天分类测试
- `test_confidence_score()` - 置信度测试
- `test_question_mark_detection()` - 问号检测

## 📊 文件统计

### 代码文件
- Python文件: 22个
- 总代码行数: ~2,800
- 平均文件大小: ~127行

### 文档文件
- Markdown文档: 7个
- 总文档行数: ~2,500
- 总文档大小: ~45KB

### 配置文件
- 配置文件: 3个
- 总大小: ~1KB

### 项目文件
- 总文件数: 32个
- 总大小: ~55KB

## 🎯 文件使用指南

### 开始学习
1. 先读 `README.md` - 了解项目
2. 再读 `QUICKSTART.md` - 快速上手
3. 查看 `examples/basic_usage.py` - 学习API

### 实际应用
1. 参考 `USAGE_GUIDE.md` - 查找用例
2. 编辑 `config/config.yaml` - 调整配置
3. 查看 `src/` - 理解实现

### 遇到问题
1. 首先查 `TROUBLESHOOTING.md` - 常见问题
2. 再查 `ARCHITECTURE.md` - 理解设计
3. 最后查 `IMPLEMENTATION_SUMMARY.md` - 技术细节

### 扩展开发
1. 学习 `ARCHITECTURE.md` - 理解架构
2. 研究相关 `src/` 模块
3. 参考 `examples/` 编写示例

---

**文件清单完成！**

所有文件已准备就绪，可以开始使用。

更多信息请参考各文档文件。
