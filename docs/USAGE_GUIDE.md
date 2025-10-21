# AI Search Engine - 完整使用指南

## 目录
1. [安装](#安装)
2. [配置](#配置)
3. [基本使用](#基本使用)
4. [高级用法](#高级用法)
5. [常见任务](#常见任务)
6. [技巧和最佳实践](#技巧和最佳实践)

## 安装

### 快速安装（5分钟）

```bash
# 1. 进入项目目录
cd /Users/sudo/PycharmProjects/ai_search

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 设置API密钥
cp .env.example .env
# 编辑 .env 文件，添加你的 OPENAI_API_KEY

# 5. 验证安装
python -m src.main info
```

## 配置

### API密钥配置

#### 必需的密钥：OPENAI_API_KEY

1. **获取OpenAI API密钥**
   - 访问 https://platform.openai.com/api-keys
   - 创建新的API密钥
   - 复制密钥

2. **设置到.env文件**
   ```bash
   # .env
   OPENAI_API_KEY=sk-your-api-key-here
   ```

#### 可选的密钥：SERPAPI_API_KEY（研究模式）

1. **获取SerpAPI密钥**
   - 访问 https://serpapi.com
   - 注册并创建API密钥
   - 复制密钥

2. **设置到.env文件**
   ```bash
   # .env
   SERPAPI_API_KEY=your-serpapi-key-here
   ```

### 配置文件（config/config.yaml）

```yaml
# 修改LLM模型
llm:
  openai:
    model: gpt-4  # 从 gpt-3.5-turbo 升级到 gpt-4

# 修改搜索结果数量
search:
  results_per_query: 10  # 增加从 5 到 10

# 修改代码执行超时
code_execution:
  timeout: 60  # 从 30 增加到 60 秒

# 启用本地模型
llm:
  ollama:
    enabled: true
    model: llama2
```

## 基本使用

### 1. 简单问题咨询

```bash
# 基本对话
python -m src.main ask "你好，你能做什么？"

# 结果：AI会响应你的问题
```

### 2. 数学计算和编程

```bash
# 计算问题
python -m src.main solve "计算2的20次方"

# 编程问题
python -m src.main solve "写一个函数检查素数"

# 结果：
# - 生成的代码
# - 执行输出
# - 结果解释
```

### 3. 网络研究（需要SerpAPI）

```bash
# 研究查询
python -m src.main search "人工智能最新进展"

# 结果：
# - 搜索查询列表
# - 找到的来源
# - 信息总结
```

### 4. 自动模式（推荐）

```bash
# 让AI自动选择合适的模式
python -m src.main ask "2的10次方是多少？" --auto

# 自动识别为代码模式，生成和执行代码
```

### 5. 交互式聊天

```bash
# 进入聊天模式
python -m src.main chat

# 在聊天中可以：
# - 提出多个问题
# - 进行多轮对话
# - 键入 'clear' 清除历史
# - 键入 'exit' 或 'quit' 退出
```

## 高级用法

### Python API 使用

#### 示例1：数学问题求解

```python
import asyncio
from src.agents import CodeAgent
from src.llm import LLMManager
from src.tools import CodeExecutor
from src.utils import get_config

async def solve_math():
    config = get_config()
    llm = LLMManager(config=config)
    executor = CodeExecutor()
    agent = CodeAgent(llm, executor, config)

    # 求解问题
    result = await agent.solve("计算1到100的所有素数")

    print("代码:")
    print(result['code'])
    print("\n输出:")
    print(result['output'])
    print("\n解释:")
    print(result['explanation'])

asyncio.run(solve_math())
```

#### 示例2：网络研究

```python
import asyncio
from src.agents import ResearchAgent
from src.llm import LLMManager
from src.tools import SearchTool, ScraperTool
from src.utils import get_config

async def research_topic():
    config = get_config()
    llm = LLMManager(config=config)
    search = SearchTool(provider="serpapi", api_key=config.search.serpapi_key)
    scraper = ScraperTool()
    agent = ResearchAgent(llm, search, scraper, config)

    # 进行研究
    result = await agent.research("量子计算应用")

    print("来源:")
    for source in result['sources']:
        print(f"- {source['title']}")
        print(f"  {source['url']}")
    print("\n总结:")
    print(result['summary'])

asyncio.run(research_topic())
```

#### 示例3：对话系统

```python
import asyncio
from src.agents import ChatAgent
from src.llm import LLMManager
from src.utils import get_config

async def chat_session():
    config = get_config()
    llm = LLMManager(config=config)
    agent = ChatAgent(llm, config)

    # 多轮对话
    questions = [
        "什么是机器学习？",
        "它有哪些应用？",
        "如何学习这个领域？"
    ]

    for question in questions:
        response = await agent.chat(question)
        print(f"Q: {question}")
        print(f"A: {response}\n")

asyncio.run(chat_session())
```

### 自定义LLM提供商

```python
from src.llm import BaseLLM

class MyLLMClient(BaseLLM):
    def __init__(self, api_key):
        super().__init__("MyLLM")
        self.api_key = api_key

    async def complete(self, messages, **kwargs):
        # 实现你的API调用
        pass

    async def is_available(self):
        # 检查可用性
        return bool(self.api_key)

# 注册到LLMManager
from src.llm import LLMManager
llm = LLMManager(config)
llm.add_provider("my_llm", MyLLMClient(api_key="..."))
```

## 常见任务

### 任务1：求解数学方程

```bash
# 解二次方程
python -m src.main solve "解方程: x^2 + 5x + 6 = 0"

# 解线性方程组
python -m src.main solve "
使用sympy解方程组:
x + 2y = 7
3x - y = 5
"
```

### 任务2：数据分析

```bash
python -m src.main solve "
生成100个随机数据：
1. 计算平均值
2. 计算标准差
3. 找出最大最小值
4. 识别异常值
"
```

### 任务3：编程任务

```bash
python -m src.main solve "编写函数找出n以内的所有完全数"

# 输出会包括：
# - 完整的代码
# - 执行结果
# - 算法解释
```

### 任务4：数据可视化

```bash
python -m src.main solve "
使用matplotlib绘制：
1. 生成sin(x)数据，x从0到2π
2. 绘制曲线
3. 添加标签和标题
4. 显示网格
"
```

### 任务5：研究和学习

```bash
# 研究特定主题
python -m src.main search "深度学习的最新发展 2024"

# 会自动：
# 1. 生成搜索查询
# 2. 执行搜索
# 3. 抓取内容
# 4. 生成总结
```

### 任务6：实时问答

```bash
python -m src.main ask "Python中列表和元组有什么区别？" --auto
```

## 技巧和最佳实践

### 💡 技巧1：使用--auto进行自动路由

```bash
# 不需要指定模式，AI会自动选择
python -m src.main ask "问题或命令" --auto

# 优于：
# python -m src.main solve "..."
# python -m src.main search "..."
```

### 💡 技巧2：启用详细输出

```bash
# 使用--verbose查看更多详细信息
python -m src.main ask "问题" --verbose
python -m src.main solve "问题" --verbose
python -m src.main search "查询" --verbose
```

### 💡 技巧3：使用本地模型节省成本

```bash
# 安装Ollama
# https://ollama.ai/

# 在config.yaml中启用
llm:
  ollama:
    enabled: true
    model: llama2

# 无需API费用，离线工作
```

### 💡 技巧4：保存重要结果

```python
# 在Python脚本中保存结果
result = await code_agent.solve(problem)
with open("results.txt", "w") as f:
    f.write(result['output'])
```

### 💡 技巧5：组合多个查询

```bash
# Python脚本处理多个问题
import asyncio
from src.agents import CodeAgent
from src.utils import get_config

async def batch_solve():
    config = get_config()
    agent = CodeAgent(...)

    problems = [
        "计算1到100的和",
        "找出前20个素数",
        "计算10!阶乘"
    ]

    for problem in problems:
        result = await agent.solve(problem)
        print(f"✓ {problem}")

asyncio.run(batch_solve())
```

### ⚠️ 最佳实践1：始终使用虚拟环境

```bash
# 始终激活虚拟环境
source venv/bin/activate

# 检查是否激活
which python  # 应该显示venv路径
```

### ⚠️ 最佳实践2：保护你的API密钥

```bash
# 不要提交.env文件到版本控制
echo ".env" >> .gitignore

# 使用.env.example作为模板
# 在生产环境使用环境变量
```

### ⚠️ 最佳实践3：处理超时

```python
# 对于长运行任务，增加超时
config.code_execution.timeout = 120

# 或在config.yaml中设置
code_execution:
  timeout: 120
```

### ⚠️ 最佳实践4：监控成本

```bash
# 使用gpt-3.5-turbo而不是gpt-4以降低成本
llm:
  openai:
    model: gpt-3.5-turbo

# 对于本地使用，启用Ollama
```

### ⚠️ 最佳实践5：验证结果

```bash
# 对于重要的计算，始终验证结果
python -m src.main solve "你的问题" --verbose

# 查看生成的代码和输出
# 手动验证逻辑是否正确
```

## 故障排除快速参考

| 问题 | 解决方案 |
|------|--------|
| "API key not configured" | 检查.env文件并重新启动 |
| 超时 | 在config.yaml中增加timeout值 |
| "No module found" | 运行 `pip install -r requirements.txt` |
| 搜索不工作 | 确保设置了SERPAPI_API_KEY |
| 代码执行失败 | 使用--verbose查看错误详情 |

## 获得帮助

### 查看命令帮助
```bash
python -m src.main --help
python -m src.main ask --help
python -m src.main solve --help
python -m src.main search --help
```

### 查看系统信息
```bash
python -m src.main info
```

### 运行示例
```bash
python examples/basic_usage.py
```

### 查看文档
- `README.md` - 完整功能说明
- `QUICKSTART.md` - 快速入门
- `ARCHITECTURE.md` - 系统架构
- `TROUBLESHOOTING.md` - 故障排除

---

现在你已经掌握了AI Search Engine的所有用法！祝你使用愉快！
