# 重构文件清单

## 📁 新创建的文件 (20个)

### 路由系统 (8个文件)
```
src/routing/
├── __init__.py                 # 新建 - 统一路由接口
├── task_types.py               # 新建 - TaskType枚举定义
├── base.py                     # 新建 - BaseRouter抽象类
├── keyword_router.py           # 新建 - 关键字路由器
├── llm_router.py               # 新建 - LLM路由器 (合并EN+ZH)
├── hybrid_router.py            # 新建 - 混合路由策略
├── factory.py                  # 新建 - 路由器工厂
└── MIGRATION_GUIDE.md          # 新建 - 迁移指南文档
```

### 依赖注入系统 (3个文件)
```
src/web/dependencies/
├── __init__.py                 # 新建 - 依赖导出
├── core.py                     # 新建 - 核心依赖 (LLM, Router, Agents)
└── tools.py                    # 新建 - 工具依赖 (Search, Code等)
```

### 重构的Web路由器 (2个文件)
```
src/web/routers/
├── query_refactored.py         # 新建 - 重构后的查询路由
└── REFACTORING_COMPARISON.md   # 新建 - 重构对比文档
```

### 重构的CLI (1个文件)
```
src/
└── main_refactored.py          # 新建 - 重构后的CLI
```

### 测试文件 (1个文件)
```
tests/
└── test_routing.py             # 新建 - 路由系统单元测试
```

### 文档文件 (5个文件)
```
项目根目录/
├── REFACTORING_PROGRESS.md     # 新建 - 重构进度报告
├── REFACTORING_COMPLETE.md     # 新建 - 重构完成报告
├── REFACTORING_FILES.md        # 新建 - 本文件清单
├── IMPLEMENTATION_ROADMAP.md   # 已存在 - 实现路线图
└── src/routing/MIGRATION_GUIDE.md  # 新建 - 路由迁移指南
```

---

## 📝 已修改的文件 (Week 1, 已完成)

### 安全相关 (3个文件)
```
src/tools/
├── code_validator.py           # Week 1 新建 - AST验证器
├── sandbox_executor.py         # Week 1 新建 - Docker沙箱
└── code_executor.py            # Week 1 修改 - 集成多层安全
```

### 配置文件 (1个文件)
```
.gitignore                      # Week 1 修改 - 添加 .env
```

---

## 🔄 建议迁移的文件 (待执行)

### Web路由器 (1个文件)
```bash
# 迁移步骤:
mv src/web/routers/query.py src/web/routers/query_old.py
mv src/web/routers/query_refactored.py src/web/routers/query.py
```

### CLI (1个文件)
```bash
# 迁移步骤:
mv src/main.py src/main_old.py
mv src/main_refactored.py src/main.py
```

### App启动文件 (1个文件)
```bash
# 需要修改 src/web/app.py
# 添加依赖清理到 lifespan 函数
```

---

## 📦 保留的旧文件 (用于回滚)

### 旧路由系统 (3个文件) - 保持不变
```
src/
├── router.py                   # 保留 - 旧关键字路由器
├── llm_router.py               # 保留 - 旧LLM路由器
└── cn_llm_router.py            # 保留 - 旧中文LLM路由器
```

**这些文件保留的原因**:
- 向后兼容性
- 快速回滚
- 渐进式迁移

**后续处理**:
- 部署成功后可标记为 `DEPRECATED`
- 3-6个月后可以删除

---

## 📊 文件统计

### 新增文件总数: 20个
```
路由系统:      8个文件  (~1000行)
依赖注入:      3个文件  (~400行)
重构路由器:    2个文件  (~450行)
重构CLI:       1个文件  (~350行)
测试:          1个文件  (~300行)
文档:          5个文件  (~800行)
-----------------------------------------
总计:         20个文件  (~3300行)
```

### 修改文件: 4个
```
安全相关:      3个文件 (Week 1)
配置文件:      1个文件 (Week 1)
```

### 保留旧文件: 3个
```
旧路由系统:    3个文件 (向后兼容)
```

---

## 🗂️ 完整目录结构

```
ai_search/
├── src/
│   ├── routing/                     # ✅ 新增 - 统一路由系统
│   │   ├── __init__.py
│   │   ├── task_types.py
│   │   ├── base.py
│   │   ├── keyword_router.py
│   │   ├── llm_router.py
│   │   ├── hybrid_router.py
│   │   ├── factory.py
│   │   └── MIGRATION_GUIDE.md
│   │
│   ├── web/
│   │   ├── dependencies/            # ✅ 新增 - 依赖注入系统
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   └── tools.py
│   │   │
│   │   ├── routers/
│   │   │   ├── query.py             # ⏳ 待替换
│   │   │   ├── query_refactored.py  # ✅ 新建 (替换上面的文件)
│   │   │   ├── query_old.py         # ⏳ 备份 (迁移后创建)
│   │   │   └── REFACTORING_COMPARISON.md  # ✅ 新建
│   │   │
│   │   └── app.py                   # ⏳ 需要修改 (添加cleanup)
│   │
│   ├── tools/
│   │   ├── code_validator.py        # ✅ Week 1 新建
│   │   ├── sandbox_executor.py      # ✅ Week 1 新建
│   │   └── code_executor.py         # ✅ Week 1 修改
│   │
│   ├── main.py                      # ⏳ 待替换
│   ├── main_refactored.py           # ✅ 新建 (替换上面的文件)
│   ├── main_old.py                  # ⏳ 备份 (迁移后创建)
│   │
│   ├── router.py                    # 🔒 保留 (旧路由器)
│   ├── llm_router.py                # 🔒 保留 (旧路由器)
│   └── cn_llm_router.py             # 🔒 保留 (旧路由器)
│
├── tests/
│   └── test_routing.py              # ✅ 新建 - 路由系统测试
│
├── .gitignore                       # ✅ Week 1 修改
│
└── 文档/
    ├── REFACTORING_PROGRESS.md      # ✅ 新建
    ├── REFACTORING_COMPLETE.md      # ✅ 新建
    ├── REFACTORING_FILES.md         # ✅ 新建 (本文档)
    ├── IMPLEMENTATION_ROADMAP.md    # 已存在
    ├── ROUTING_*.md                 # 已存在 (分析文档)
    └── CLAUDE.md                    # 已存在 (项目说明)
```

**图例**:
- ✅ 已完成/已新建
- ⏳ 待执行
- 🔒 保留不变 (向后兼容)

---

## 🚀 迁移检查清单

### 阶段1: 验证新文件 (已完成 ✅)
- [x] 路由系统文件创建完成 (8个文件)
- [x] 依赖注入文件创建完成 (3个文件)
- [x] 重构文件创建完成 (2个文件)
- [x] 测试文件创建完成 (1个文件)
- [x] 文档文件创建完成 (5个文件)

### 阶段2: 迁移执行 (待执行 ⏳)
- [ ] 备份 `src/web/routers/query.py` → `query_old.py`
- [ ] 重命名 `query_refactored.py` → `query.py`
- [ ] 备份 `src/main.py` → `main_old.py`
- [ ] 重命名 `main_refactored.py` → `main.py`
- [ ] 修改 `src/web/app.py` 添加 cleanup
- [ ] 运行测试验证

### 阶段3: 测试验证 (待执行 ⏳)
- [ ] 运行单元测试: `pytest tests/test_routing.py`
- [ ] 运行集成测试: `pytest tests/test_web_ui.py`
- [ ] 启动Web服务: `python -m src.web.app`
- [ ] 手动测试所有功能
- [ ] 检查日志无错误

### 阶段4: 部署 (待执行 ⏳)
- [ ] 提交到Git: `git add . && git commit -m "Refactor: ..."` 
- [ ] 推送到远程: `git push origin refactoring`
- [ ] 创建Pull Request
- [ ] Code Review
- [ ] 合并到主分支

### 阶段5: 清理 (可选)
- [ ] 标记旧文件为DEPRECATED
- [ ] 3-6个月后删除旧路由器
- [ ] 更新CLAUDE.md文档

---

## 📌 重要提示

### 迁移前必读
1. **先备份**: 所有修改前都先备份原文件
2. **测试验证**: 每个阶段都要运行测试
3. **回滚准备**: 确保可以5分钟内回滚
4. **监控日志**: 迁移后密切监控错误日志
5. **分阶段部署**: 建议先测试环境 → 金丝雀 → 全量

### 回滚方案
```bash
# 如果出现问题，快速回滚:
mv src/web/routers/query.py src/web/routers/query_new.py
mv src/web/routers/query_old.py src/web/routers/query.py
mv src/main.py src/main_new.py
mv src/main_old.py src/main.py
# 重启服务
```

---

## 📞 联系支持

如遇到迁移问题:
1. 查看 `REFACTORING_COMPARISON.md` - 详细对比
2. 查看 `MIGRATION_GUIDE.md` - 迁移步骤
3. 查看 `test_routing.py` - 测试示例
4. 查看日志文件 - 错误信息

**预计迁移时间**: 30分钟
**回滚时间**: 5分钟
**风险等级**: 低 (有完整测试和回滚方案)

---

**创建时间**: 2024-11-04
**文件数量**: 20个新建 + 4个修改
**代码行数**: ~3300行新代码
