# Archived Test Files

**Date**: 2025-11-05
**Phase**: 7.1 - Test Consolidation

## Purpose

This directory contains historical test files that have been consolidated into the main test suite. These files are kept for reference but are no longer actively maintained or run.

## Archived Files

### Integration Tests (Consolidated → test_complete_system.py)
- **comprehensive_test.py** (19KB) - Full feature test for Phase 1-5
- **final_test.py** (14KB) - Similar to comprehensive, skips weather API
- **quick_test.py** (8.7KB) - Quick smoke tests for core features

**Reason**: These three files had significant overlap in testing the same features (RAG, OCR, Vision, Weather, Finance, Routing, Research Agent, etc.). Consolidated into `test_complete_system.py` which provides the most comprehensive coverage.

### Web API Tests (Consolidated → test_web_api.py)
- **test_basic_functions.py** (6.0KB) - Basic web UI endpoint tests
- **test_web_ui.py** (4.5KB) - Additional web UI tests

**Reason**: Duplicate scope testing the same endpoints (health check, homepage, CSS/JS loading, classification). Consolidated into `test_web_api.py` with proper pytest structure and markers.

## Active Test Files

The following test files remain active and are properly organized:

### Unit Tests
- `test_routing.py` - Routing system unit tests (keyword, LLM, hybrid routers)
- `test_code_security.py` - Security system unit tests (3-layer architecture)

### Integration Tests
- `test_complete_system.py` - Comprehensive system integration tests (14 test scenarios)
- `test_web_api.py` - Web API endpoint tests (8 test scenarios)

### Configuration
- `conftest.py` - Shared pytest fixtures and configuration
- `pytest.ini` - Pytest configuration with markers and coverage settings

## Test Organization

**By Type**:
- Unit tests: Focus on individual components
- Integration tests: Test multiple components working together
- API tests: Test web endpoints and HTTP interfaces

**By Markers**:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.requires_api` - Tests requiring external API keys
- `@pytest.mark.requires_docker` - Tests requiring Docker

## Running Tests

```bash
# Run all active tests
pytest tests/

# Run specific test file
pytest tests/test_routing.py -v

# Run tests by marker
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m "not slow"

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Migration Notes

**Test Coverage Maintained**:
- All test scenarios from archived files are covered in active test files
- Proper pytest structure with fixtures, markers, and parameterization
- Better organization with conftest.py for shared fixtures
- Conditional skipping for tests requiring API keys

**Improvements**:
- Reduced duplication: 5 redundant files → 2 consolidated files
- Better structure: Proper pytest classes and fixtures
- More maintainable: Shared configuration in conftest.py
- Clearer purpose: Each test file has a specific scope

## Restoration

If you need to restore any archived test file:
```bash
cp tests/archive/comprehensive_test.py tests/
python tests/comprehensive_test.py  # Run directly (not via pytest)
```

Note: Archived files use `asyncio.run()` and can be run directly, but they are not integrated with pytest markers and fixtures.
