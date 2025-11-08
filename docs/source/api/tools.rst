Tools Module
============

The tools module provides various utilities for search, scraping, code execution, RAG, and domain-specific features.

Overview
--------

Available tools:

* **SearchTool**: Web search via SerpAPI
* **ScraperTool**: Async web scraping
* **CodeExecutor**: Safe Python code execution
* **VectorStore**: ChromaDB-based vector storage
* **DocumentProcessor**: Text extraction from documents
* **SmartChunker**: Semantic text chunking
* **Reranker**: Retrieval result reranking
* **CredibilityScorer**: Source credibility scoring
* **WeatherTool**: Weather data
* **FinanceTool**: Stock/finance data
* **RoutingTool**: Navigation/routing
* **OCRTool**: Text extraction from images
* **VisionTool**: Image analysis

Search Tools
------------

SearchTool
~~~~~~~~~~

.. automodule:: src.tools.search
   :members:
   :undoc-members:
   :show-inheritance:

ScraperTool
~~~~~~~~~~~

.. automodule:: src.tools.scraper
   :members:
   :undoc-members:
   :show-inheritance:

Code Execution
--------------

CodeExecutor
~~~~~~~~~~~~

.. automodule:: src.tools.code_executor
   :members:
   :undoc-members:
   :show-inheritance:

Code Validator
~~~~~~~~~~~~~~

.. automodule:: src.tools.code_validator
   :members:
   :undoc-members:
   :show-inheritance:

Sandbox Executor
~~~~~~~~~~~~~~~~

.. automodule:: src.tools.sandbox_executor
   :members:
   :undoc-members:
   :show-inheritance:

RAG Tools
---------

VectorStore
~~~~~~~~~~~

.. automodule:: src.tools.vector_store
   :members:
   :undoc-members:
   :show-inheritance:

DocumentProcessor
~~~~~~~~~~~~~~~~~

.. automodule:: src.tools.document_processor
   :members:
   :undoc-members:
   :show-inheritance:

SmartChunker
~~~~~~~~~~~~

.. automodule:: src.tools.chunking
   :members:
   :undoc-members:
   :show-inheritance:

Reranker
~~~~~~~~

.. automodule:: src.tools.reranker
   :members:
   :undoc-members:
   :show-inheritance:

CredibilityScorer
~~~~~~~~~~~~~~~~~

.. automodule:: src.tools.credibility_scorer
   :members:
   :undoc-members:
   :show-inheritance:

Domain-Specific Tools
---------------------

WeatherTool
~~~~~~~~~~~

.. automodule:: src.tools.weather_tool
   :members:
   :undoc-members:
   :show-inheritance:

FinanceTool
~~~~~~~~~~~

.. automodule:: src.tools.finance_tool
   :members:
   :undoc-members:
   :show-inheritance:

RoutingTool
~~~~~~~~~~~

.. automodule:: src.tools.routing_tool
   :members:
   :undoc-members:
   :show-inheritance:

Multimodal Tools
----------------

OCRTool
~~~~~~~

.. automodule:: src.tools.ocr_tool
   :members:
   :undoc-members:
   :show-inheritance:

VisionTool
~~~~~~~~~~

.. automodule:: src.tools.vision_tool
   :members:
   :undoc-members:
   :show-inheritance:

Advanced PDF Processing
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: src.tools.advanced_pdf_processor
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Vector Store
~~~~~~~~~~~~

.. code-block:: python

   from src.tools import VectorStore

   # Initialize vector store
   vector_store = VectorStore(
       persist_directory="./data/vector_store",
       collection_name="my_docs",
       cache_size=1000,
       cache_ttl=3600
   )

   # Add documents
   texts = ["Document 1 content", "Document 2 content"]
   ids = vector_store.add_documents(texts=texts)

   # Search
   results = vector_store.similarity_search("query", k=5)

Code Executor
~~~~~~~~~~~~~

.. code-block:: python

   from src.tools import CodeExecutor

   # Initialize executor
   executor = CodeExecutor(
       timeout=30,
       enable_docker=False,
       enable_validation=True
   )

   # Execute code
   code = "print(2 + 2)"
   result = await executor.execute(code)
   print(result['output'])

Weather Tool
~~~~~~~~~~~~

.. code-block:: python

   from src.tools import WeatherTool

   # Initialize tool
   weather = WeatherTool(api_key="your_key")

   # Get weather
   result = await weather.get_weather("Beijing")
   print(result['temperature'])

Finance Tool
~~~~~~~~~~~~

.. code-block:: python

   from src.tools import FinanceTool

   # Initialize tool
   finance = FinanceTool(
       alpha_vantage_key="your_key",
       enable_yfinance_fallback=True
   )

   # Get stock price
   result = await finance.get_stock_price("AAPL")
   print(result['price'])
