# 🤖 Agent 系统详解

> **目标**: 理解Agent架构、执行流程和扩展方法

Agent是AI Search Engine中执行具体任务的核心单位。每个Agent专注于特定的任务类型。

---

## 📋 Agent概述

### Agent层级结构

```
BaseAgent (抽象基类)
├── ResearchAgent (网页搜索)
├── CodeAgent (代码执行)
├── ChatAgent (对话)
├── RAGAgent (文档检索)
├── WeatherAgent (天气)
├── FinanceAgent (金融)
├── RoutingAgent (路由)
└── WorkflowAgent (工作流)
```

---

## 🏗️ 基础架构

### BaseAgent 接口

```python
class BaseAgent(ABC):
    def __init__(self, llm_manager, config):
        self.llm = llm_manager
        self.config = config
    
    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """执行任务的主方法"""
        pass
    
    async def _validate_input(self, input_data: dict) -> bool:
        """验证输入数据"""
        pass
    
    async def _format_output(self, output: any) -> dict:
        """格式化输出结果"""
        pass
```

---

## 🔍 ResearchAgent (研究代理)

### 执行流程

```
用户查询
  ↓
生成搜索计划 (1-3个子查询)
  ↓
并发执行搜索 (asyncio.gather)
  ↓
选择Top N结果
  ↓
并发爬取内容 (多个URL)
  ↓
内容预处理 (清理、分段)
  ↓
综合生成答案
  ↓
返回结果 + 来源
```

### 核心代码

```python
class ResearchAgent(BaseAgent):
    def __init__(self, llm_manager, search_tool, scraper_tool, config):
        super().__init__(llm_manager, config)
        self.search_tool = search_tool
        self.scraper = scraper_tool
    
    async def execute(self, input_data: dict) -> dict:
        query = input_data.get("query")
        
        # Step 1: 生成搜索计划
        plan = await self._generate_plan(query)
        
        # Step 2: 并发搜索
        search_results = await asyncio.gather(*[
            self.search_tool.search(q) for q in plan["queries"]
        ])
        
        # Step 3: 收集顶部URL
        urls = self._extract_top_urls(search_results, top_k=9)
        
        # Step 4: 并发爬取
        contents = await asyncio.gather(*[
            self.scraper.scrape(url) for url in urls
        ], return_exceptions=True)
        
        # Step 5: 综合总结
        summary = await self._synthesize(query, contents)
        
        return {
            "query": query,
            "summary": summary,
            "sources": urls,
            "plan": plan
        }
    
    async def _generate_plan(self, query: str) -> dict:
        prompt = f"""
        将用户查询分解为3-5个搜索子查询,以获得全面的信息。
        
        用户查询: {query}
        
        返回JSON: {{"queries": ["query1", "query2", ...]}}
        """
        
        response = await self.llm.complete(prompt)
        # 解析JSON...
        return plan
    
    async def _synthesize(self, query: str, contents: list) -> str:
        context = "\n\n".join([c for c in contents if c])
        
        prompt = f"""
        基于以下信息,回答用户的查询。
        
        查询: {query}
        信息: {context}
        """
        
        return await self.llm.complete(prompt)
```

---

## 💻 CodeAgent (代码代理)

### 执行流程

```
数学问题
  ↓
生成Python代码
  ↓
验证代码安全性
  ↓
沙箱执行代码
  ↓
解释执行结果
  ↓
返回代码 + 输出 + 解释
```

### 核心特性

- 自动导入允许的库 (numpy, pandas, matplotlib等)
- 执行超时保护 (默认30秒)
- 危险模式检测 (eval, exec, os.system等)
- 输出行数限制

### 核心代码

```python
class CodeAgent(BaseAgent):
    def __init__(self, llm_manager, code_executor, config):
        super().__init__(llm_manager, config)
        self.executor = code_executor
    
    async def execute(self, input_data: dict) -> dict:
        problem = input_data.get("problem")
        
        # Step 1: 生成代码
        code = await self._generate_code(problem)
        
        # Step 2: 验证安全性
        if not self.executor.validate_code(code):
            raise ValueError("代码未通过安全检查")
        
        # Step 3: 执行代码
        result = self.executor.execute(code)
        
        # Step 4: 解释结果
        explanation = await self._explain(problem, code, result)
        
        return {
            "problem": problem,
            "code": code,
            "output": result["output"],
            "explanation": explanation,
            "error": result.get("error")
        }
    
    async def _generate_code(self, problem: str) -> str:
        prompt = f"""
        编写Python代码解决以下问题:
        
        {problem}
        
        要求:
        - 代码要清晰、有注释
        - 只使用标准库和numpy/pandas/matplotlib
        - 打印最终结果
        """
        
        response = await self.llm.complete(prompt)
        return response.strip()
```

---

## 📚 RAGAgent (文档代理)

### 执行流程

```
用户问题
  ↓
Embedding转换
  ↓
ChromaDB检索 (Top-k)
  ↓
Reranking排序 (可选)
  ↓
生成答案
  ↓
返回答案 + 文档引用
```

### 核心代码

```python
class RAGAgent(BaseAgent):
    def __init__(self, llm_manager, vector_store, reranker=None):
        super().__init__(llm_manager)
        self.vector_store = vector_store
        self.reranker = reranker
    
    async def execute(self, input_data: dict) -> dict:
        question = input_data.get("question")
        
        # Step 1: 检索文档
        chunks = await self.vector_store.query(question, top_k=10)
        
        # Step 2: Reranking (可选)
        if self.reranker:
            chunks = self.reranker.rerank(question, chunks, top_k=3)
        
        # Step 3: 生成答案
        context = "\n\n".join([c["text"] for c in chunks])
        answer = await self._generate_answer(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "sources": chunks
        }
    
    async def _generate_answer(self, question: str, context: str) -> str:
        prompt = f"""
        基于以下文档内容回答问题:
        
        文档: {context}
        
        问题: {question}
        """
        
        return await self.llm.complete(prompt)
```

---

## 💬 ChatAgent (聊天代理)

### 特点

- 支持多轮对话
- 记忆对话历史
- 流式输出支持

### 核心代码

```python
class ChatAgent(BaseAgent):
    def __init__(self, llm_manager, config):
        super().__init__(llm_manager, config)
        self.conversation_history = []
    
    async def execute(self, input_data: dict) -> dict:
        message = input_data.get("message")
        
        # 构建对话历史
        self.conversation_history.append({"role": "user", "content": message})
        
        # 生成响应
        response = await self.llm.complete(
            messages=self.conversation_history
        )
        
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "history": self.conversation_history
        }
```

---

## 🌤️ 域名Agents (天气/金融/路由)

### WeatherAgent

```python
class WeatherAgent(BaseAgent):
    async def execute(self, input_data: dict) -> dict:
        location = input_data.get("location")
        
        # 调用天气API
        weather_data = await self.weather_tool.get_weather(location)
        
        # LLM生成自然语言描述
        description = await self.llm.complete(
            f"用自然语言描述这个天气数据: {weather_data}"
        )
        
        return {
            "location": location,
            "weather": weather_data,
            "description": description
        }
```

### FinanceAgent

```python
class FinanceAgent(BaseAgent):
    async def execute(self, input_data: dict) -> dict:
        symbol = input_data.get("symbol")
        
        # 获取股票数据
        stock_data = await self.finance_tool.get_stock(symbol)
        
        # LLM分析
        analysis = await self.llm.complete(
            f"分析这只股票的走势: {stock_data}"
        )
        
        return {
            "symbol": symbol,
            "data": stock_data,
            "analysis": analysis
        }
```

---

## 🚀 Agent扩展

### 添加新Agent

1. 继承BaseAgent
2. 实现execute方法
3. 在Router中注册
4. 配置相应任务类型

```python
class CustomAgent(BaseAgent):
    async def execute(self, input_data: dict) -> dict:
        # 实现自定义逻辑
        return result
```

---

## 📌 下一步

- [13-DATA-FLOW.md](13-DATA-FLOW.md) - 数据流详解
- [20-FEATURE-RESEARCH.md](20-FEATURE-RESEARCH.md) - 研究模式
- [70-DEVELOPMENT-GUIDE.md](70-DEVELOPMENT-GUIDE.md) - 开发指南

---

**Agent是系统的执行引擎! 🚀**
