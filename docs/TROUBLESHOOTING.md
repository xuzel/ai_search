# Troubleshooting Guide

AI Search Engine 故障排除指南

## 常见错误和解决方案

### 1. API 和配置错误

#### 错误: "OPENAI_API_KEY not configured"
```
Error: OPENAI_API_KEY not configured
```

**原因:**
- `.env` 文件不存在或未设置
- API密钥无效
- 配置文件加载失败

**解决步骤:**
```bash
# 1. 检查 .env 文件是否存在
ls -la .env

# 2. 如果不存在，创建它
cp .env.example .env

# 3. 编辑 .env 文件并添加你的API密钥
nano .env  # 或使用你喜欢的编辑器

# 4. 验证配置
python -c "from src.utils import get_config; c = get_config(); print(c.llm.openai_api_key[:10])"
```

#### 错误: "All LLM providers failed"
```
Error: All LLM providers failed. Last error: ...
```

**原因:**
- 所有配置的LLM提供商都不可用
- 网络连接问题
- API密钥无效

**解决步骤:**
```bash
# 1. 检查网络连接
ping openai.com

# 2. 验证API密钥格式
# OpenAI API密钥应该以 'sk-' 开头

# 3. 检查提供商状态
python -m src.main info

# 4. 尝试测试API连接
python -c "
import asyncio
from src.llm import OpenAIClient
async def test():
    client = OpenAIClient(api_key='your-key-here')
    result = await client.is_available()
    print(f'OpenAI available: {result}')
asyncio.run(test())
"
```

### 2. 代码执行错误

#### 错误: "Execution timeout"
```
Execution timeout (>30s)
```

**原因:**
- 代码执行时间超过限制（默认30秒）
- 代码陷入无限循环
- 算法效率低下

**解决步骤:**
```bash
# 1. 增加超时时间
# 编辑 config/config.yaml
# 将 code_execution.timeout 改为更大的值，如 60

code_execution:
  timeout: 60  # 从 30 改为 60

# 2. 优化代码
# 使用更高效的算法或数据结构

# 3. 检查是否有无限循环
# 查看生成的代码并手动验证
```

#### 错误: "Dangerous pattern detected"
```
Error: Dangerous pattern detected: open(
```

**原因:**
- 代码包含危险的操作（文件I/O、系统命令等）
- 安全检查阻止了不安全的代码执行

**解决步骤:**
```bash
# 这是预期的安全行为！
# 如果你需要进行危险操作，请：

# 1. 在沙箱环境中手动运行代码
python your_script.py

# 2. 或修改代码以避免危险操作
# 例如，使用内存中的字符串而不是文件I/O
```

#### 错误: "Import not allowed"
```
Error: Import not allowed: requests
```

**原因:**
- 导入的模块不在允许列表中
- 配置限制了可用的导入

**解决步骤:**
```bash
# 1. 检查允许的导入
# 编辑 config/config.yaml

code_execution:
  allowed_imports:
    - numpy
    - pandas
    - scipy
    - requests  # 添加需要的模块

# 2. 使用标准库或允许的模块
# 标准库模块（math, statistics等）通常是允许的
```

### 3. 搜索和爬虫错误

#### 错误: "SerpAPI key not configured"
```
Error: SerpAPI key not configured
```

**原因:**
- 没有设置SerpAPI API密钥
- 使用了搜索功能但没有配置

**解决步骤:**
```bash
# 1. 获取SerpAPI密钥
# 访问 https://serpapi.com

# 2. 设置环境变量
echo "SERPAPI_API_KEY=your-key-here" >> .env

# 3. 验证配置
python -m src.main info
```

#### 错误: "Failed to fetch URL"
```
Failed to fetch {url}: status 403
```

**原因:**
- 网站拒绝了请求
- User-Agent被识别为爬虫
- 网站有反爬虫措施

**解决步骤:**
```bash
# 1. 等待一段时间后重试
# 网站可能有速率限制

# 2. 修改User-Agent
# 编辑 config/config.yaml
scraper:
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."

# 3. 使用不同的搜索源
search:
  provider: google_search  # 改为其他提供商
```

#### 错误: "Timeout fetching URL"
```
Timeout fetching {url}
```

**原因:**
- 网络连接慢
- 网站响应时间长
- 超时设置太短

**解决步骤:**
```bash
# 1. 增加超时时间
# 编辑 config/config.yaml
scraper:
  timeout: 20  # 从 10 改为 20

search:
  timeout: 15  # 增加搜索超时
```

### 4. 安装和依赖错误

#### 错误: "ModuleNotFoundError: No module named 'src'"
```
ModuleNotFoundError: No module named 'src'
```

**原因:**
- Python路径不正确
- 从错误的目录运行
- 虚拟环境未激活

**解决步骤:**
```bash
# 1. 确认在正确的目录
pwd  # 应该是 /Users/sudo/PycharmProjects/ai_search

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 运行命令时使用正确的格式
python -m src.main info

# 不要这样：
# python src/main.py info  # 错误

# 要这样：
# python -m src.main info  # 正确
```

#### 错误: "No module named 'openai'"
```
ModuleNotFoundError: No module named 'openai'
```

**原因:**
- 依赖未安装
- 虚拟环境不正确
- 使用了系统Python而不是虚拟环境

**解决步骤:**
```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 检查虚拟环境
which python  # 应该显示 venv 路径

# 3. 重新安装依赖
pip install --upgrade -r requirements.txt

# 4. 验证安装
python -c "import openai; print(openai.__version__)"
```

### 5. 性能问题

#### 问题: 命令执行非常慢

**原因:**
- 并发工作者太多导致系统过载
- 网络延迟
- LLM API响应慢

**解决步骤:**
```bash
# 1. 减少并发工作者
# 编辑 config/config.yaml
scraper:
  max_workers: 3  # 从 5 改为 3

# 2. 使用本地模型
# 编辑 config/config.yaml
llm:
  ollama:
    enabled: true  # 启用本地模型
    model: llama2

# 3. 启用缓存
# 编辑 config/config.yaml
cache:
  enabled: true
  ttl_seconds: 3600  # 1小时缓存
```

### 6. 日志和调试

#### 启用详细日志
```bash
# 使用 --verbose 标志
python -m src.main ask "test" --verbose

# 编辑 config/config.yaml
cli:
  verbose: true
```

#### 查看完整错误堆栈
```bash
# 使用 --verbose 标志会显示完整的traceback
python -m src.main solve "problem" --verbose
```

#### 手动测试组件
```python
# test_component.py
import asyncio
from src.llm import LLMManager
from src.utils import get_config

async def main():
    config = get_config()
    llm = LLMManager(config=config)

    # 测试LLM
    response = await llm.complete([
        {"role": "user", "content": "Hello"}
    ])
    print(response)

asyncio.run(main())
```

## 获得帮助

1. **检查日志**
   - 大多数错误都会记录详细信息
   - 使用 `--verbose` 标志获得更多详息

2. **查看示例**
   - `examples/basic_usage.py` 包含工作示例
   - 参考示例代码进行调试

3. **测试单个组件**
   - 独立测试搜索、LLM、代码执行
   - 逐个排除问题

4. **检查配置**
   - 验证 `config/config.yaml`
   - 检查 `.env` 文件
   - 运行 `python -m src.main info`

## 进阶调试

### 启用Python调试
```python
import pdb
pdb.set_trace()  # 在代码中设置断点

# 或使用 post_mortem 调试异常
import pdb
import sys
try:
    # 你的代码
except Exception as e:
    pdb.post_mortem(sys.exc_info()[2])
```

### 性能分析
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 你的代码

profiler.disable()
stats = pstats.Stats(profiler)
stats.print_stats()
```

---

如果问题仍未解决，请：
1. 查看完整的错误信息和日志
2. 检查 README.md 和示例代码
3. 验证所有API密钥和配置
4. 尝试在Python REPL中手动测试组件
