# Quick Start Guide

快速开始使用 AI Search Engine

## 1. 安装

### 1.1 克隆项目
```bash
cd /Users/sudo/PycharmProjects/ai_search
```

### 1.2 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 1.3 安装依赖
```bash
pip install -r requirements.txt
```

## 2. 配置API密钥

### 2.1 创建 .env 文件
```bash
cp .env.example .env
```

### 2.2 编辑 .env 文件，添加你的API密钥

**必需的 API 密钥:**
- `OPENAI_API_KEY`: 从 https://platform.openai.com/api-keys 获取

**可选的 API 密钥:**
- `SERPAPI_API_KEY`: 从 https://serpapi.com 获取（用于研究模式）
- `DEEPSEEK_API_KEY`: 从 https://deepseek.com 获取（可选）

## 3. 快速测试

### 3.1 查看系统信息
```bash
python -m src.main info
```

### 3.2 简单对话
```bash
python -m src.main ask "Hello, what can you do?"
```

### 3.3 数学计算
```bash
python -m src.main solve "Calculate 2^20"
```

### 3.4 自动模式（推荐）
```bash
python -m src.main ask "What is 10! (factorial)?" --auto
```

## 4. 常见使用场景

### 场景1: 解决数学问题
```bash
python -m src.main solve "Solve the equation: x^2 - 5x + 6 = 0"
```

### 场景2: 编程问题
```bash
python -m src.main solve "Write a function to check if a number is prime"
```

### 场景3: 数据分析
```bash
python -m src.main solve "Generate 100 random numbers and find the mean, median, and std deviation"
```

### 场景4: 网络研究（需要SerpAPI）
```bash
python -m src.main search "Latest breakthroughs in artificial intelligence 2024"
```

### 场景5: 交互式聊天
```bash
python -m src.main chat
```

## 5. Python API 使用

创建 `test_script.py`:
```python
import asyncio
from src.agents import CodeAgent
from src.llm import LLMManager
from src.tools import CodeExecutor
from src.utils import get_config

async def main():
    config = get_config()
    llm_manager = LLMManager(config=config)
    code_executor = CodeExecutor()
    code_agent = CodeAgent(llm_manager, code_executor, config)

    result = await code_agent.solve("Calculate the Fibonacci sequence up to 10 terms")
    print(result['output'])
    print(result['explanation'])

if __name__ == "__main__":
    asyncio.run(main())
```

运行:
```bash
python test_script.py
```

## 6. 故障排除

### 问题1: "OPENAI_API_KEY not configured"
**解决方案:**
1. 确保 `.env` 文件存在
2. 检查 `OPENAI_API_KEY=` 后面是否有有效的API密钥
3. 运行 `python -m src.main info` 检查配置

### 问题2: 代码执行超时
**解决方案:**
- 编辑 `config/config.yaml`，增加 `code_execution.timeout`
- 默认为 30 秒，可以改为 60 或更大

### 问题3: 搜索功能不工作
**解决方案:**
1. 确保 `SERPAPI_API_KEY` 已设置
2. 检查网络连接
3. 运行 `python -m src.main search "test query"` 检查

### 问题4: 导入错误
**解决方案:**
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 确保虚拟环境激活
source venv/bin/activate  # Mac/Linux
# 或
venv\Scripts\activate  # Windows
```

## 7. 性能提示

1. **启用本地模型（Ollama）** 以减少API调用成本
2. **使用缓存** - 相同的查询不会重复搜索
3. **批量操作** - 如果可能，将多个查询组合在一起
4. **异步处理** - 系统已优化用于并发操作

## 8. 下一步

- 查看 `examples/basic_usage.py` 了解更多示例
- 阅读 `README.md` 获得完整文档
- 尝试 `chat` 命令进行交互式使用
- 自定义 `config/config.yaml` 以满足您的需求

## 9. 获得帮助

### 查看命令帮助
```bash
python -m src.main --help
python -m src.main solve --help
python -m src.main search --help
```

### 启用详细日志
```bash
python -m src.main ask "test" --verbose
```

## 10. 推荐工作流

### 对于研究任务
```bash
# 1. 进行研究
python -m src.main search "Your research topic"

# 2. 或使用自动模式
python -m src.main ask "Your question about the topic?" --auto
```

### 对于编程/数学任务
```bash
# 1. 简单问题
python -m src.main solve "Your math/code problem"

# 2. 查看生成的代码
python -m src.main solve "Your problem" --verbose
```

### 对于交互式探索
```bash
# 启动聊天模式
python -m src.main chat

# 在聊天中可以：
# - 提问
# - 进行多轮对话
# - 键入 'clear' 清除历史
# - 键入 'exit' 或 'quit' 退出
```

---

现在你已经准备好使用 AI Search Engine 了！祝你使用愉快！
