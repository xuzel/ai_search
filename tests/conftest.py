"""Pytest configuration and shared fixtures"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
import tempfile
import shutil

from src.utils import get_config
from src.llm import LLMManager


# ============================================================================
# Session Scope Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def config():
    """Load configuration once for entire test session"""
    return get_config()


@pytest.fixture(scope="session")
def llm_manager(config):
    """Initialize LLM manager once for entire test session"""
    return LLMManager(config=config)


# ============================================================================
# Function Scope Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for each test"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent.parent / "test_data"


@pytest.fixture
def sample_document(test_data_dir):
    """Create sample document for testing"""
    test_doc = test_data_dir / "sample_document.txt"
    test_data_dir.mkdir(exist_ok=True)

    if not test_doc.exists():
        test_doc.write_text(
            "AI Search Engine Test Document\n\n"
            "This is a test document for RAG system testing.\n"
            "It contains sample content for document processing and retrieval."
        )

    return test_doc


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for multiple components")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Tests that take a long time to run")
    config.addinivalue_line("markers", "security: Security-related tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "requires_api: Tests that require external API keys")
    config.addinivalue_line("markers", "requires_docker: Tests that require Docker")


# ============================================================================
# Skip Conditions
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests based on conditions"""

    # Skip tests that require API keys if not configured
    app_config = get_config()

    # Check which API keys are available
    has_serpapi = app_config.search.serpapi_key and "your" not in app_config.search.serpapi_key
    has_weather = (
        hasattr(app_config.domain_tools, 'weather') and
        app_config.domain_tools.weather.api_key and
        "your" not in app_config.domain_tools.weather.api_key
    )
    has_vision = (
        hasattr(app_config.multimodal, 'vision') and
        app_config.multimodal.vision.api_key and
        "your" not in app_config.multimodal.vision.api_key
    )

    skip_serpapi = pytest.mark.skip(reason="SerpAPI key not configured")
    skip_weather = pytest.mark.skip(reason="Weather API key not configured")
    skip_vision = pytest.mark.skip(reason="Vision API key not configured")

    for item in items:
        # Skip tests requiring specific APIs
        if "requires_api" in item.keywords:
            if "search" in item.nodeid.lower() and not has_serpapi:
                item.add_marker(skip_serpapi)
            elif "weather" in item.nodeid.lower() and not has_weather:
                item.add_marker(skip_weather)
            elif "vision" in item.nodeid.lower() and not has_vision:
                item.add_marker(skip_vision)
