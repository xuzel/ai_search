# API 端点配置指南

本指南说明如何配置OpenAI兼容的API提供商，包括获取API密钥和设置自定义URL的步骤。

## 目录
1. [OpenAI](#openai)
2. [DeepSeek](#deepseek)
3. [本地服务器](#本地服务器)
4. [其他兼容提供商](#其他兼容提供商)
5. [配置方法](#配置方法)
6. [Conda环境管理](#conda环境管理)

---

## OpenAI

### 官方网站
🌐 https://openai.com

### 获取API密钥

1. **访问 OpenAI Platform**
   - 登录: https://platform.openai.com/login
   - 没有账户？注册: https://platform.openai.com/signup

2. **获取API密钥**
   - 进入 "API keys" 页面: https://platform.openai.com/account/api-keys
   - 点击 "Create new secret key"
   - 复制密钥并保存（只会显示一次）

### 可用模型
- `gpt-4` - 最强大的模型
- `gpt-4-turbo` - 更快的GPT-4变体
- `gpt-3.5-turbo` - 最经济的选择（推荐）
- `gpt-3.5-turbo-16k` - 更大的上下文窗口

### API端点
```
Base URL: https://api.openai.com/v1
Chat Completion: https://api.openai.com/v1/chat/completions
```

### 配置示例

#### .env 文件
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

#### config/config.yaml
```yaml
llm:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
    base_url: https://api.openai.com/v1
    temperature: 0.7
    max_tokens: 2000
```

### 成本
- GPT-3.5-turbo: $0.0005/1K tokens (input), $0.0015/1K tokens (output)
- GPT-4: $0.03/1K tokens (input), $0.06/1K tokens (output)

### 文档
- 官方文档: https://platform.openai.com/docs
- API参考: https://platform.openai.com/docs/api-reference

---

## DeepSeek

### 官方网站
🌐 https://www.deepseek.com

### 获取API密钥

1. **访问 DeepSeek**
   - 官网: https://www.deepseek.com
   - 文档: https://github.com/deepseek-ai
   - API平台: https://platform.deepseek.com

2. **创建API密钥**
   - 注册账户
   - 进入控制面板
   - 创建新的API密钥
   - 复制保存

### 可用模型
- `deepseek-chat` - 主要对话模型
- `deepseek-coder` - 代码专用模型
- 其他变体请查阅最新文档

### API端点
```
Base URL: https://api.deepseek.com
Chat Completion: https://api.deepseek.com/chat/completions
```

### 配置示例

#### .env 文件
```bash
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

#### config/config.yaml
```yaml
llm:
  openai_compatible:
    deepseek:
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      base_url: https://api.deepseek.com
      temperature: 0.7
      max_tokens: 2000
      provider_name: "DeepSeek"
```

### 成本
- 检查官方定价: https://www.deepseek.com/pricing

### 使用示例
```python
from src.llm import LLMManager
from src.utils import get_config

config = get_config()
llm = LLMManager(config=config)

# DeepSeek会自动初始化
response = await llm.complete(
    messages=[{"role": "user", "content": "Hello"}],
    preferred_provider="deepseek"
)
```

### 文档
- GitHub: https://github.com/deepseek-ai
- API文档: https://github.com/deepseek-ai/DeepSeek-API

---

## 本地服务器

如果使用本地OpenAI兼容服务器（如LM Studio、vLLM等），可以直接指向本地URL。

### LM Studio

🌐 https://lmstudio.ai

#### 安装和运行
1. 下载 LM Studio: https://lmstudio.ai
2. 安装并启动
3. 加载模型
4. 启动本地服务器（通常在 `http://localhost:8000`）

#### 可用模型
- 支持Hugging Face上的大多数模型
- 热门选择: Llama 2, Mistral, Neural Chat等

#### API端点
```
Base URL: http://localhost:8000/v1
Chat Completion: http://localhost:8000/v1/chat/completions
```

#### 配置示例

##### config/config.yaml
```yaml
llm:
  openai_compatible:
    local_compatible:
      enabled: true
      api_key: "local-key"  # 本地无需真实密钥
      model: llama-2        # 使用你加载的模型
      base_url: http://localhost:8000/v1
      temperature: 0.7
      max_tokens: 2000
      provider_name: "LocalOpenAI"
```

#### 使用示例
```python
response = await llm.complete(
    messages=[...],
    preferred_provider="local_compatible"
)
```

### vLLM

🌐 https://github.com/lm-sys/vLLM

#### 安装和运行
```bash
# 安装 vLLM
pip install vllm

# 启动服务器
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-hf \
  --port 8000
```

#### API端点
```
Base URL: http://localhost:8000/v1
```

#### 配置示例
同LM Studio，只需改变base_url指向vLLM实例

### 其他本地选项
- **Ollama** - 已内置支持（参见 `Ollama Local Model Configuration`）
- **Text Generation WebUI** - 支持OpenAI兼容API
- **LocalAI** - 本地LLM推理引擎

---

## 其他兼容提供商

### Together AI

🌐 https://www.together.ai

#### 获取API密钥
1. 注册: https://www.together.ai
2. 获取API密钥: https://www.together.ai/settings/api-keys

#### API端点
```
Base URL: https://api.together.xyz/v1
```

#### 配置示例
```yaml
llm:
  openai_compatible:
    together_ai:
      enabled: true
      api_key: ${TOGETHER_API_KEY}
      model: meta-llama/Llama-2-7b-hf
      base_url: https://api.together.xyz/v1
      provider_name: "TogetherAI"
```

### Replicate

🌐 https://replicate.com

#### 获取API密钥
1. 注册: https://replicate.com/signin
2. API Token: https://replicate.com/account/api-tokens

#### API端点
```
Base URL: https://api.replicate.com/v1
```

### Azure OpenAI

如果使用 Azure 提供的 OpenAI 服务：

#### API端点格式
```
Base URL: https://{resource-name}.openai.azure.com/v1
```

#### 配置示例
```yaml
llm:
  openai:
    enabled: true
    api_key: ${AZURE_OPENAI_KEY}
    model: gpt-35-turbo
    base_url: https://your-resource.openai.azure.com/v1
```

---

## 配置方法

### 方法1: 使用 .env 文件

1. **创建 .env 文件**
   ```bash
   cp .env.example .env
   ```

2. **添加API密钥**
   ```bash
   # .env
   OPENAI_API_KEY=sk-your-key
   DEEPSEEK_API_KEY=your-deepseek-key
   TOGETHER_API_KEY=your-together-key
   ```

3. **验证配置**
   ```bash
   python -m src.main info
   ```

### 方法2: 编辑 config/config.yaml

直接修改配置文件中的 `base_url` 和 `api_key`：

```yaml
llm:
  openai:
    enabled: true
    api_key: sk-your-key
    base_url: https://api.openai.com/v1  # 修改这里
    model: gpt-3.5-turbo
```

### 方法3: 通过Python代码

```python
from src.llm import OpenAIClient, LLMManager

# 直接创建客户端
client = OpenAIClient(
    api_key="your-api-key",
    model="gpt-3.5-turbo",
    base_url="https://your-custom-endpoint.com/v1",
    provider_name="CustomProvider"
)

# 或通过LLMManager
llm = LLMManager()
llm.add_provider("custom", client)
```

---

## 优先级和Fallback

系统会按以下优先级尝试LLM提供商：

1. **preferred_provider** - 如果指定
2. **_primary_provider** - 第一个配置的提供商
3. **其他配置的提供商** - 按配置顺序
4. **如果全部失败** - 抛出错误

### 自动Fallback示例
```python
# 如果 OpenAI 不可用，会自动尝试 DeepSeek
response = await llm.complete(messages=[...])
```

---

## Conda 环境管理

如您提到的，使用 Conda 来管理环境是一个最佳实践。

### 创建Conda环境

```bash
# 创建新环境
conda create -n ai-search python=3.11

# 激活环境
conda activate ai-search

# 安装依赖
pip install -r requirements.txt
```

### 环境管理最佳实践

```bash
# 查看所有环境
conda env list

# 创建带特定Python版本的环境
conda create -n ai-search python=3.11 pip

# 激活环境
conda activate ai-search

# 在环境中安装包
pip install -r requirements.txt

# 导出环境配置
conda env export > environment.yml

# 从配置文件重建环境
conda env create -f environment.yml

# 移除环境
conda env remove -n ai-search

# 更新所有包
conda update --all
```

### 创建 environment.yml 文件

```yaml
# environment.yml
name: ai-search
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - pip:
    - -r requirements.txt
```

### 推荐的工作流

```bash
# 1. 克隆项目
git clone <your-repo>
cd ai_search

# 2. 创建Conda环境
conda create -n ai-search python=3.11

# 3. 激活环境
conda activate ai-search

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置API密钥
cp .env.example .env
# 编辑 .env 文件

# 6. 验证设置
python -m src.main info

# 7. 开始使用
python -m src.main ask "Hello" --auto
```

---

## 常见问题

### Q1: 如何切换API提供商？

```python
# 在命令行中指定
python -m src.main ask "问题" --auto

# 在Python中指定
response = await llm.complete(
    messages=[...],
    preferred_provider="deepseek"  # 或 "local_compatible"
)
```

### Q2: 自定义URL不工作怎么办？

检查以下几点：
1. URL格式是否正确（应包含 `/v1`）
2. API密钥是否有效
3. 服务器是否在线且可访问
4. 防火墙/代理设置是否允许访问
5. 查看详细日志: `python -m src.main ask "test" --verbose`

### Q3: 如何在多个LLM之间切换？

```python
# config.yaml 中启用多个提供商
llm:
  openai:
    enabled: true
  deepseek:
    enabled: true
  local_compatible:
    enabled: true

# 然后在运行时选择
response = await llm.complete(
    messages=[...],
    preferred_provider="deepseek"
)
```

### Q4: 本地服务器需要网络连接吗？

不需要。本地服务器（如LM Studio、vLLM）运行在 `localhost`，完全离线工作。

### Q5: 如何测试新的API端点？

```bash
# 启用详细模式
python -m src.main ask "test" --verbose

# 或编写测试脚本
python << 'EOF'
import asyncio
from src.llm import OpenAIClient

async def test():
    client = OpenAIClient(
        api_key="your-key",
        base_url="https://your-endpoint/v1",
        provider_name="Test"
    )
    if await client.is_available():
        response = await client.complete([
            {"role": "user", "content": "Hello"}
        ])
        print(response)

asyncio.run(test())
EOF
```

---

## 安全提示

1. **不要硬编码API密钥**
   - ❌ 错误: `api_key: "sk-xxx"`
   - ✅ 正确: `api_key: ${OPENAI_API_KEY}`

2. **使用 .env 文件**
   - 将 `.env` 添加到 `.gitignore`
   - 只提交 `.env.example`

3. **环境变量隔离**
   - 为不同的API使用不同的环境变量
   - 定期轮换API密钥

4. **Conda环境隔离**
   - 为不同项目使用不同的Conda环境
   - 避免全局安装依赖

---

## 联系和支持

- OpenAI: https://help.openai.com
- DeepSeek: https://github.com/deepseek-ai/DeepSeek-API/issues
- 本地工具问题: 查看相应项目的GitHub issues

---

**更新于**: 2024年10月20日

祝您使用愉快！🚀
