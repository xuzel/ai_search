Installation Guide
==================

This guide covers the installation and setup of the AI Search Engine.

Requirements
------------

* **Python**: 3.10, 3.11, or 3.12
* **Operating System**: Linux, macOS, or Windows
* **Memory**: Minimum 4GB RAM (8GB+ recommended for RAG features)
* **Disk Space**: ~5GB (for models and vector databases)

Quick Install
-------------

1. Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yourusername/ai_search.git
   cd ai_search

2. Create Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv

   # Activate (Linux/macOS)
   source venv/bin/activate

   # Activate (Windows)
   venv\Scripts\activate

3. Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install all dependencies
   pip install -r requirements.txt

   # Or install specific groups
   pip install -r requirements.txt --no-deps  # Core only

4. Configure Environment
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Copy example config
   cp .env.example .env

   # Edit .env with your API keys
   nano .env

5. Verify Installation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run tests
   pytest tests/ -v

   # Check system info
   python -m src.main info

Detailed Installation
---------------------

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development with additional tools:

.. code-block:: bash

   # Install with development dependencies
   pip install -r requirements.txt

   # Install pre-commit hooks
   pre-commit install

Docker Installation
~~~~~~~~~~~~~~~~~~~

Using Docker (recommended for production):

.. code-block:: bash

   # Build image
   docker build -t ai-search .

   # Run container
   docker run -p 8000:8000 \\
     -e DASHSCOPE_API_KEY=your-key \\
     -e SERPAPI_API_KEY=your-key \\
     ai-search

Optional Components
-------------------

Docker (for Code Execution Sandbox)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Add user to docker group
   sudo usermod -aG docker $USER

   # Enable in config
   # config/config.yaml:
   # code_execution:
   #   enable_docker: true

PaddleOCR (for OCR Support)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Already included in requirements.txt
   # Download models (happens automatically on first use)
   python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='en')"

GPU Support (for Faster Embeddings)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install PyTorch with CUDA
   pip install torch==2.2.0+cu118 -f https://download.pytorch.org/whl/torch_stable.html

   # Verify CUDA
   python -c "import torch; print(torch.cuda.is_available())"

API Keys Configuration
----------------------

Required API Keys
~~~~~~~~~~~~~~~~~

Minimum required keys for basic functionality:

* ``DASHSCOPE_API_KEY`` or ``OPENAI_API_KEY``: For LLM (at least one required)
* ``SERPAPI_API_KEY``: For web search (required for research mode)

Optional API Keys
~~~~~~~~~~~~~~~~~

For additional features:

* ``GOOGLE_API_KEY``: For Gemini Vision API (multimodal)
* ``OPENWEATHERMAP_API_KEY``: For weather data
* ``ALPHA_VANTAGE_API_KEY``: For stock/finance data
* ``OPENROUTESERVICE_API_KEY``: For routing/navigation

Configuration Methods
~~~~~~~~~~~~~~~~~~~~~

**Method 1: Environment Variables** (Recommended)

.. code-block:: bash

   # .env file
   DASHSCOPE_API_KEY=sk-your-key-here
   SERPAPI_API_KEY=your-serpapi-key
   OPENWEATHERMAP_API_KEY=your-weather-key

**Method 2: config.yaml**

.. code-block:: yaml

   # config/config.yaml
   llm:
     dashscope_api_key: ${DASHSCOPE_API_KEY}  # Still uses env var
     # OR direct value (not recommended for secrets)
     # dashscope_api_key: sk-your-key-here

   search:
     serpapi_key: ${SERPAPI_API_KEY}

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

.. code-block:: bash

   # If you see "ModuleNotFoundError"
   # Make sure you're in the virtual environment
   which python  # Should show path to venv

   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall

API Key Errors
~~~~~~~~~~~~~~

.. code-block:: bash

   # If you see "API key not found"
   # Check environment variables
   echo $DASHSCOPE_API_KEY

   # Reload .env file
   source .env  # Linux/macOS
   # Or restart your shell

Permission Errors (Docker)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # If you see "permission denied" with Docker
   # Add user to docker group
   sudo usermod -aG docker $USER

   # Log out and log back in
   newgrp docker

   # Verify
   docker run hello-world

Model Download Issues
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # If sentence-transformers fails to download
   # Set cache directory
   export TRANSFORMERS_CACHE=/path/to/cache
   export SENTENCE_TRANSFORMERS_HOME=/path/to/cache

   # Or use proxy
   export HF_ENDPOINT=https://hf-mirror.com  # For China users

Next Steps
----------

* See :doc:`configuration` for detailed configuration options
* See :doc:`usage` for usage examples
* See :doc:`deployment` for production deployment
