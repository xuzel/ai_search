# 🔑 外部API密钥配置

> **目标**: 配置所有外部API密钥

---

## 📋 配置清单

### 必需API

```bash
# 搜索API
SERPAPI_API_KEY=xxx

# LLM API (至少一个)
DASHSCOPE_API_KEY=xxx
```

### 可选API

```bash
# 天气
OPENWEATHERMAP_API_KEY=xxx

# 金融
ALPHA_VANTAGE_API_KEY=xxx

# 路由
OPENROUTESERVICE_API_KEY=xxx

# Vision
GOOGLE_API_KEY=xxx
```

---

## 🔐 安全最佳实践

1. 使用环境变量
2. 不提交.env到Git
3. 定期轮换密钥
4. 使用密钥管理服务

---

## 🧪 验证配置

```bash
python -m src.main info
```

---

## 📌 下一步

- [70-DEVELOPMENT-GUIDE.md](70-DEVELOPMENT-GUIDE.md) - 开发指南

