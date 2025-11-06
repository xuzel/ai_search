Routing Module
==============

The routing module provides intelligent query classification with pluggable strategies.

Overview
--------

The routing system classifies user queries and routes them to appropriate agents:

* **KeywordRouter**: Fast keyword-based classification
* **LLMRouter**: Accurate LLM-based classification
* **HybridRouter**: Combines keyword + LLM strategies

Architecture
------------

.. code-block:: text

   ┌─────────────────┐
   │   User Query    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │     Router      │
   │  (Pluggable)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ RoutingDecision │
   │  - task_type    │
   │  - confidence   │
   │  - tools_needed │
   └─────────────────┘

Task Types
----------

The system supports the following task types:

* **RESEARCH**: Web search and information gathering
* **CODE**: Code generation and execution
* **CHAT**: Conversational AI
* **RAG**: Document question answering
* **DOMAIN_WEATHER**: Weather queries
* **DOMAIN_FINANCE**: Stock/finance queries
* **DOMAIN_ROUTING**: Navigation/routing queries

Base Classes
------------

.. automodule:: src.routing.base
   :members:
   :undoc-members:
   :show-inheritance:

Task Types
----------

.. automodule:: src.routing.task_types
   :members:
   :undoc-members:
   :show-inheritance:

Router Implementations
----------------------

Keyword Router
~~~~~~~~~~~~~~

.. automodule:: src.routing.keyword_router
   :members:
   :undoc-members:
   :show-inheritance:

LLM Router
~~~~~~~~~~

.. automodule:: src.routing.llm_router
   :members:
   :undoc-members:
   :show-inheritance:

Hybrid Router
~~~~~~~~~~~~~

.. automodule:: src.routing.hybrid_router
   :members:
   :undoc-members:
   :show-inheritance:

Router Factory
--------------

.. automodule:: src.routing.factory
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from src.routing import create_router, TaskType
   from src.utils import get_config
   from src.llm import LLMManager

   # Load configuration
   config = get_config()
   llm_manager = LLMManager(config)

   # Create router
   router = create_router(config, llm_manager, router_type='hybrid')

   # Route query
   decision = await router.route("What's the weather in Beijing?")
   print(f"Task: {decision.primary_task_type}")
   print(f"Confidence: {decision.task_confidence:.2f}")

Custom Router
~~~~~~~~~~~~~

.. code-block:: python

   from src.routing import BaseRouter, RoutingDecision, TaskType

   class CustomRouter(BaseRouter):
       async def route(self, query: str, context=None) -> RoutingDecision:
           # Custom routing logic
           return RoutingDecision(
               query=query,
               primary_task_type=TaskType.RESEARCH,
               task_confidence=0.95,
               reasoning="Custom routing logic"
           )

   # Use custom router
   router = CustomRouter(config)
   decision = await router.route("test query")
