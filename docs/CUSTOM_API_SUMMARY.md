# 自定义API配置总结

已为AI Search Engine添加了完整的自定义URL和多API提供商支持。

## ✨ 新增功能

### 1. OpenAI兼容API支持
- 支持任何兼容OpenAI格式的API
- 只需修改 `base_url` 和 `api_key`
- 支持自定义 `provider_name`

### 2. 多提供商配置
- **OpenAI** - 官方API
- **DeepSeek** - 低成本替代方案
- **本地兼容服务** - LM Studio、vLLM等
- **Azure OpenAI** - 企业解决方案
- **Together AI** - 多模型平台
- **Replicate** - 按使用量付费

### 3. Fallback机制
- 自动尝试多个提供商
- 如果一个失败，自动切换到下一个
- 优先级可配置

### 4. Conda环境管理
- 完整的环境隔离
- 依赖管理最佳实践
- 可重复的设置步骤

## 📁 修改的文件

### 1. src/llm/openai_client.py
**改动内容：**
- 添加 `base_url` 参数（支持自定义URL）
- 添加 `provider_name` 参数（自定义显示名称）
- 动态设置 `openai.api_base`
- 更新文档和类型提示

**关键改动：**
```python
def __init__(
    self,
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    base_url: Optional[str] = None,        # 新增
    provider_name: str = "OpenAI",          # 新增
):
```

### 2. src/utils/config.py
**改动内容：**
- OpenAI配置：添加 `base_url` 和 `provider_name`
- 新增 DeepSeek 配置部分
- 新增本地兼容服务配置
- 扩展 LLMConfig 类

**新增配置字段：**
```python
# OpenAI
openai_base_url: str = "https://api.openai.com/v1"
openai_provider_name: str = "OpenAI"

# DeepSeek
deepseek_enabled: bool = False
deepseek_api_key: str = ...
deepseek_base_url: str = "https://api.deepseek.com"
deepseek_model: str = "deepseek-chat"

# Local compatible
local_compatible_enabled: bool = False
local_compatible_base_url: str = "http://localhost:8000/v1"
```

### 3. src/llm/manager.py
**改动内容：**
- 支持加载 OpenAI 的自定义 base_url
- 添加 DeepSeek 提供商初始化
- 添加本地兼容服务初始化
- 更新初始化日志

**新增初始化代码：**
```python
# DeepSeek 初始化
if self.config and self.config.llm.deepseek_enabled:
    self.providers["deepseek"] = OpenAIClient(...)

# Local compatible 初始化
if self.config and self.config.llm.local_compatible_enabled:
    self.providers["local_compatible"] = OpenAIClient(...)
```

### 4. config/config.yaml
**改动内容：**
- OpenAI 配置添加 base_url 和 provider_name
- 新增 openai_compatible 配置部分
- 包含 DeepSeek、本地服务、其他提供商的示例
- 详细注释说明

**新增配置块：**
```yaml
llm:
  openai:
    base_url: https://api.openai.com/v1
    provider_name: "OpenAI"

  openai_compatible:
    deepseek:
      base_url: https://api.deepseek.com
    local_compatible:
      base_url: http://localhost:8000/v1
```

### 5. .env.example
**改动内容：**
- 添加所有LLM API密钥配置项
- 组织为清晰的分类（LLM、搜索、本地模型）
- 添加所有支持的提供商URL

## 📖 新增文档

### 1. API_ENDPOINTS_GUIDE.md
**内容：**
- OpenAI、DeepSeek、本地服务详细配置
- 获取API密钥的完整步骤
- 可用模型列表
- 成本信息
- 配置方法（.env、YAML、Python代码）
- 优先级和Fallback说明
- Conda环境管理
- 常见问题Q&A

### 2. CUSTOM_URL_SETUP.md
**内容：**
- 快速参考表格（提供商、URL、密钥获取、模型）
- 5分钟快速设置指南
- API端点完整列表
- 配置示例（OpenAI、DeepSeek、本地）
- API密钥获取步骤
- Conda环境管理快速指南
- 排查指南
- 最佳实践

### 3. CUSTOM_API_SUMMARY.md
**内容：**
- 本文件，总结所有改动

## 🔧 使用示例

### 示例1：使用 DeepSeek

```bash
# 1. 配置 .env
DEEPSEEK_API_KEY=your-deepseek-key

# 2. 编辑 config/config.yaml
llm:
  openai_compatible:
    deepseek:
      enabled: true

# 3. 运行
python -m src.main ask "问题" --auto
```

### 示例2：本地模型（LM Studio）

```bash
# 1. 启动 LM Studio 服务
# (自动在 localhost:8000 运行)

# 2. 编辑 config/config.yaml
llm:
  openai_compatible:
    local_compatible:
      enabled: true
      base_url: http://localhost:8000/v1

# 3. 运行（完全离线）
python -m src.main chat
```

### 示例3：Python代码直接使用

```python
from src.llm import OpenAIClient

# 创建自定义提供商客户端
client = OpenAIClient(
    api_key="your-key",
    model="your-model",
    base_url="https://your-api.com/v1",
    provider_name="CustomProvider"
)

# 使用
response = await client.complete(messages=[...])
```

## 📋 API端点速查

| 提供商 | Base URL | 如何获取密钥 |
|--------|----------|------------|
| OpenAI | `https://api.openai.com/v1` | https://platform.openai.com/api-keys |
| DeepSeek | `https://api.deepseek.com` | https://platform.deepseek.com |
| Together AI | `https://api.together.xyz/v1` | https://www.together.ai/settings/api-keys |
| Azure | `https://{resource}.openai.azure.com/v1` | Azure Portal |
| 本地(LM Studio) | `http://localhost:8000/v1` | 无需密钥 |
| 本地(vLLM) | `http://localhost:8000/v1` | 无需密钥 |

## ⚙️ Conda环境设置

```bash
# 创建环境
conda create -n ai-search python=3.11

# 激活环境
conda activate ai-search

# 安装依赖
pip install -r requirements.txt

# 项目工作...

# 完成后停用
conda deactivate
```

## ✅ 配置检查清单

- [ ] 选择要使用的LLM提供商
- [ ] 获取API密钥（如需要）
- [ ] 添加密钥到 .env 文件
- [ ] 在 config/config.yaml 中启用提供商
- [ ] 运行 `python -m src.main info` 验证
- [ ] 测试 `python -m src.main ask "test" --auto`

## 🚀 快速开始

```bash
# 1. 克隆/进入项目
cd /Users/sudo/PycharmProjects/ai_search

# 2. 创建Conda环境
conda create -n ai-search python=3.11
conda activate ai-search

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置API
cp .env.example .env
# 编辑 .env，添加 API 密钥

# 5. 配置提供商
nano config/config.yaml
# 启用所需的提供商，设置base_url

# 6. 验证
python -m src.main info

# 7. 开始使用
python -m src.main ask "你好" --auto
```

## 📚 文档导航

| 文档 | 用途 |
|-----|------|
| API_ENDPOINTS_GUIDE.md | 详细的API配置和获取指南 |
| CUSTOM_URL_SETUP.md | 5分钟快速设置和快速参考 |
| CUSTOM_API_SUMMARY.md | 本文件，改动总结 |
| README.md | 项目总体说明 |
| QUICKSTART.md | 快速开始 |

## 🔍 故障排除

**API连接失败？**
```bash
# 检查配置
python -m src.main info

# 查看详细日志
python -m src.main ask "test" --verbose

# 测试连接
curl -i https://api.openai.com/v1
```

**模型不支持？**
- 检查模型名称是否正确
- 确认该提供商支持该模型
- 查看文档获取最新模型列表

**本地服务无法连接？**
- 确保服务正在运行
- 检查 base_url 是否正确
- 确认防火墙不阻止连接

## 💡 提示

1. **多提供商Fallback**
   - 启用多个提供商以获得故障转移
   - 系统会自动尝试其他提供商

2. **成本优化**
   - 本地开发使用 LM Studio 或 Ollama（免费）
   - 生产环境使用 DeepSeek（比OpenAI便宜）

3. **性能优化**
   - gpt-3.5-turbo 比 gpt-4 快且便宜
   - 本地模型响应最快

4. **安全实践**
   - 将 .env 添加到 .gitignore
   - 定期轮换API密钥
   - 不要提交密钥到版本控制

## 📝 更新日期

- **创建日期**: 2024年10月20日
- **最后更新**: 2024年10月20日
- **状态**: ✅ 完成

## 🎉 总结

AI Search Engine现在支持：

✅ OpenAI官方API
✅ DeepSeek低成本API
✅ 本地模型服务（LM Studio、vLLM等）
✅ 其他兼容提供商
✅ 自定义URL配置
✅ 自动Fallback机制
✅ Conda环境隔离

所有配置已完全记录和示例化，可以立即开始使用！

---

**需要帮助？**
- 查看 `API_ENDPOINTS_GUIDE.md` 获取详细说明
- 查看 `CUSTOM_URL_SETUP.md` 获取快速参考
- 运行 `python -m src.main --help` 获取命令帮助
