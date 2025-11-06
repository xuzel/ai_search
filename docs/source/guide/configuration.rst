Configuration Guide
===================

This guide covers all configuration options for the AI Search Engine.

Configuration File
------------------

The main configuration file is ``config/config.yaml``. It uses Pydantic for validation and supports environment variable substitution.

Structure
~~~~~~~~~

.. code-block:: yaml

   # LLM Configuration
   llm:
     # Provider settings
     # Search Configuration
   search:
     # Search settings
   # RAG Configuration
   rag:
     # Vector store settings
   # Code Execution
   code_execution:
     # Sandbox settings
   # Domain Tools
   domain_tools:
     # Weather, finance, routing

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Use ``${VAR_NAME}`` syntax for environment variable substitution:

.. code-block:: yaml

   llm:
     openai_api_key: ${OPENAI_API_KEY}
     dashscope_api_key: ${DASHSCOPE_API_KEY}

LLM Configuration
-----------------

OpenAI
~~~~~~

.. code-block:: yaml

   llm:
     openai_enabled: true  # Enable/disable provider
     openai_api_key: ${OPENAI_API_KEY}
     openai_model: gpt-4
     openai_base_url: https://api.openai.com/v1  # Optional
     openai_provider_name: OpenAI  # Display name
     openai_temperature: 0.7
     openai_max_tokens: 2000

Aliyun DashScope (Qwen)
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   llm:
     dashscope_enabled: true
     dashscope_api_key: ${DASHSCOPE_API_KEY}
     dashscope_model: qwen-max
     dashscope_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1

DeepSeek
~~~~~~~~

.. code-block:: yaml

   llm:
     deepseek_enabled: false
     deepseek_api_key: ${DEEPSEEK_API_KEY}
     deepseek_model: deepseek-chat
     deepseek_base_url: https://api.deepseek.com/v1

Ollama (Local)
~~~~~~~~~~~~~~

.. code-block:: yaml

   llm:
     ollama_enabled: false
     ollama_base_url: http://localhost:11434
     ollama_model: llama2

Custom OpenAI-Compatible
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   llm:
     local_compatible_enabled: true
     local_compatible_api_key: not-needed  # Optional
     local_compatible_model: custom-model
     local_compatible_base_url: http://localhost:8080/v1

Search Configuration
--------------------

.. code-block:: yaml

   search:
     serpapi_key: ${SERPAPI_API_KEY}
     default_engine: google  # google, bing, duckduckgo
     num_results: 10
     safe_search: moderate  # off, moderate, strict

RAG Configuration
-----------------

Vector Store
~~~~~~~~~~~~

.. code-block:: yaml

   rag:
     vector_store:
       persist_directory: ./data/vector_store
       collection_name: documents
       embedding_model: sentence-transformers/all-MiniLM-L6-v2
       embedding_dimension: 384
       cache_size: 1000
       cache_ttl: 3600  # seconds

Chunking
~~~~~~~~

.. code-block:: yaml

   rag:
     chunking:
       strategy: semantic  # semantic, fixed, recursive
       chunk_size: 500
       chunk_overlap: 50
       semantic_threshold: 0.5  # For semantic chunking

Retrieval
~~~~~~~~~

.. code-block:: yaml

   rag:
     retrieval:
       top_k: 10
       similarity_threshold: 0.7
       enable_reranking: true
       reranker_top_k: 5

Reranking
~~~~~~~~~

.. code-block:: yaml

   rag:
     reranking:
       strategy: hybrid  # bge, cross_encoder, hybrid
       bge_model: BAAI/bge-reranker-large
       cross_encoder_model: cross-encoder/ms-marco-MiniLM-L-6-v2
       hybrid_weight_bge: 0.6
       hybrid_weight_cross: 0.4

Code Execution Configuration
-----------------------------

.. code-block:: yaml

   code_execution:
     timeout: 30  # seconds
     max_output_lines: 1000
     enable_docker: false  # Set to true for production
     enable_validation: true
     allowed_imports:
       - math
       - statistics
       - datetime
       - json
       - collections
       - itertools
       - functools
       - random
       - re
     docker_image: python:3.11-slim
     docker_memory_limit: 512m
     docker_cpu_limit: 1.0

Domain Tools Configuration
--------------------------

Weather
~~~~~~~

.. code-block:: yaml

   domain_tools:
     weather:
       enabled: true
       api_key: ${OPENWEATHERMAP_API_KEY}
       default_units: metric  # metric, imperial
       default_language: en

Finance
~~~~~~~

.. code-block:: yaml

   domain_tools:
     finance:
       enabled: true
       alpha_vantage_key: ${ALPHA_VANTAGE_API_KEY}
       enable_yfinance_fallback: true  # Free fallback
       default_interval: 1day  # 1min, 5min, 15min, 1day, 1week

Routing
~~~~~~~

.. code-block:: yaml

   domain_tools:
     routing:
       enabled: true
       api_key: ${OPENROUTESERVICE_API_KEY}
       default_profile: driving-car  # driving-car, cycling-regular, foot-walking
       default_units: km  # km, mi

Multimodal Configuration
------------------------

OCR
~~~

.. code-block:: yaml

   multimodal:
     ocr:
       enabled: true
       use_angle_cls: true
       lang: en  # en, ch, en,ch (both)
       det_db_thresh: 0.3
       det_db_box_thresh: 0.6

Vision
~~~~~~

.. code-block:: yaml

   multimodal:
     vision:
       enabled: true
       google_api_key: ${GOOGLE_API_KEY}
       model: gemini-pro-vision
       max_output_tokens: 2048

Routing Configuration
---------------------

.. code-block:: yaml

   routing:
     router_type: hybrid  # keyword, llm, hybrid
     hybrid_threshold: 0.6  # Use LLM if keyword confidence < 0.6
     enable_caching: true
     cache_ttl: 3600  # seconds

Research Configuration
----------------------

.. code-block:: yaml

   research:
     max_queries: 5
     top_results_per_query: 3
     max_scrape_concurrent: 5
     summary_max_tokens: 500
     enable_credibility_scoring: true

Workflow Configuration
----------------------

.. code-block:: yaml

   workflow:
     max_concurrent_tasks: 10
     default_task_timeout: 300  # seconds
     default_retry_count: 3
     enable_progress_callbacks: true

Web Server Configuration
------------------------

.. code-block:: yaml

   web:
     host: 0.0.0.0
     port: 8000
     reload: false  # Set to true for development
     workers: 4  # Number of worker processes
     log_level: info  # debug, info, warning, error

Rate Limiting
~~~~~~~~~~~~~

.. code-block:: yaml

   web:
     rate_limiting:
       enabled: true
       requests_per_minute: 30
       burst_size: 10

CORS
~~~~

.. code-block:: yaml

   web:
     cors:
       enabled: true
       allow_origins:
         - http://localhost:3000
         - https://example.com
       allow_methods:
         - GET
         - POST
       allow_headers:
         - "*"

Logging Configuration
---------------------

.. code-block:: yaml

   logging:
     level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
     format: json  # json, text
     file: logs/app.log  # Optional log file
     max_bytes: 10485760  # 10MB
     backup_count: 5
     enable_console: true

Advanced Configuration
----------------------

Caching
~~~~~~~

.. code-block:: yaml

   caching:
     enabled: true
     backend: memory  # memory, redis
     redis_url: redis://localhost:6379/0  # If using Redis
     default_ttl: 3600

Security
~~~~~~~~

.. code-block:: yaml

   security:
     enable_api_key_auth: false  # Set to true for production
     api_keys:
       - ${API_KEY_1}
       - ${API_KEY_2}
     enable_secret_sanitization: true
     allowed_hosts:
       - localhost
       - example.com

Performance
~~~~~~~~~~~

.. code-block:: yaml

   performance:
     enable_async_db: true
     max_db_connections: 10
     enable_connection_pooling: true
     enable_query_optimization: true

Configuration Validation
------------------------

The configuration is validated on load using Pydantic. Invalid configurations will raise errors:

.. code-block:: python

   from src.utils import get_config

   try:
       config = get_config()
   except ValueError as e:
       print(f"Invalid configuration: {e}")

Environment-Specific Configuration
-----------------------------------

**Development**

.. code-block:: yaml

   # config/config.dev.yaml
   web:
     reload: true
     workers: 1
     log_level: debug

   logging:
     level: DEBUG

**Production**

.. code-block:: yaml

   # config/config.prod.yaml
   web:
     reload: false
     workers: 4
     log_level: warning

   code_execution:
     enable_docker: true

   security:
     enable_api_key_auth: true

**Loading environment-specific config:**

.. code-block:: bash

   # Set environment
   export CONFIG_ENV=production

   # Config file loaded: config/config.prod.yaml
   python -m src.web.app

Best Practices
--------------

1. **Use Environment Variables for Secrets**

   Never commit API keys to version control. Always use environment variables.

2. **Enable Docker in Production**

   For code execution, always use Docker sandbox in production.

3. **Configure Rate Limiting**

   Protect your API from abuse with appropriate rate limits.

4. **Enable CORS Carefully**

   Only allow trusted origins in production.

5. **Use Appropriate Log Levels**

   Use DEBUG for development, INFO for production.

6. **Configure Caching**

   Use Redis for distributed caching in production.

7. **Validate Configuration**

   Run ``python -m src.main info`` to verify configuration.
