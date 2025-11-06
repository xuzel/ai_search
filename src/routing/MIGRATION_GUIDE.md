# Routing System Migration Guide

## Overview

The routing system has been refactored from 3 separate routers (1185 lines) to a unified system (400 lines).

### Old System (Deprecated)
- `src/router.py` (428 lines) - Keyword router
- `src/llm_router.py` (384 lines) - LLM router  
- `src/cn_llm_router.py` (373 lines) - Chinese LLM router

### New System (Recommended)
- `src/routing/` - Unified routing package
  - `keyword_router.py` - Fast keyword-based routing
  - `llm_router.py` - Accurate LLM-based routing (supports EN/ZH)
  - `hybrid_router.py` - Combines both strategies
  - `factory.py` - Router creation

## Migration Steps

### Step 1: Update Imports

**Old:**
```python
from src.router import Router, TaskType
from src.cn_llm_router import ChineseIntelligentRouter

router = Router()
cn_router = ChineseIntelligentRouter(llm_manager)
```

**New:**
```python
from src.routing import create_router, TaskType

# Create unified router (supports EN and ZH)
router = create_router(config, llm_manager, router_type='hybrid')
```

### Step 2: Update Usage

**Old:**
```python
# Keyword routing
task_type = Router.classify(query)
confidence = Router.get_confidence(query, task_type)

# LLM routing
decision = await cn_router.route_query(query, context={'language': 'zh'})
```

**New:**
```python
# Unified routing
decision = await router.route(query, context={'language': 'zh'})

# Access results
task_type = decision.primary_task_type
confidence = decision.task_confidence
reasoning = decision.reasoning
tools = decision.tools_needed
```

### Step 3: RoutingDecision Structure

**New structure has more information:**
```python
@dataclass
class RoutingDecision:
    query: str
    primary_task_type: TaskType
    task_confidence: float
    reasoning: str
    tools_needed: List[ToolRequirement]
    multi_intent: bool
    alternative_task_types: List[TaskType]
    metadata: Dict[str, Any]
```

### Step 4: TaskType Enum

**Location changed:**
```python
# Old
from src.router import TaskType

# New  
from src.routing import TaskType
```

**Values remain the same:**
- `RESEARCH`, `CODE`, `CHAT`
- `RAG`
- `DOMAIN_WEATHER`, `DOMAIN_FINANCE`, `DOMAIN_ROUTING`

## Backward Compatibility

The old routers are still available but deprecated:
```python
from src.router import Router  # Still works, deprecated
from src.llm_router import IntelligentRouter  # Still works, deprecated  
from src.cn_llm_router import ChineseIntelligentRouter  # Still works, deprecated
```

A deprecation warning will be shown when using old routers.

## Benefits of New System

1. **Unified Interface**: One router for all strategies
2. **Pluggable**: Easy to switch between keyword/LLM/hybrid
3. **Multilingual**: Single router supports EN/ZH (no separate Chinese router)
4. **Testable**: Clear interfaces and dependency injection
5. **Maintainable**: 66% code reduction (1185 → 400 lines)

## Configuration

Add to `config.yaml`:
```yaml
routing:
  type: hybrid  # Options: keyword, llm, hybrid
  confidence_threshold: 0.7  # For hybrid mode
```

## Examples

### Example 1: CLI Usage
```python
from src.routing import create_router
from src.llm import LLMManager
from src.utils import get_config

config = get_config()
llm_manager = LLMManager(config)
router = create_router(config, llm_manager)

# Route query
decision = await router.route("北京今天天气怎么样？")
print(f"Task: {decision.primary_task_type}")
print(f"Confidence: {decision.task_confidence:.2f}")
print(f"Reasoning: {decision.reasoning}")
```

### Example 2: Web UI Usage
```python
from fastapi import Depends
from src.routing import create_router
from src.web.dependencies import get_router

@router.post("/query")
async def unified_query(
    query: str = Form(...),
    router = Depends(get_router)  # Dependency injection
):
    decision = await router.route(query)
    # Handle decision...
```

## Timeline

- Week 2, Day 1-3: Routing system unified ✅
- Week 2, Day 4-5: Update all usage to new system
- Week 3: Remove deprecated routers

## Support

For issues or questions, check:
- `src/routing/__init__.py` - Package documentation
- `tests/test_routing.py` - Usage examples
