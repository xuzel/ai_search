Usage Guide
===========

This guide covers common usage patterns for the AI Search Engine.

Web UI
------

The web UI is the recommended way to interact with the system.

Starting the Server
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Basic start
   python -m src.web.app

   # Custom host/port
   WEB_HOST=127.0.0.1 WEB_PORT=8080 python -m src.web.app

   # Using uvicorn directly (for advanced options)
   uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000 --workers 4

Accessing the UI
~~~~~~~~~~~~~~~~

Open your browser and navigate to:

* **Homepage**: http://localhost:8000
* **Health Check**: http://localhost:8000/health
* **History**: http://localhost:8000/history

Features
~~~~~~~~

* **Unified Search**: Single input box with intelligent routing
* **Research Mode**: Web search with AI synthesis
* **Code Mode**: Generate and execute Python code
* **Chat Mode**: Conversational AI
* **RAG Mode**: Document Q&A
* **Domain Tools**: Weather, finance, routing queries
* **Multimodal**: OCR and vision analysis
* **History**: Search and manage conversation history

CLI Usage
---------

Search (Research Mode)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Basic search
   python -m src.main search "What is quantum computing?"

   # With verbose output
   python -m src.main search "machine learning" --verbose

Solve (Code Mode)
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Math problem
   python -m src.main solve "Calculate factorial of 10"

   # Unit conversion
   python -m src.main solve "Convert 100 miles to kilometers"

   # Statistical calculation
   python -m src.main solve "Find mean and std dev of [1,2,3,4,5]"

Ask (Auto-routing)
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Auto-detect query type
   python -m src.main ask "What's the weather in Beijing?" --auto

   # The system will route to appropriate agent:
   # - Weather query -> WeatherTool
   # - Math question -> CodeAgent
   # - General question -> ResearchAgent

Chat (Interactive Mode)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start interactive chat
   python -m src.main chat

   # In chat mode
   You: Hello!
   Assistant: Hi! How can I help you today?

   You: /exit  # Exit chat

System Info
~~~~~~~~~~~

.. code-block:: bash

   # Show system configuration and status
   python -m src.main info

Python API
----------

As a Library
~~~~~~~~~~~~

.. code-block:: python

   from src.agents import ResearchAgent, CodeAgent
   from src.llm import LLMManager
   from src.tools import SearchTool, ScraperTool, CodeExecutor
   from src.utils import get_config

   # Initialize
   config = get_config()
   llm_manager = LLMManager(config)

   # Research
   search_tool = SearchTool(config.search.serpapi_key)
   scraper_tool = ScraperTool()
   research_agent = ResearchAgent(
       llm_manager=llm_manager,
       search_tool=search_tool,
       scraper_tool=scraper_tool,
       config=config
   )

   result = await research_agent.research("What is AI?")
   print(result['summary'])

   # Code Execution
   code_executor = CodeExecutor(timeout=30)
   code_agent = CodeAgent(
       llm_manager=llm_manager,
       code_executor=code_executor,
       config=config
   )

   result = await code_agent.solve("Calculate 2^10")
   print(result['output'])

Routing System
~~~~~~~~~~~~~~

.. code-block:: python

   from src.routing import create_router

   # Create router
   router = create_router(config, llm_manager, router_type='hybrid')

   # Route query
   decision = await router.route("What's the stock price of AAPL?")

   print(f"Task Type: {decision.primary_task_type}")
   print(f"Confidence: {decision.task_confidence:.2f}")
   print(f"Tools Needed: {decision.tools_needed}")

RAG System
~~~~~~~~~~

.. code-block:: python

   from src.agents import RAGAgent
   from src.tools import VectorStore, DocumentProcessor

   # Initialize RAG
   vector_store = VectorStore()
   doc_processor = DocumentProcessor()

   rag_agent = RAGAgent(
       llm_manager=llm_manager,
       vector_store=vector_store,
       doc_processor=doc_processor,
       config=config
   )

   # Ingest documents
   await rag_agent.ingest_document("path/to/document.pdf")

   # Query
   result = await rag_agent.query("What is the main topic?")
   print(result['answer'])
   print(result['sources'])

Workflow System
~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import WorkflowEngine, ExecutionMode

   # Create workflow
   engine = WorkflowEngine()
   workflow = engine.create_workflow("my_workflow", mode=ExecutionMode.DAG)

   # Add tasks
   async def task_a():
       return {"value": 10}

   async def task_b(a_result):
       return {"value": a_result["value"] * 2}

   workflow.add_task("A", func=task_a)
   workflow.add_task("B", func=task_b, dependencies={"A"})

   # Execute
   result = await engine.execute(workflow)
   print(result.results)

Common Scenarios
----------------

Scenario 1: Research with Web Search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Goal**: Find recent information about a topic

**Web UI**:

1. Enter query in search box
2. System auto-detects research mode
3. View synthesized summary with sources

**CLI**:

.. code-block:: bash

   python -m src.main search "Latest developments in AI 2024"

**Python**:

.. code-block:: python

   result = await research_agent.research(
       "Latest developments in AI 2024",
       show_progress=True
   )

   print("Summary:", result['summary'])
   print("Sources:", result['sources'])

Scenario 2: Mathematical Calculations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Goal**: Solve math or perform calculations

**Web UI**:

1. Enter math query
2. System generates Python code
3. View code and results

**CLI**:

.. code-block:: bash

   python -m src.main solve "Find prime numbers between 1 and 100"

**Python**:

.. code-block:: python

   result = await code_agent.solve(
       "Find prime numbers between 1 and 100"
   )

   print("Code:", result['code'])
   print("Output:", result['output'])

Scenario 3: Document Question Answering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Goal**: Ask questions about uploaded documents

**Web UI**:

1. Navigate to RAG section
2. Upload PDF/DOCX files
3. Enter question
4. View answer with source references

**Python**:

.. code-block:: python

   # Ingest
   await rag_agent.ingest_document("research_paper.pdf")

   # Query
   result = await rag_agent.query(
       "What methodology was used in the study?"
   )

   print("Answer:", result['answer'])
   for source in result['sources']:
       print(f"  - {source['text'][:100]}...")

Scenario 4: Weather Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Goal**: Get current weather

**Web UI**:

1. Enter "Weather in [city]"
2. View temperature, humidity, conditions

**CLI**:

.. code-block:: bash

   python -m src.main ask "What's the weather in Tokyo?" --auto

**Python**:

.. code-block:: python

   from src.tools import WeatherTool

   weather = WeatherTool(api_key=config.domain_tools.weather.api_key)
   result = await weather.get_weather("Tokyo")

   print(f"Temperature: {result['temperature']}°C")
   print(f"Conditions: {result['conditions']}")

Scenario 5: Stock Price Lookup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Goal**: Get stock/finance information

**Web UI**:

1. Enter "AAPL stock price"
2. View current price, change, volume

**Python**:

.. code-block:: python

   from src.tools import FinanceTool

   finance = FinanceTool(
       alpha_vantage_key=config.domain_tools.finance.alpha_vantage_key
   )

   result = await finance.get_stock_price("AAPL")

   print(f"Price: ${result['price']}")
   print(f"Change: {result['change_percent']}%")

Scenario 6: Multi-step Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Goal**: Execute complex multi-step task

**Python**:

.. code-block:: python

   from src.workflow import WorkflowEngine, ExecutionMode

   engine = WorkflowEngine()
   workflow = engine.create_workflow("research_pipeline", mode=ExecutionMode.DAG)

   # Step 1: Research
   async def research_topic():
       return await research_agent.research("Quantum computing")

   # Step 2: Summarize
   async def summarize(research_result):
       return research_result['summary'][:200]

   # Step 3: Save
   async def save_summary(summary):
       with open("summary.txt", "w") as f:
           f.write(summary)
       return {"saved": True}

   workflow.add_task("research", func=research_topic)
   workflow.add_task("summarize", func=summarize, dependencies={"research"})
   workflow.add_task("save", func=save_summary, dependencies={"summarize"})

   result = await engine.execute(workflow)

Advanced Usage
--------------

Custom Routers
~~~~~~~~~~~~~~

.. code-block:: python

   from src.routing import BaseRouter, RoutingDecision, TaskType

   class MyRouter(BaseRouter):
       async def route(self, query: str, context=None) -> RoutingDecision:
           # Custom routing logic
           if "urgent" in query.lower():
               return RoutingDecision(
                   query=query,
                   primary_task_type=TaskType.RESEARCH,
                   task_confidence=1.0,
                   reasoning="Urgent query detected"
               )
           # Fallback to keyword routing
           return await super().route(query, context)

Custom Tools
~~~~~~~~~~~~

.. code-block:: python

   class MyCustomTool:
       async def execute(self, query: str) -> dict:
           # Custom tool logic
           return {"result": "custom result"}

   # Use in agent
   custom_tool = MyCustomTool()
   result = await custom_tool.execute("test query")

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   try:
       result = await research_agent.research("query")
   except Exception as e:
       logger.error(f"Research failed: {e}")
       # Fallback logic

Tips & Best Practices
---------------------

1. **Use Auto-routing**: Let the system choose the best mode
2. **Check Conversation History**: Review past queries for context
3. **Upload Multiple Documents**: RAG works better with more context
4. **Use Specific Queries**: More specific queries get better results
5. **Monitor Performance**: Use ``/health`` endpoint for status checks
6. **Configure Logging**: Enable DEBUG for troubleshooting
7. **Use Workflow for Complex Tasks**: Break down multi-step tasks
8. **Cache Results**: Enable caching for frequently used queries

Next Steps
----------

* See :doc:`configuration` for configuration options
* See :doc:`deployment` for production deployment
* See :doc:`/dev/testing` for testing guide
