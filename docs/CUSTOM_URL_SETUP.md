# 自定义URL快速设置指南

快速配置不同的LLM API端点和获取API密钥的完整列表。

## 📋 快速参考

| 提供商 | Base URL | API密钥获取 | 模型 |
|--------|----------|------------|------|
| **OpenAI** | `https://api.openai.com/v1` | https://platform.openai.com/account/api-keys | `gpt-3.5-turbo` |
| **DeepSeek** | `https://api.deepseek.com` | https://platform.deepseek.com | `deepseek-chat` |
| **Together AI** | `https://api.together.xyz/v1` | https://www.together.ai/settings/api-keys | `meta-llama/Llama-2-7b-hf` |
| **LM Studio** | `http://localhost:8000/v1` | 本地（无需密钥） | 自定义 |
| **vLLM** | `http://localhost:8000/v1` | 本地（无需密钥） | 自定义 |
| **Azure OpenAI** | `https://{resource}.openai.azure.com/v1` | Azure Portal | `gpt-35-turbo` |

---

## 🚀 5分钟快速设置

### 第1步：配置 .env 文件

```bash
# 进入项目目录
cd /Users/sudo/PycharmProjects/ai_search

# 复制示例文件
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

### 第2步：选择API提供商并获取密钥

#### 选项A: OpenAI（推荐入门）
```bash
# 1. 访问 https://platform.openai.com/account/api-keys
# 2. 创建新API密钥
# 3. 在 .env 中添加:
OPENAI_API_KEY=sk-your-actual-key-here
```

#### 选项B: DeepSeek（成本更低）
```bash
# 1. 访问 https://platform.deepseek.com
# 2. 获取API密钥
# 3. 在 .env 中添加:
DEEPSEEK_API_KEY=your-actual-key-here

# 4. 在 config/config.yaml 中启用:
llm:
  openai_compatible:
    deepseek:
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}
```

#### 选项C: 本地模型（完全免费）

**使用 LM Studio:**
```bash
# 1. 下载: https://lmstudio.ai
# 2. 安装并启动 LM Studio
# 3. 加载模型（如 Llama 2）
# 4. 启动服务器（会自动在 localhost:8000 运行）
# 5. config/config.yaml 中:

llm:
  openai_compatible:
    local_compatible:
      enabled: true
      api_key: "local-key"
      model: llama-2
      base_url: http://localhost:8000/v1
```

**使用 Ollama:**
```bash
# 1. 安装: https://ollama.ai
# 2. 运行: ollama serve
# 3. 在另一个终端: ollama pull llama2
# 4. config/config.yaml 中:

llm:
  ollama:
    enabled: true
    base_url: http://localhost:11434
    model: llama2
```

### 第3步：验证配置

```bash
# 创建 Conda 环境
conda create -n ai-search python=3.11
conda activate ai-search

# 安装依赖
pip install -r requirements.txt

# 验证设置
python -m src.main info

# 测试使用
python -m src.main ask "Hello" --auto
```

---

## 🔗 API端点完整列表

### OpenAI 官方
- **网站**: https://openai.com
- **API密钥**: https://platform.openai.com/account/api-keys
- **文档**: https://platform.openai.com/docs/api-reference
- **Base URL**: `https://api.openai.com/v1`
- **模型**: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo-preview`

### DeepSeek
- **网站**: https://www.deepseek.com
- **API平台**: https://platform.deepseek.com
- **GitHub**: https://github.com/deepseek-ai
- **Base URL**: `https://api.deepseek.com`
- **模型**: `deepseek-chat`, `deepseek-coder`

### Together AI
- **网站**: https://www.together.ai
- **API密钥**: https://www.together.ai/settings/api-keys
- **文档**: https://docs.together.ai
- **Base URL**: `https://api.together.xyz/v1`
- **模型**: 支持200+开源模型

### Azure OpenAI
- **网站**: https://azure.microsoft.com/en-us/products/cognitive-services/openai-service/
- **门户**: https://portal.azure.com
- **文档**: https://learn.microsoft.com/en-us/azure/cognitive-services/openai
- **Base URL**: `https://{resource-name}.openai.azure.com/v1`

### Replicate
- **网站**: https://replicate.com
- **API Token**: https://replicate.com/account/api-tokens
- **Base URL**: `https://api.replicate.com/v1`

### 本地服务

#### LM Studio
- **网站**: https://lmstudio.ai
- **下载**: https://lmstudio.ai/download
- **Base URL**: `http://localhost:8000/v1`
- **注意**: 完全本地，无需API密钥

#### vLLM
- **GitHub**: https://github.com/lm-sys/vLLM
- **文档**: https://docs.vllm.ai
- **安装**: `pip install vllm`
- **Base URL**: `http://localhost:8000/v1`

#### Ollama
- **网站**: https://ollama.ai
- **下载**: https://ollama.ai/download
- **Base URL**: `http://localhost:11434`
- **注意**: 专注于本地模型推理

---

## 📝 配置示例

### 示例1: 使用 DeepSeek API

**config/config.yaml:**
```yaml
llm:
  openai:
    enabled: false  # 禁用 OpenAI

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

**.env:**
```
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

### 示例2: 同时使用 OpenAI 和 DeepSeek（带Fallback）

**config/config.yaml:**
```yaml
llm:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
    base_url: https://api.openai.com/v1

  openai_compatible:
    deepseek:
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      base_url: https://api.deepseek.com
```

**.env:**
```
OPENAI_API_KEY=sk-openai-key
DEEPSEEK_API_KEY=sk-deepseek-key
```

**使用:**
```bash
# 默认使用 OpenAI，如果失败则自动切换到 DeepSeek
python -m src.main ask "Hello"

# 强制使用 DeepSeek
python -m src.main ask "Hello" --prefer deepseek
```

### 示例3: 本地开发（使用 LM Studio）

**config/config.yaml:**
```yaml
llm:
  openai:
    enabled: false

  openai_compatible:
    local_compatible:
      enabled: true
      api_key: "local-key"
      model: llama-2
      base_url: http://localhost:8000/v1
      provider_name: "LocalOpenAI"
```

**步骤:**
1. 下载并启动 LM Studio
2. 加载 Llama 2 模型
3. 启动服务器
4. 运行: `python -m src.main chat`

---

## 🔍 如何获取API密钥

### OpenAI
```
1. 访问 https://platform.openai.com/login
2. 登录或注册
3. 点击右上角头像 → API keys
4. 点击 "Create new secret key"
5. 复制密钥（重要：只会显示一次！）
6. 保存到 .env: OPENAI_API_KEY=sk-xxx
```

### DeepSeek
```
1. 访问 https://platform.deepseek.com
2. 创建账户或登录
3. 进入控制面板
4. 点击 "API Keys"
5. 创建新密钥
6. 复制并保存到 .env: DEEPSEEK_API_KEY=xxx
```

### Together AI
```
1. 访问 https://www.together.ai
2. 登录或注册
3. 进入 Settings → API Keys
4. 创建新密钥
5. 保存到 .env: TOGETHER_API_KEY=xxx
```

### Azure OpenAI
```
1. 登录 Azure Portal: https://portal.azure.com
2. 创建 "Cognitive Services" 资源
3. 获取端点和密钥
4. 在 config.yaml 中配置:
   base_url: https://{your-resource}.openai.azure.com/v1
   api_key: {your-key}
```

---

## 🐍 使用 Conda 管理环境

### 创建环境
```bash
# 创建环境
conda create -n ai-search python=3.11

# 激活环境
conda activate ai-search

# 安装依赖
pip install -r requirements.txt
```

### 管理多个环境
```bash
# 列出所有环境
conda env list

# 切换环境
conda activate ai-search

# 移除环境
conda env remove -n ai-search

# 导出环境配置
conda env export > environment.yml

# 从配置创建环境
conda env create -f environment.yml
```

### 推荐工作流
```bash
# 为项目创建隔离环境
conda create -n ai-search python=3.11

# 激活环境
conda activate ai-search

# 安装所有依赖
pip install -r requirements.txt

# 项目工作
python -m src.main chat

# 完成后激活环境
conda deactivate
```

---

## ⚠️ 常见问题排查

### 问题1: "API key not configured"
```bash
# 检查 .env 文件是否存在且正确
cat .env

# 检查 API 密钥格式
# OpenAI: 应以 sk- 开头
# DeepSeek: 应该是长字符串

# 验证配置被读取
python -c "from src.utils import get_config; print(get_config().llm)"
```

### 问题2: "Connection refused" 或 "Cannot connect"
```bash
# 检查 URL 格式
# 确保包含 /v1 路径
# 检查是否有代理/防火墙阻止
# 测试连接:
curl -i https://api.openai.com/v1

# 对于本地服务
curl -i http://localhost:8000/v1
```

### 问题3: "Invalid model" 或 "Model not found"
```bash
# 检查 config.yaml 中的模型名称
# 确保模型名称正确（拼写和大小写）
# 检查该提供商是否支持该模型

# 示例
OpenAI: gpt-3.5-turbo ✓
DeepSeek: deepseek-chat ✓
```

### 问题4: 速度慢或超时
```bash
# 增加超时时间 (config/config.yaml)
code_execution:
  timeout: 60  # 从 30 改为 60

research:
  timeout: 20

# 使用本地模型加速
# 或选择更快的模型
llm:
  openai:
    model: gpt-3.5-turbo  # 比 gpt-4 更快
```

---

## 💡 最佳实践

1. **密钥安全**
   - ✅ 使用 .env 文件存储密钥
   - ✅ 将 .env 添加到 .gitignore
   - ❌ 不要硬编码密钥
   - ❌ 不要提交 .env 文件到git

2. **环境隔离**
   - ✅ 为每个项目使用单独的 Conda 环境
   - ✅ 定期更新依赖
   - ✅ 使用 environment.yml 记录环境

3. **成本控制**
   - ✅ 使用 gpt-3.5-turbo（比 gpt-4 便宜）
   - ✅ 本地开发时使用本地模型
   - ✅ 监控API使用量

4. **配置管理**
   - ✅ 为不同的用途保存不同的配置
   - ✅ 使用注释记录配置的含义
   - ✅ 定期备份配置

---

## 🚀 开始使用

```bash
# 1. 进入项目
cd /Users/sudo/PycharmProjects/ai_search

# 2. 创建 Conda 环境
conda create -n ai-search python=3.11
conda activate ai-search

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API
cp .env.example .env
# 编辑 .env，添加 API 密钥

# 5. 选择提供商
# 编辑 config/config.yaml，启用所需的提供商

# 6. 验证
python -m src.main info

# 7. 使用
python -m src.main ask "你好" --auto
```

---

**更新于**: 2024年10月20日

有问题？查看 `API_ENDPOINTS_GUIDE.md` 获取更多详细信息！
