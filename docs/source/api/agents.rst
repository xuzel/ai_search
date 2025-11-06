Agents Module
=============

The agents module provides specialized AI agents for different task types.

Overview
--------

Agents are responsible for executing specific types of tasks:

* **ResearchAgent**: Web research and information synthesis
* **CodeAgent**: Code generation and execution
* **ChatAgent**: Conversational AI
* **RAGAgent**: Document-based question answering

Research Agent
--------------

Conducts multi-step web research with search planning, content scraping, and LLM-based synthesis.

.. automodule:: src.agents.research_agent
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

   from src.agents import ResearchAgent
   from src.llm import LLMManager
   from src.tools import SearchTool, ScraperTool
   from src.utils import get_config

   config = get_config()
   llm_manager = LLMManager(config)
   search_tool = SearchTool(config.search.serpapi_key)
   scraper_tool = ScraperTool()

   agent = ResearchAgent(
       llm_manager=llm_manager,
       search_tool=search_tool,
       scraper_tool=scraper_tool,
       config=config
   )

   result = await agent.research("What is quantum computing?")
   print(result['summary'])

Code Agent
----------

Generates and executes Python code in a sandboxed environment.

.. automodule:: src.agents.code_agent
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

   from src.agents import CodeAgent
   from src.llm import LLMManager
   from src.tools import CodeExecutor
   from src.utils import get_config

   config = get_config()
   llm_manager = LLMManager(config)
   code_executor = CodeExecutor(
       timeout=30,
       enable_docker=False,
       enable_validation=True
   )

   agent = CodeAgent(
       llm_manager=llm_manager,
       code_executor=code_executor,
       config=config
   )

   result = await agent.solve("Calculate the factorial of 10")
   print(result['code'])
   print(result['output'])

Chat Agent
----------

Simple conversational AI agent.

.. automodule:: src.agents.chat_agent
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

   from src.agents import ChatAgent
   from src.llm import LLMManager
   from src.utils import get_config

   config = get_config()
   llm_manager = LLMManager(config)

   agent = ChatAgent(llm_manager=llm_manager, config=config)

   response = await agent.chat("Hello, how are you?")
   print(response)

RAG Agent
---------

Document-based question answering using vector search.

.. automodule:: src.agents.rag_agent
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

   from src.agents import RAGAgent
   from src.llm import LLMManager
   from src.tools import VectorStore, DocumentProcessor
   from src.utils import get_config

   config = get_config()
   llm_manager = LLMManager(config)
   vector_store = VectorStore()
   doc_processor = DocumentProcessor()

   agent = RAGAgent(
       llm_manager=llm_manager,
       vector_store=vector_store,
       doc_processor=doc_processor,
       config=config
   )

   # Ingest documents
   await agent.ingest_document("path/to/document.pdf")

   # Query
   result = await agent.query("What is the main topic?")
   print(result['answer'])
