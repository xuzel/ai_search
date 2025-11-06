Testing Guide
=============

This guide covers testing practices for the AI Search Engine.

Test Overview
-------------

The project uses pytest with comprehensive test coverage:

* **Total Tests**: 181
* **Coverage**: 33%
* **Test Categories**: unit, integration, API, security, performance, load

Test Structure
--------------

.. code-block:: text

   tests/
   ├── conftest.py                 # Shared fixtures
   ├── test_routing.py             # 33 tests (routing)
   ├── test_code_security.py       # 40 tests (security)
   ├── test_complete_system.py     # 14 tests (integration)
   ├── test_web_api.py             # 8 tests (API)
   ├── test_tools.py               # 25 tests (tools)
   ├── test_agents.py              # 19 tests (agents)
   ├── test_workflow.py            # 21 tests (workflow)
   ├── test_performance.py         # 15 tests (performance)
   ├── test_load.py                # 12 tests (load)
   └── archive/                    # Archived tests

Running Tests
-------------

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest tests/

   # Verbose output
   pytest tests/ -v

   # Stop on first failure
   pytest tests/ -x

   # Show local variables on failure
   pytest tests/ -l

By Category
~~~~~~~~~~~

.. code-block:: bash

   # Unit tests only
   pytest tests/ -m unit

   # Integration tests
   pytest tests/ -m integration

   # Security tests
   pytest tests/ -m security

   # API tests (requires running server)
   pytest tests/ -m api

   # Skip slow tests
   pytest tests/ -m "not slow"

   # Skip tests requiring API keys
   pytest tests/ -m "not requires_api"

With Coverage
~~~~~~~~~~~~~

.. code-block:: bash

   # Run with coverage
   pytest tests/ --cov=src --cov-report=html

   # View coverage report
   open htmlcov/index.html

   # Generate XML report (for CI/CD)
   pytest tests/ --cov=src --cov-report=xml

   # Generate JSON report
   pytest tests/ --cov=src --cov-report=json

Parallel Execution
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install pytest-xdist
   pip install pytest-xdist

   # Run tests in parallel (4 workers)
   pytest tests/ -n 4

   # Auto-detect CPU count
   pytest tests/ -n auto

Specific Tests
~~~~~~~~~~~~~~

.. code-block:: bash

   # Run specific file
   pytest tests/test_routing.py

   # Run specific test class
   pytest tests/test_routing.py::TestKeywordRouter

   # Run specific test method
   pytest tests/test_routing.py::TestKeywordRouter::test_research_query

   # Run tests matching pattern
   pytest tests/ -k "test_router"

Test Markers
------------

Available markers defined in ``pytest.ini``:

* ``@pytest.mark.unit``: Unit tests (95 tests)
* ``@pytest.mark.integration``: Integration tests (17 tests)
* ``@pytest.mark.api``: API endpoint tests (20 tests)
* ``@pytest.mark.security``: Security tests (40 tests)
* ``@pytest.mark.slow``: Performance/load tests (27 tests)
* ``@pytest.mark.requires_api``: Tests needing API keys (15 tests)
* ``@pytest.mark.requires_docker``: Tests needing Docker

Writing Tests
-------------

Unit Test Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from src.routing import KeywordRouter

   @pytest.mark.unit
   class TestKeywordRouter:
       @pytest.fixture
       def router(self):
           return KeywordRouter()

       @pytest.mark.asyncio
       async def test_research_query(self, router):
           decision = await router.route("What is Python?")

           assert decision.primary_task_type == TaskType.RESEARCH
           assert decision.task_confidence > 0.7

Integration Test Example
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from src.agents import ResearchAgent
   from src.llm import LLMManager
   from src.utils import get_config

   @pytest.mark.integration
   @pytest.mark.requires_api
   @pytest.mark.asyncio
   async def test_research_flow():
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

       result = await agent.research("test query")

       assert "summary" in result
       assert "sources" in result
       assert len(result["sources"]) > 0

API Test Example
~~~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   import aiohttp

   @pytest.mark.api
   @pytest.mark.asyncio
   async def test_health_endpoint():
       async with aiohttp.ClientSession() as session:
           async with session.get("http://localhost:8000/health") as response:
               assert response.status == 200
               data = await response.json()
               assert data["status"] == "healthy"

Using Fixtures
~~~~~~~~~~~~~~

.. code-block:: python

   @pytest.fixture
   def config():
       """Shared configuration fixture"""
       return get_config()

   @pytest.fixture
   def llm_manager(config):
       """Shared LLM manager fixture"""
       return LLMManager(config=config)

   @pytest.fixture
   def temp_dir():
       """Temporary directory fixture"""
       temp = tempfile.mkdtemp()
       yield temp
       shutil.rmtree(temp, ignore_errors=True)

Mocking
~~~~~~~

.. code-block:: python

   from unittest.mock import AsyncMock, MagicMock

   @pytest.mark.unit
   @pytest.mark.asyncio
   async def test_with_mock():
       # Mock LLM
       mock_llm = AsyncMock()
       mock_llm.complete = AsyncMock(return_value="test response")

       # Use mock
       agent = ChatAgent(llm_manager=mock_llm)
       response = await agent.chat("test")

       assert response == "test response"
       mock_llm.complete.assert_called_once()

Performance Testing
-------------------

Benchmarks
~~~~~~~~~~

.. code-block:: python

   @pytest.mark.slow
   def test_router_speed(benchmark):
       router = create_router(config, llm_manager, router_type='keyword')

       def classify_query():
           return asyncio.run(router.route("test query"))

       result = benchmark(classify_query)

       # Assert performance target
       assert benchmark.stats['mean'] < 0.1  # < 100ms

Load Testing
~~~~~~~~~~~~

.. code-block:: python

   @pytest.mark.slow
   @pytest.mark.api
   @pytest.mark.asyncio
   async def test_concurrent_load():
       async with aiohttp.ClientSession() as session:
           # 100 concurrent requests
           tasks = [
               session.get("http://localhost:8000/health")
               for _ in range(100)
           ]

           start = time.time()
           responses = await asyncio.gather(*tasks)
           duration = time.time() - start

           assert duration < 2.0  # All requests in < 2s
           assert all(r.status == 200 for r in responses)

Coverage Goals
--------------

Current Coverage
~~~~~~~~~~~~~~~~

* Overall: 33%
* Routing: 88%
* Tools: 33%
* Agents: 45%
* Workflow: 35%

Target Coverage
~~~~~~~~~~~~~~~

* Short-term: 60%
* Long-term: 80%+

Coverage by Module
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check coverage by module
   pytest tests/ --cov=src --cov-report=term-missing

   # Fail if coverage below threshold
   pytest tests/ --cov=src --cov-fail-under=60

CI/CD Integration
-----------------

GitHub Actions
~~~~~~~~~~~~~~

The project uses GitHub Actions for automated testing:

.. code-block:: yaml

   # .github/workflows/test.yml
   jobs:
     test:
       runs-on: ubuntu-latest
       strategy:
         matrix:
           python-version: ['3.10', '3.11', '3.12']

       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-python@v4
         - run: pip install -r requirements.txt
         - run: pytest tests/ -m "unit and not requires_docker" --cov=src
         - uses: codecov/codecov-action@v3

Codecov Integration
~~~~~~~~~~~~~~~~~~~

Coverage reports are automatically uploaded to Codecov:

* Pull request comments with coverage diff
* Coverage badges for README
* Trend tracking over time

Testing Best Practices
-----------------------

1. **Write Tests First** (TDD)

   Write tests before implementing features.

2. **Use Descriptive Names**

   .. code-block:: python

      def test_router_classifies_weather_query_correctly():
          # Clear what is being tested

3. **Test One Thing**

   Each test should verify one specific behavior.

4. **Use Fixtures**

   Share setup code with pytest fixtures.

5. **Mock External Dependencies**

   Don't rely on external APIs in unit tests.

6. **Test Error Cases**

   Test both success and failure scenarios.

7. **Keep Tests Fast**

   Unit tests should run in milliseconds.

8. **Use Markers**

   Mark tests appropriately (unit, integration, slow, etc.).

9. **Check Coverage**

   Aim for high coverage on critical code.

10. **Clean Up**

    Use fixtures with cleanup logic.

Common Testing Patterns
-----------------------

Parametrized Tests
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @pytest.mark.parametrize("query,expected_type", [
       ("What is Python?", TaskType.RESEARCH),
       ("Calculate 2+2", TaskType.CODE),
       ("Hello", TaskType.CHAT),
   ])
   async def test_routing(router, query, expected_type):
       decision = await router.route(query)
       assert decision.primary_task_type == expected_type

Async Tests
~~~~~~~~~~~

.. code-block:: python

   @pytest.mark.asyncio
   async def test_async_function():
       result = await some_async_function()
       assert result is not None

Exception Testing
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_exception():
       with pytest.raises(ValueError, match="Invalid input"):
           some_function(invalid_input)

Temporary Files
~~~~~~~~~~~~~~~

.. code-block:: python

   def test_file_processing(tmp_path):
       test_file = tmp_path / "test.txt"
       test_file.write_text("content")

       result = process_file(str(test_file))

       assert result is not None

Troubleshooting
---------------

Tests Fail with Import Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Make sure src/ is in Python path
   export PYTHONPATH="${PYTHONPATH}:."

   # Or use conftest.py to add path
   # (already done in tests/conftest.py)

Async Tests Fail
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install pytest-asyncio
   pip install pytest-asyncio

   # Mark test with @pytest.mark.asyncio

API Tests Fail
~~~~~~~~~~~~~~

.. code-block:: bash

   # Make sure server is running
   python -m src.web.app &

   # Run API tests
   pytest tests/test_load.py -v

Performance Tests Flaky
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Add appropriate margins
   assert duration < 0.5  # Instead of < 0.1

   # Or skip on slow systems
   @pytest.mark.skipif(
       os.getenv("CI") is not None,
       reason="Skip performance tests in CI"
   )

Next Steps
----------

* See :doc:`/guide/configuration` for test configuration
* See :doc:`contributing` for contribution guidelines
* See ``LOAD_TESTING_GUIDE.md`` for detailed load testing guide
