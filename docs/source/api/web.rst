Web Module
==========

The web module provides a FastAPI-based web interface with HTMX for dynamic interactions.

Overview
--------

Architecture:

* **FastAPI**: Modern async web framework
* **HTMX**: Dynamic UI without heavy JavaScript
* **Jinja2**: Template rendering
* **SQLite**: Async database for history
* **SSE**: Server-sent events for streaming

Application
-----------

.. automodule:: src.web.app
   :members:
   :undoc-members:
   :show-inheritance:

Database
--------

.. automodule:: src.web.database
   :members:
   :undoc-members:
   :show-inheritance:

Upload Manager
--------------

.. automodule:: src.web.upload_manager
   :members:
   :undoc-members:
   :show-inheritance:

Routers
-------

Main Router
~~~~~~~~~~~

.. automodule:: src.web.routers.main
   :members:
   :undoc-members:
   :show-inheritance:

Query Router
~~~~~~~~~~~~

.. automodule:: src.web.routers.query
   :members:
   :undoc-members:
   :show-inheritance:

Search Router
~~~~~~~~~~~~~

.. automodule:: src.web.routers.search
   :members:
   :undoc-members:
   :show-inheritance:

Code Router
~~~~~~~~~~~

.. automodule:: src.web.routers.code
   :members:
   :undoc-members:
   :show-inheritance:

Chat Router
~~~~~~~~~~~

.. automodule:: src.web.routers.chat
   :members:
   :undoc-members:
   :show-inheritance:

RAG Router
~~~~~~~~~~

.. automodule:: src.web.routers.rag
   :members:
   :undoc-members:
   :show-inheritance:

Multimodal Router
~~~~~~~~~~~~~~~~~

.. automodule:: src.web.routers.multimodal
   :members:
   :undoc-members:
   :show-inheritance:

Tools Router
~~~~~~~~~~~~

.. automodule:: src.web.routers.tools
   :members:
   :undoc-members:
   :show-inheritance:

Workflow Router
~~~~~~~~~~~~~~~

.. automodule:: src.web.routers.workflow
   :members:
   :undoc-members:
   :show-inheritance:

History Router
~~~~~~~~~~~~~~

.. automodule:: src.web.routers.history
   :members:
   :undoc-members:
   :show-inheritance:

Dependencies
------------

Core Dependencies
~~~~~~~~~~~~~~~~~

.. automodule:: src.web.dependencies.core
   :members:
   :undoc-members:
   :show-inheritance:

Tool Dependencies
~~~~~~~~~~~~~~~~~

.. automodule:: src.web.dependencies.tools
   :members:
   :undoc-members:
   :show-inheritance:

Formatters
~~~~~~~~~~

.. automodule:: src.web.dependencies.formatters
   :members:
   :undoc-members:
   :show-inheritance:

Middleware
----------

Rate Limiter
~~~~~~~~~~~~

.. automodule:: src.web.middleware.rate_limiter
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Running the Server
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start web server
   python -m src.web.app

   # Or using uvicorn directly
   uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000

   # With custom configuration
   WEB_HOST=127.0.0.1 WEB_PORT=8080 python -m src.web.app

API Endpoints
~~~~~~~~~~~~~

**Health Check**

.. code-block:: bash

   curl http://localhost:8000/health

**Query (Unified)**

.. code-block:: bash

   curl -X POST http://localhost:8000/query \\
     -F "query=What is Python?"

**Search**

.. code-block:: bash

   curl -X POST http://localhost:8000/search \\
     -F "query=quantum computing"

**Code Execution**

.. code-block:: bash

   curl -X POST http://localhost:8000/code \\
     -F "query=Calculate factorial of 10"

**Chat**

.. code-block:: bash

   curl -X POST http://localhost:8000/chat \\
     -F "message=Hello!"

**RAG Document Upload**

.. code-block:: bash

   curl -X POST http://localhost:8000/rag/upload \\
     -F "file=@document.pdf"

**RAG Query**

.. code-block:: bash

   curl -X POST http://localhost:8000/rag/query \\
     -F "query=What is the main topic?"

**Weather**

.. code-block:: bash

   curl -X POST http://localhost:8000/tools/weather \\
     -F "query=Weather in Beijing"

**Finance**

.. code-block:: bash

   curl -X POST http://localhost:8000/tools/finance \\
     -F "query=AAPL stock price"

Database Schema
~~~~~~~~~~~~~~~

**conversation_history table**

.. code-block:: sql

   CREATE TABLE conversation_history (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       timestamp TEXT NOT NULL,
       mode TEXT NOT NULL,
       query TEXT NOT NULL,
       response TEXT NOT NULL,
       metadata TEXT
   );

   CREATE INDEX idx_timestamp ON conversation_history(timestamp);
   CREATE INDEX idx_mode ON conversation_history(mode);

**rag_documents table**

.. code-block:: sql

   CREATE TABLE rag_documents (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       filename TEXT NOT NULL,
       saved_filename TEXT NOT NULL,
       filepath TEXT NOT NULL,
       file_type TEXT NOT NULL,
       file_size INTEGER NOT NULL,
       file_hash TEXT NOT NULL UNIQUE,
       upload_timestamp TEXT NOT NULL,
       processing_status TEXT NOT NULL,
       num_chunks INTEGER,
       vector_store_ids TEXT,
       metadata TEXT
   );

   CREATE INDEX idx_upload_timestamp ON rag_documents(upload_timestamp);
   CREATE INDEX idx_processing_status ON rag_documents(processing_status);

Template Development
~~~~~~~~~~~~~~~~~~~~

**Base Template**

.. code-block:: html+jinja

   {% extends "base.html" %}

   {% block title %}My Page{% endblock %}

   {% block content %}
   <div class="container">
       <h1>My Content</h1>
   </div>
   {% endblock %}

**HTMX Integration**

.. code-block:: html

   <form hx-post="/query"
         hx-target="#result"
         hx-indicator="#loading">
       <input type="text" name="query" />
       <button type="submit">Submit</button>
   </form>

   <div id="loading" class="htmx-indicator">
       Loading...
   </div>

   <div id="result">
       <!-- Response will be inserted here -->
   </div>
