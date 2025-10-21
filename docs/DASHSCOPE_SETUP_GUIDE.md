# 🚀 阿里云 DashScope 完整配置指南

根据官方文档修复的 DashScope 集成指南。

## 问题回顾

原来的代码使用 OpenAI 格式的 API 密钥（以 `sk-` 开头），但阿里云 DashScope 使用不同格式的密钥。

**之前的错误**:
```
Error code: 401 - Incorrect API key provided: sk-e9c08*****...
```

**原因**:
1. 环境变量名称不同：OpenAI 用 `OPENAI_API_KEY`，DashScope 用 `DASHSCOPE_API_KEY`
2. 密钥格式完全不同：OpenAI 以 `sk-` 开头，DashScope 是自己的格式

## ✅ 修复内容

### 1. 代码修改（4个文件）

#### ✓ config.yaml
```yaml
llm:
  # OpenAI 配置（禁用）
  openai:
    enabled: false

  # ✨ 新增：DashScope 配置（启用）
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max
    temperature: 0.7
    max_tokens: 20000
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    provider_name: "Aliyun DashScope"
```

#### ✓ .env 文件
```bash
# ✨ 新增：DashScope 密钥配置
DASHSCOPE_API_KEY=your-actual-dashscope-api-key-here
```

#### ✓ src/utils/config.py
```python
# 新增 DashScope 配置类
dashscope_api_key: str = Field(default_factory=lambda: os.getenv('DASHSCOPE_API_KEY', ''))
dashscope_model: str = "qwen3-max"
dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

#### ✓ src/llm/manager.py
```python
# 新增 DashScope 提供商初始化
if self.config and self.config.llm.dashscope_api_key:
    self.providers["dashscope"] = OpenAIClient(
        api_key=self.config.llm.dashscope_api_key,
        model=self.config.llm.dashscope_model,
        base_url=self.config.llm.dashscope_base_url,
        provider_name="Aliyun DashScope",
    )
```

### 2. 新增文档
- ✓ `ALIYUN_DASHSCOPE_SETUP.md` - 详细配置指南
- ✓ `DASHSCOPE_SETUP_GUIDE.md` - 本文件

## 🔧 快速配置（3步）

### 步骤1：获取 DashScope API 密钥

```
1. 访问: https://dashscope.console.aliyun.com/
2. 登录阿里云账号
3. 进入 "API密钥管理"
4. 创建并复制新的 API 密钥
```

### 步骤2：配置 .env 文件

```bash
# 编辑 .env
DASHSCOPE_API_KEY=你的真实api密钥
```

### 步骤3：验证配置

```bash
python -m src.main info
# 应该看到: DashScope provider initialized
```

## 📝 官方文档参考

根据官方示例修改的代码：

**官方示例** (来自 https://help.aliyun.com/):
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # ← 注意密钥名称
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen3-max",
    messages=[{"role": "user", "content": "你是谁？"}],
)
```

**我们的实现**（遵循同样的模式）:
- ✅ 使用 `DASHSCOPE_API_KEY` 环境变量
- ✅ 使用 `https://dashscope.aliyuncs.com/compatible-mode/v1` base_url
- ✅ 支持 `qwen3-max`、`qwen3-turbo` 等模型
- ✅ 异步 API 调用支持

## 🎯 使用示例

### 示例1：简单问答

```bash
python -m src.main ask "你好，请介绍你自己" --auto
```

### 示例2：代码生成

```bash
python -m src.main solve "写一个Python函数计算阶乘"
```

### 示例3：交互式聊天

```bash
python -m src.main chat
```

输入你的问题，享受与通义千问的对话！

## 🔄 工作流程

```bash
# 1. 激活环境
conda activate hw_llm_deepsearch

# 2. 编辑 .env（添加 DASHSCOPE_API_KEY）
nano .env

# 3. 验证配置加载
python -m src.main info

# 4. 开始使用
python -m src.main chat
```

## ⚙️ 可用模型对比

| 模型 | 优势 | 成本 | 建议用途 |
|------|------|------|--------|
| **qwen3-max** | 最强大 | ¥0.006/1K | 复杂推理、长文本 |
| **qwen3-turbo** | 平衡 | ¥0.002/1K | **推荐使用** |
| **qwen3-32b-turbo** | 快速 | ¥0.0005/1K | 成本优先 |

**建议**:
- 默认使用 `qwen3-max`（性能最好）
- 或改用 `qwen3-turbo`（便宜70%）

修改方法：
```yaml
# config/config.yaml
dashscope:
  model: qwen3-turbo  # 改这里
```

## ✅ 配置检查清单

使用此清单确保配置正确：

```
[ ] 访问了 https://dashscope.console.aliyun.com/
[ ] 获取了有效的 DASHSCOPE_API_KEY
[ ] 编辑 .env，添加了 DASHSCOPE_API_KEY
[ ] 运行 python -m src.main info
[ ] 看到 "DashScope provider initialized"
[ ] 运行 python -m src.main ask "test" --auto 测试
[ ] 成功得到回复
```

## 🐛 故障排除

### 错误1：密钥无效
```
Error code: 401 - Incorrect API key provided
```
**解决**: 检查 API 密钥是否正确且已启用

### 错误2：No providers configured
```
No LLM providers configured
```
**解决**: 检查 .env 中是否有 DASHSCOPE_API_KEY

### 错误3：Model not found
```
Error: Model not found
```
**解决**: 确认模型名称，查看官方文档最新模型列表

## 📊 性能对比

| 方案 | 响应速度 | 质量 | 成本 | 推荐 |
|------|---------|------|------|------|
| OpenAI GPT-4 | 中 | 最高 | 最高 | ❌ |
| OpenAI GPT-3.5 | 快 | 中 | 中 | ❌ |
| **DashScope qwen3-max** | 中 | 高 | 低 | ✅ |
| **DashScope qwen3-turbo** | 快 | 中 | 最低 | ✅ |

## 🔗 重要链接

| 资源 | URL |
|------|-----|
| DashScope 控制台 | https://dashscope.console.aliyun.com/ |
| 官方 API 文档 | https://help.aliyun.com/zh/dashscope/developer-reference/ |
| 模型列表 | https://help.aliyun.com/zh/dashscope/latest/models/ |
| GitHub 仓库 | https://github.com/aliyun/dashscope-sdk |

## 💡 技巧

### 技巧1：多提供商配置

同时启用多个提供商实现自动故障转移：

```yaml
llm:
  openai:
    enabled: true
  dashscope:
    enabled: true
  deepseek:
    openai_compatible:
      deepseek:
        enabled: true
```

系统会按优先级尝试，如果一个失败会自动切换到下一个。

### 技巧2：模型切换

快速在不同模型间切换（无需改代码）：

```bash
# 编辑 config/config.yaml 中的 model 字段
dashscope:
  model: qwen3-turbo  # 改这里即可

# 重新运行
python -m src.main chat
```

### 技巧3：成本控制

使用便宜的模型进行测试：

```yaml
dashscope:
  model: qwen3-32b-turbo  # 最便宜的选项
  max_tokens: 5000        # 限制输出长度
```

## 📈 后续改进

系统已支持以下特性：

- ✅ OpenAI 格式兼容
- ✅ 自定义 base_url
- ✅ 多提供商支持
- ✅ 自动故障转移
- ✅ 异步 API 调用
- ✅ 环境变量配置

## 🎉 总结

现在您已经可以：

1. ✅ 使用阿里云 DashScope API
2. ✅ 调用通义千问模型（qwen3-max/turbo）
3. ✅ 与多个 LLM 提供商集成
4. ✅ 以更低的成本获得高质量的 AI 服务

**立即开始**：
```bash
nano .env
# 添加你的 DASHSCOPE_API_KEY
python -m src.main chat
```

祝您使用愉快！🚀

---

**更新于**: 2024年10月20日
**基于**: 阿里云 DashScope 官方文档
