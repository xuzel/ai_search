Utils Module
============

The utils module provides utility functions for configuration, logging, and data processing.

Overview
--------

Available utilities:

* **Config**: Pydantic-based configuration management
* **Logger**: Structured logging with JSON support
* **Secret Sanitizer**: Sensitive data removal
* **Entity Extractor**: Named entity extraction
* **JSON Logger**: Structured JSON logging

Configuration
-------------

.. automodule:: src.utils.config
   :members:
   :undoc-members:
   :show-inheritance:

Logging
-------

Logger
~~~~~~

.. automodule:: src.utils.logger
   :members:
   :undoc-members:
   :show-inheritance:

JSON Logger
~~~~~~~~~~~

.. automodule:: src.utils.json_logger
   :members:
   :undoc-members:
   :show-inheritance:

Security
--------

Secret Sanitizer
~~~~~~~~~~~~~~~~

.. automodule:: src.utils.secret_sanitizer
   :members:
   :undoc-members:
   :show-inheritance:

Entity Extraction
-----------------

.. automodule:: src.utils.entity_extractor
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Configuration
~~~~~~~~~~~~~

.. code-block:: python

   from src.utils import get_config

   # Load configuration
   config = get_config()

   # Access configuration
   print(config.llm.openai_api_key)
   print(config.search.serpapi_key)
   print(config.code_execution.timeout)

   # Configuration is cached
   config2 = get_config()
   assert config is config2  # Same instance

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Configuration supports environment variable substitution in ``config.yaml``:

.. code-block:: yaml

   llm:
     openai_api_key: ${OPENAI_API_KEY}  # Reads from env var
     dashscope_api_key: ${DASHSCOPE_API_KEY}

.. code-block:: bash

   # Set environment variables
   export OPENAI_API_KEY="sk-..."
   export DASHSCOPE_API_KEY="sk-..."

Logging
~~~~~~~

.. code-block:: python

   from src.utils.logger import get_logger

   logger = get_logger(__name__)

   # Standard logging
   logger.info("Processing query")
   logger.warning("API key not found")
   logger.error("Failed to connect", exc_info=True)

   # With extra fields
   logger.info(
       "Query processed",
       extra={
           "query": "test",
           "duration_ms": 123,
           "provider": "openai"
       }
   )

JSON Logging
~~~~~~~~~~~~

.. code-block:: python

   from src.utils.json_logger import get_json_logger

   logger = get_json_logger(__name__)

   # All logs are in JSON format
   logger.info(
       "API request",
       extra={
           "method": "POST",
           "endpoint": "/query",
           "duration_ms": 456,
           "status_code": 200
       }
   )

   # Output:
   # {
   #   "timestamp": "2025-01-05T10:30:45.123Z",
   #   "level": "INFO",
   #   "logger": "src.web.app",
   #   "message": "API request",
   #   "method": "POST",
   #   "endpoint": "/query",
   #   "duration_ms": 456,
   #   "status_code": 200
   # }

Secret Sanitizer
~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.utils.secret_sanitizer import sanitize_secrets

   # Sanitize sensitive data
   data = {
       "api_key": "sk-1234567890abcdef",
       "password": "secret123",
       "user": "john",
       "query": "What is Python?"
   }

   sanitized = sanitize_secrets(data)
   # {
   #   "api_key": "sk-***",
   #   "password": "***",
   #   "user": "john",
   #   "query": "What is Python?"
   # }

   # Works with nested structures
   nested = {
       "config": {
           "openai_api_key": "sk-1234567890abcdef",
           "settings": {
               "timeout": 30
           }
       }
   }

   sanitized_nested = sanitize_secrets(nested)
   # {
   #   "config": {
   #     "openai_api_key": "sk-***",
   #     "settings": {
   #       "timeout": 30
   #     }
   #   }
   # }

Entity Extractor
~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.utils.entity_extractor import EntityExtractor

   extractor = EntityExtractor()

   # Extract entities from text
   text = "Apple Inc. is headquartered in Cupertino, California. Tim Cook is the CEO."

   entities = extractor.extract(text)
   # {
   #   "organizations": ["Apple Inc."],
   #   "locations": ["Cupertino", "California"],
   #   "persons": ["Tim Cook"],
   #   "dates": []
   # }

   # Extract specific entity type
   orgs = extractor.extract_organizations(text)
   # ["Apple Inc."]

Configuration Priority
~~~~~~~~~~~~~~~~~~~~~~

Configuration values are loaded with the following priority (highest to lowest):

1. Environment variables
2. ``config/config.yaml`` file
3. Default values

.. code-block:: python

   # config.yaml
   llm:
     openai_api_key: ${OPENAI_API_KEY}  # From env var (priority 1)
     openai_model: gpt-4                # From YAML (priority 2)
     openai_temperature: 0.7            # From YAML (priority 2)

   # If OPENAI_API_KEY env var is not set, ValueError is raised
   # If openai_model is not in YAML, default from Pydantic model is used
