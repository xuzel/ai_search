AI Search Engine Documentation
==============================

Welcome to the AI Search Engine documentation! This is an LLM-powered search engine with multiple intelligent modes.

Features
--------

* **Research Mode**: Web search, content scraping, and LLM-based synthesis
* **Code Mode**: Generates and executes Python code for math/computation problems
* **Chat Mode**: General conversational AI
* **RAG Mode**: Document Q&A with vector search (PDF, DOCX, etc.)
* **Domain Tools**: Weather, Finance, and Routing queries
* **Multimodal**: OCR and Vision API support
* **Workflow**: Multi-step task orchestration

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

Configuration
~~~~~~~~~~~~~

Configure API keys in ``config/config.yaml`` or set environment variables:

.. code-block:: bash

   export DASHSCOPE_API_KEY="your-key"  # For Aliyun Qwen models
   export SERPAPI_API_KEY="your-key"    # For web search

Running the Application
~~~~~~~~~~~~~~~~~~~~~~~

**Web UI (Recommended)**

.. code-block:: bash

   # Start web server
   python -m src.web.app

   # Access at http://localhost:8000

**CLI**

.. code-block:: bash

   # Run as module
   python -m src.main search "query here"
   python -m src.main solve "math problem"
   python -m src.main ask "question" --auto
   python -m src.main chat

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/routing
   api/agents
   api/tools
   api/llm
   api/workflow
   api/web
   api/utils

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   guide/installation
   guide/configuration
   guide/usage
   guide/deployment

.. toctree::
   :maxdepth: 1
   :caption: Development:

   dev/architecture
   dev/testing
   dev/contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
