# 🚨 故障排查手册

> **目标**: 常见问题的诊断和解决方案

---

## 🔍 诊断工具

### 系统检查

```bash
python -m src.main info
```

### 日志查看

```bash
tail -f logs/app.log
```

---

## 🐛 常见问题

### 问题1: LLM提供商不可用

**症状**: "No LLM providers available"

**诊断**:
```bash
python -c "from src.llm import LLMManager; print(LLMManager().providers)"
```

**解决方案**:
1. 检查.env文件
2. 验证API密钥
3. 检查enabled标志

### 问题2: 搜索API错误

**症状**: "Search API not configured"

**解决方案**:
```bash
export SERPAPI_API_KEY=your_key
```

### 问题3: 代码执行超时

**症状**: "Code execution timeout"

**解决方案**:
```yaml
code_execution:
  timeout: 60  # 增加超时时间
```

---

## 📊 性能诊断

### 慢查询排查

1. 启用详细日志
2. 检查网络延迟
3. 分析瓶颈位置

---

## 📌 下一步

- [81-FAQ.md](81-FAQ.md) - 常见问题解答

