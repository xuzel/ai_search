# Architecture Overview

AI Search Engine 架构概览

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface (typer)                    │
│  search | solve | ask | chat | info                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Router (Smart Routing)                     │
│  - Classifies task type                                          │
│  - Routes to appropriate agent                                   │
│  - Calculates confidence scores                                  │
└──────────────────────┬──────────────────┬──────────────────────┘
         │              │                  │
         ▼              ▼                  ▼
    ┌─────────┐   ┌─────────┐   ┌──────────────┐
    │Research │   │  Code   │   │  Chat Agent  │
    │ Agent   │   │ Agent   │   │              │
    └────┬────┘   └────┬────┘   └──────┬───────┘
         │             │               │
         ▼             ▼               ▼
    ┌─────────────────────────────────────────┐
    │            LLM Manager                   │
    │  - OpenAI / Anthropic / Ollama          │
    │  - Fallback support                      │
    │  - Retry logic                           │
    └──────┬──────────────┬────────────────────┘
           │              │
           ▼              ▼
    ┌──────────────┐ ┌──────────────┐
    │ OpenAI       │ │ Ollama       │
    │ Client       │ │ Client       │
    └──────────────┘ └──────────────┘

    ┌─────────────────────────────────────────┐
    │           Tools & Utilities              │
    ├──────────────┬──────────┬───────────────┤
    │ Search Tool  │ Scraper  │ Code Executor │
    └──────────────┴──────────┴───────────────┘
           │             │             │
           ▼             ▼             ▼
       SerpAPI      Trafilatura     Python Sandbox
      Google API    BeautifulSoup     subprocess
```

## 核心组件

### 1. CLI Interface (src/main.py)
- 使用 `typer` 框架构建
- 提供命令行接口
- 支持的命令：
  - `search`: 网页研究
  - `solve`: 代码执行和数学问题
  - `ask`: 自动检测模式
  - `chat`: 交互式聊天
  - `info`: 显示系统信息

### 2. Router (src/router.py)
```python
TaskType = {
    RESEARCH: 网络搜索和信息综合,
    CODE: 代码生成和执行,
    CHAT: 常规对话
}
```

**分类逻辑:**
- 检测数学符号和操作符
- 匹配关键词
- 分析问号
- 计算置信度分数

### 3. Agents

#### Research Agent (src/agents/research_agent.py)
```
输入查询
    ↓
生成搜索计划 (LLM生成3-5个查询)
    ↓
并发搜索执行 (SerpAPI)
    ↓
并发内容抓取 (Trafilatura)
    ↓
信息综合 (LLM汇总)
    ↓
返回带源引用的答案
```

**主要方法:**
- `research(query)` - 执行完整的研究流程
- `_generate_search_plan()` - 生成搜索策略
- `_synthesize_information()` - 汇总信息

#### Code Agent (src/agents/code_agent.py)
```
输入问题
    ↓
分析问题 (LLM理解)
    ↓
生成Python代码 (LLM)
    ↓
验证代码 (检查危险模式)
    ↓
沙箱执行 (subprocess)
    ↓
解释结果 (LLM)
    ↓
返回代码和说明
```

**主要方法:**
- `solve(problem)` - 解决问题
- `_generate_code()` - 生成代码
- `_explain_results()` - 解释结果

#### Chat Agent (src/agents/chat_agent.py)
```
维护对话历史
    ↓
添加用户消息
    ↓
发送到LLM
    ↓
添加响应到历史
    ↓
返回响应
```

**主要方法:**
- `chat(message)` - 发送消息并获得回复
- `clear_history()` - 清除对话历史
- `set_system_prompt()` - 设置系统提示

### 4. LLM Management (src/llm/)

#### BaseLLM (src/llm/base.py)
抽象基类，定义接口

#### OpenAI Client (src/llm/openai_client.py)
- 支持GPT-3.5 / GPT-4
- 重试逻辑 (3次尝试)
- 参数化温度和token

#### Ollama Client (src/llm/ollama_client.py)
- 支持本地模型
- 异步HTTP请求
- 可用性检查

#### LLM Manager (src/llm/manager.py)
- 统一接口
- Fallback支持
- 提供商优先级

```python
# 使用示例
llm = LLMManager(config)
response = await llm.complete(
    messages=[...],
    preferred_provider="openai"
)
```

### 5. Tools (src/tools/)

#### Search Tool (src/tools/search.py)
```python
SearchTool(provider="serpapi", api_key="...")
- search(query, num_results)
- batch_search(queries)
```

支持提供商:
- SerpAPI (推荐)
- Google搜索

#### Scraper Tool (src/tools/scraper.py)
```python
ScraperTool(timeout=10, max_workers=5)
- fetch_url(url)
- extract_content(html)
- scrape_url(url)
- batch_scrape(urls)
```

使用:
- requests/aiohttp (网络请求)
- trafilatura (内容提取)

#### Code Executor (src/tools/code_executor.py)
```python
CodeExecutor(timeout=30, max_output_lines=1000)
- execute(code)
- validate_code(code)
```

安全特性:
- 超时控制
- 危险模式检测
- 导入限制
- 输出限制

### 6. Configuration (src/utils/config.py)

配置管理系统:
```python
Config
├── llm
│   ├── openai
│   └── ollama
├── search
├── scraper
├── code_execution
├── research
├── cache
└── cli
```

来源:
- YAML文件 (config/config.yaml)
- 环境变量 (.env)
- 代码默认值

## 数据流

### Research 流程
```
User Query
    ↓
Router.classify() → RESEARCH
    ↓
ResearchAgent.research()
    ├── LLM生成搜索查询 (3-5个)
    ├── SearchTool.batch_search()
    ├── ScraperTool.batch_scrape()
    └── LLM综合信息
    ↓
返回: {sources, summary}
```

### Code 流程
```
User Problem
    ↓
Router.classify() → CODE
    ↓
CodeAgent.solve()
    ├── LLM生成代码
    ├── CodeExecutor.validate()
    ├── CodeExecutor.execute()
    └── LLM解释结果
    ↓
返回: {code, output, explanation}
```

### Chat 流程
```
User Message
    ↓
Router.classify() → CHAT
    ↓
ChatAgent.chat()
    ├── 添加到历史
    ├── LLM.complete()
    └── 返回响应
    ↓
Response
```

## 异步处理

系统使用 `asyncio` 进行并发处理:

```python
# 搜索多个查询
results = await search_tool.batch_search(queries)

# 抓取多个URL
contents = await scraper_tool.batch_scrape(urls)

# 代码执行
output = await code_executor.execute(code)
```

**好处:**
- 提高网络I/O效率
- 并发请求多个URL
- 更响应的CLI

## 错误处理

### Retry Logic
- 使用 `tenacity` 库
- 最多3次重试
- 指数退避策略

### Fallback Support
```python
# 如果OpenAI失败，尝试Ollama
await llm_manager.complete(messages)
# → 尝试OpenAI
# → 如果失败，尝试Ollama
# → 如果全失败，抛出错误
```

### Validation
- 代码执行前验证
- 超时保护
- 资源限制

## 缓存机制（计划实现）

```python
@cache(ttl=3600)
async def search(query):
    # 相同查询在1小时内返回缓存结果
    pass
```

支持:
- SQLite (默认)
- Redis (可选)

## 扩展点

### 添加新的LLM提供商
1. 继承 `BaseLLM`
2. 实现 `complete()` 和 `is_available()`
3. 在 `LLMManager` 中注册

### 添加新的搜索提供商
1. 在 `SearchTool` 中添加 `_search_xxx()`
2. 更新 `search()` 方法
3. 测试和文档

### 添加新的代理
1. 创建继承自基类的新代理
2. 实现主要执行方法
3. 在路由器中注册
4. 更新CLI

## 依赖关系

```
CLI (typer)
  ↓
Router
  ↓
Agents (Research, Code, Chat)
  ├→ LLM Manager
  │   ├→ OpenAI Client
  │   └→ Ollama Client
  │
  ├→ Tools
  │   ├→ Search Tool
  │   ├→ Scraper Tool
  │   └→ Code Executor
  │
  └→ Utils
      ├→ Config
      └→ Logger
```

## 性能优化

1. **并发处理**
   - 多URL并发爬取
   - 多查询并发搜索

2. **缓存**
   - 搜索结果缓存
   - 刮取内容缓存

3. **资源管理**
   - 连接池
   - Worker限制
   - 超时控制

4. **异步I/O**
   - aiohttp用于网络请求
   - asyncio用于并发

## 安全考虑

1. **代码执行**
   - 沙箱执行（subprocess）
   - 模式检测
   - 导入限制
   - 超时保护

2. **API密钥**
   - 使用环境变量
   - 不硬编码凭证
   - 从配置文件隐藏

3. **网络请求**
   - User-Agent设置
   - 超时限制
   - SSL验证

---

这个架构提供了：
- ✅ 模块化设计
- ✅ 易于扩展
- ✅ 并发处理
- ✅ 错误处理
- ✅ 多提供商支持
- ✅ 安全代码执行
