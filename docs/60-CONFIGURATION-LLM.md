# 🧩 LLM提供商配置

> **目标**: 配置和管理多个LLM提供商

---

## 📋 支持的提供商

### OpenAI

```yaml
llm:
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
    temperature: 0.7
    max_tokens: 2000
```

### DashScope (阿里云)

```yaml
llm:
  dashscope:
    enabled: true
    api_key: ${DASHSCOPE_API_KEY}
    model: qwen3-max
    temperature: 0.7
    max_tokens: 20000
```

### DeepSeek

```yaml
llm:
  openai_compatible:
    deepseek:
      enabled: true
      api_key: ${DEEPSEEK_API_KEY}
      model: deepseek-chat
      base_url: https://api.deepseek.com
```

### Ollama (本地)

```yaml
llm:
  ollama:
    enabled: true
    base_url: http://localhost:11434
    model: llama2
```

---

## ⚙️ 性能优化

### 模型选择

| 模型 | 速度 | 质量 | 成本 |
|------|------|------|------|
| qwen-turbo | ⚡⚡⚡ | ⭐⭐ | ¥ |
| qwen3-max | ⚡⚡ | ⭐⭐⭐ | ¥¥ |
| gpt-4 | ⚡ | ⭐⭐⭐⭐ | ¥¥¥ |

### 温度参数

- 0.0: 确定性强(适合代码)
- 0.7: 平衡(默认)
- 1.0: 创意强(适合创意)

---

## 📌 下一步

- [61-CONFIGURATION-APIS.md](61-CONFIGURATION-APIS.md) - API配置

