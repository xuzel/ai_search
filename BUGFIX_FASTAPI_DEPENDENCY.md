# FastAPI Dependency Injection Bug Fix

## 问题描述

启动Web UI时出现错误：
```
fastapi.exceptions.FastAPIError: Invalid args for response field!
Hint: check that <class 'src.llm.manager.LLMManager'> is a valid Pydantic field type.
```

## 根本原因

**错误代码模式**（`src/web/dependencies/core.py`）：
```python
# ❌ 错误：FastAPI无法解析带默认参数的依赖链
async def get_router(
    llm_manager: LLMManager = None  # FastAPI会尝试序列化LLMManager类型
) -> BaseRouter:
    if llm_manager is None:
        llm_manager = await get_llm_manager()
    ...
```

### 问题分析
1. FastAPI的依赖注入系统会检查**所有参数类型**
2. `LLMManager`不是Pydantic模型，无法被FastAPI序列化为响应字段
3. 即使有默认值`= None`，FastAPI仍会尝试验证类型注解

## 解决方案

### 修复后代码（已应用）

```python
# ✅ 正确：依赖内部直接调用，无参数注入
async def get_router() -> BaseRouter:
    """Get router instance - no parameter injection"""
    global _router

    if _router is None:
        # 内部直接调用依赖，不通过参数注入
        llm_manager = await get_llm_manager()
        config = get_config()

        _router = create_router(
            config=config,
            llm_manager=llm_manager,
            router_type='hybrid'
        )

    return _router
```

### FastAPI依赖注入的两种正确模式

#### 模式1：无参数依赖（本项目使用）
```python
# 依赖函数内部调用其他依赖
async def get_service_a() -> ServiceA:
    dependency_b = await get_service_b()  # 内部调用
    return ServiceA(dependency_b)

@app.post("/endpoint")
async def endpoint(service: ServiceA = Depends(get_service_a)):
    ...
```

#### 模式2：嵌套Depends（不适合本项目）
```python
# 使用Depends()显式声明依赖链
async def get_service_a(
    dependency_b: ServiceB = Depends(get_service_b)  # 注意：必须用Depends()
) -> ServiceA:
    return ServiceA(dependency_b)
```

**为什么本项目不用模式2？**
- 依赖层级深（router → llm_manager → config）
- 单例模式已通过global变量实现
- 避免FastAPI重复调用依赖函数

## 修改文件清单

### ✅ 已修复
- `src/web/dependencies/core.py` - 移除所有依赖函数的参数

### ⚠️  需要检查的其他文件
运行以下命令检查是否有类似问题：
```bash
grep -rn "= Depends" src/web/dependencies/
```

## 验证方法

### 1. 导入测试
```bash
python -c "from src.web.routers import query; print('✅ Import OK')"
```

### 2. 启动测试
```bash
# 方法1：直接启动（会持续运行）
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000

# 方法2：快速验证（10秒后超时）
timeout 10 uvicorn src.web.app:app --host 127.0.0.1 --port 8888 || echo "Expected timeout"
```

### 3. Health检查
```bash
curl http://localhost:8000/health
# 期望输出: {"status":"ok","message":"AI Search Engine is running"}
```

## 技术要点

### FastAPI类型验证机制
1. **路由函数参数检查**：所有参数类型必须是：
   - Pydantic模型（自动序列化）
   - 基础类型（str, int, bool等）
   - `Depends()`返回的任意类型（但不检查类型本身）

2. **Depends()的魔法**：
   ```python
   # FastAPI不验证Depends()返回值类型
   service: ComplexClass = Depends(get_service)  # ✅ OK

   # 但会验证默认参数类型
   def func(service: ComplexClass = None):  # ❌ 会尝试序列化ComplexClass
   ```

### 单例模式最佳实践
```python
# 全局缓存 + 无参数依赖 = 高性能单例
_singleton = None

async def get_singleton() -> Service:
    global _singleton
    if _singleton is None:
        _singleton = Service()
    return _singleton  # 只创建一次，后续直接返回
```

## 其他警告处理（可选）

### pyowm警告
```python
# 在requirements.txt固定版本
pyowm==3.3.0  # 改为
pyowm>=3.3.0,<4.0.0  # 并迁移至新API
```

### PaddlePaddle警告
```bash
# macOS安装ccache（可选，加速编译）
brew install ccache
```

## 总结

**修复前问题**：依赖函数有参数 → FastAPI尝试序列化类型 → 非Pydantic模型报错

**修复后方案**：依赖函数无参数 → 内部直接调用 → FastAPI只检查返回值 → ✅ 成功

**关键原则**：
- FastAPI的Depends()只应出现在路由函数参数中
- 依赖函数本身应该是"纯"的（无参数或仅基础类型参数）
- 复杂对象通过内部调用传递，不通过参数注入
