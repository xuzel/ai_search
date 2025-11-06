LLM Module
==========

The LLM module provides a unified interface for multiple LLM providers with automatic fallback support.

Overview
--------

The LLM Manager supports:

* **OpenAI**: GPT models
* **Aliyun DashScope**: Qwen models
* **DeepSeek**: DeepSeek models
* **Ollama**: Local models
* **Custom OpenAI-compatible endpoints**

LLM Manager
-----------

.. automodule:: src.llm.manager
   :members:
   :undoc-members:
   :show-inheritance:

Base LLM
--------

.. automodule:: src.llm.base
   :members:
   :undoc-members:
   :show-inheritance:

OpenAI Client
-------------

.. automodule:: src.llm.openai_client
   :members:
   :undoc-members:
   :show-inheritance:

Ollama Client
-------------

.. automodule:: src.llm.ollama_client
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from src.llm import LLMManager
   from src.utils import get_config

   # Initialize manager
   config = get_config()
   llm_manager = LLMManager(config)

   # Generate completion
   messages = [
       {"role": "system", "content": "You are a helpful assistant."},
       {"role": "user", "content": "What is Python?"}
   ]

   response = await llm_manager.complete(messages)
   print(response)

Preferred Provider
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use specific provider
   response = await llm_manager.complete(
       messages,
       preferred_provider="openai"
   )

Custom Parameters
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom temperature and max_tokens
   response = await llm_manager.complete(
       messages,
       temperature=0.7,
       max_tokens=500
   )

Provider Configuration
----------------------

Configuration is done via ``config/config.yaml``:

.. code-block:: yaml

   llm:
     # OpenAI
     openai_enabled: true
     openai_api_key: ${OPENAI_API_KEY}
     openai_model: gpt-4
     openai_temperature: 0.7
     openai_max_tokens: 2000

     # Aliyun DashScope (Qwen)
     dashscope_enabled: true
     dashscope_api_key: ${DASHSCOPE_API_KEY}
     dashscope_model: qwen-max
     dashscope_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1

     # DeepSeek
     deepseek_enabled: false
     deepseek_api_key: ${DEEPSEEK_API_KEY}
     deepseek_model: deepseek-chat
     deepseek_base_url: https://api.deepseek.com/v1

     # Ollama (local)
     ollama_enabled: false
     ollama_base_url: http://localhost:11434
     ollama_model: llama2

Fallback Mechanism
------------------

The LLM Manager automatically tries providers in order:

1. **Preferred provider** (if specified)
2. **Primary provider** (first initialized provider)
3. **Remaining providers** (in order of initialization)

If a provider fails, the manager automatically falls back to the next available provider.

.. code-block:: python

   # Even if preferred provider fails, fallback providers will be tried
   try:
       response = await llm_manager.complete(
           messages,
           preferred_provider="unavailable_provider"
       )
       # Will use primary or other available providers
   except Exception as e:
       print(f"All providers failed: {e}")

Error Handling
--------------

.. code-block:: python

   from src.llm import LLMManager

   llm_manager = LLMManager(config)

   try:
       response = await llm_manager.complete(messages)
   except ValueError as e:
       print(f"Invalid input: {e}")
   except RuntimeError as e:
       print(f"No providers available: {e}")
   except Exception as e:
       print(f"Unexpected error: {e}")
