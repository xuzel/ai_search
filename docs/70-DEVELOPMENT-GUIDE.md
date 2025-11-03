# 👨‍💻 开发者指南

> **目标**: 为开发者提供完整的开发流程指导

---

## 🚀 快速开发流程

### 1. 设置开发环境

```bash
git clone <repo>
cd ai_search
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .  # 可编辑安装
```

### 2. 创建功能分支

```bash
git checkout -b feature/new-feature
```

### 3. 实现功能

- 遵循项目代码风格
- 编写单元测试
- 更新文档

### 4. 提交并提PR

```bash
git commit -m "feat: 描述新功能"
git push origin feature/new-feature
```

---

## 📝 代码风格

- Python: PEP8
- 缩进: 4空格
- 类型提示: 推荐使用

```python
async def execute(self, input_data: dict) -> dict:
    """函数文档."""
    pass
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_router.py

# 生成覆盖率报告
pytest --cov=src
```

---

## 🔄 新增Agent

1. 创建Agent类
2. 继承BaseAgent
3. 实现execute方法
4. 注册到Router

---

## 📌 下一步

- [71-TESTING-GUIDE.md](71-TESTING-GUIDE.md) - 测试指南

