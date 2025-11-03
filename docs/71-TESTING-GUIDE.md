# 🧪 测试指南

> **目标**: 完整的测试策略和方法

---

## 📋 测试类型

### 单元测试

```python
import pytest
from src.router import Router

@pytest.mark.asyncio
async def test_router_classify():
    router = Router()
    result = router.classify("计算2+2")
    assert result == TaskType.CODE
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_research_agent():
    result = await agent.research("AI")
    assert "summary" in result
```

### 端到端测试

```python
def test_web_ui():
    # 测试完整流程
    pass
```

---

## 🧬 测试覆盖

- 目标: > 80%
- 运行: `pytest --cov=src`

---

## 🐛 调试技巧

### 日志

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")
```

### 断点

```python
import pdb; pdb.set_trace()
```

---

## 📌 下一步

- [80-TROUBLESHOOTING.md](80-TROUBLESHOOTING.md) - 故障排查

