# Coverage Setup Guide

**Date**: 2025-11-05
**Phase**: 7.2 - Add pytest-cov coverage
**Status**: ✅ COMPLETED

## Overview

Comprehensive test coverage reporting setup with pytest-cov, including:
- ✅ `.coveragerc` configuration file
- ✅ pytest.ini integration
- ✅ GitHub Actions CI/CD workflow
- ✅ HTML, XML, JSON, and terminal coverage reports
- ✅ Automatic coverage badges
- ✅ Codecov integration

## Files Created/Modified

### 1. `.coveragerc` - Coverage Configuration

**Purpose**: Configure coverage.py behavior

**Key Settings**:
```ini
[run]
source = src
branch = True
omit =
    */tests/*
    src/web/*       # Exclude web UI (requires running server)
    src/workflow/*  # Exclude workflow (to be tested in Phase 7.3)

[report]
precision = 2
show_missing = True
skip_covered = False

exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
title = AI Search Engine Coverage Report
```

**Benefits**:
- ✅ Excludes test files from coverage
- ✅ Tracks branch coverage (if/else branches)
- ✅ Skips web UI and workflow (requires integration testing)
- ✅ Sensible exclusion patterns

### 2. `pytest.ini` - Coverage Integration

**Added**:
```ini
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    --cov-report=json
    # --cov-fail-under=60  # Enable after Phase 7.3
```

**Benefits**:
- ✅ Automatic coverage on every test run
- ✅ Multiple report formats (HTML, XML, JSON, terminal)
- ✅ Configurable failure threshold (commented out for now)

### 3. `.github/workflows/test.yml` - CI/CD Workflow

**Purpose**: Automated testing on GitHub

**Jobs**:
1. **test** - Unit tests across Python 3.10, 3.11, 3.12
2. **integration-test** - Integration tests (on push)
3. **security-test** - Security-specific tests

**Features**:
```yaml
- Matrix testing: Python 3.10, 3.11, 3.12
- Parallel execution: pytest -n auto (pytest-xdist)
- Coverage upload: Codecov integration
- Coverage badge: Automatic generation
- Dependency caching: pip cache
- Conditional runs: Integration tests on push only
```

**Benefits**:
- ✅ Tests run automatically on push/PR
- ✅ Multi-version Python testing
- ✅ Fast parallel execution
- ✅ Coverage tracking over time
- ✅ Automatic badge generation

## Coverage Reports

### 1. HTML Report (Best for local development)

**Generate**:
```bash
pytest tests/ --cov=src --cov-report=html
```

**View**:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Features**:
- Interactive file browser
- Line-by-line coverage highlighting
- Branch coverage visualization
- Missing lines highlighted in red
- Covered lines in green

### 2. Terminal Report (Best for quick checks)

**Generate**:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

**Output**:
```
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
src/__init__.py                          4      0   100%
src/routing/__init__.py                  6      0   100%
src/routing/base.py                     51      5    90%   45-49
src/routing/keyword_router.py          127     15    88%   67, 102-115
src/routing/llm_router.py               88     12    86%   78-89
...
------------------------------------------------------------------
TOTAL                                 5037   3903    23%
```

**Benefits**:
- ✅ Quick overview in terminal
- ✅ Shows missing line numbers
- ✅ Easy to identify uncovered code

### 3. XML Report (Best for CI/CD)

**Generate**:
```bash
pytest tests/ --cov=src --cov-report=xml
```

**Output**: `coverage.xml`

**Use Cases**:
- Codecov upload
- SonarQube integration
- GitLab CI coverage parsing
- Other CI/CD tools

### 4. JSON Report (Best for automation)

**Generate**:
```bash
pytest tests/ --cov=src --cov-report=json
```

**Output**: `coverage.json`

**Use Cases**:
- Custom coverage analysis scripts
- Coverage trend tracking
- Automated reporting tools
- API integrations

## Current Coverage Status

### Overall Coverage: 23% (Baseline)

**High Coverage (>80%)**:
- ✅ `src/routing/` - 88% (keyword router, LLM router, hybrid router)
- ✅ `src/utils/config.py` - 99% (configuration loading)
- ✅ `src/tools/reranker.py` - 100% (reranker interface)

**Medium Coverage (40-80%)**:
- 🟡 `src/agents/code_agent.py` - 57%
- 🟡 `src/agents/research_agent.py` - 55%
- 🟡 `src/utils/logger.py` - 57%
- 🟡 `src/llm/manager.py` - 55%

**Low Coverage (<40%)**:
- 🔴 `src/tools/` - 13-27% (weather, finance, routing, OCR, vision tools)
- 🔴 `src/agents/rag_agent.py` - 19%
- 🔴 `src/web/` - 0% (requires running server)
- 🔴 `src/workflow/` - 0% (excluded, Phase 7.3)

### Coverage by Module

| Module | Coverage | Priority |
|--------|----------|----------|
| **Core** | | |
| `src/routing/` | 88% | ✅ High |
| `src/llm/` | 55% | 🟡 Medium |
| `src/utils/` | 64% | 🟡 Medium |
| **Agents** | | |
| `src/agents/` | 45% | 🟡 Medium |
| **Tools** | | |
| `src/tools/` | 18% | 🔴 Low (Phase 7.3) |
| **Web** | | |
| `src/web/` | 0% | 🔴 Excluded (API tests) |
| **Workflow** | | |
| `src/workflow/` | 0% | 🔴 Excluded (Phase 7.3) |

## Running Coverage

### Basic Usage

```bash
# Run all tests with coverage
pytest tests/

# Run specific test file with coverage
pytest tests/test_routing.py

# Run specific marker with coverage
pytest tests/ -m unit
```

### Coverage Only (No Tests)

```bash
# Generate coverage report from existing .coverage file
coverage report

# Generate HTML report
coverage html

# Show missing lines
coverage report --show-missing
```

### Advanced Usage

```bash
# Run with specific minimum coverage
pytest tests/ --cov-fail-under=60

# Run with branch coverage
pytest tests/ --cov-branch

# Exclude specific modules
pytest tests/ --cov=src --cov-omit=src/web/*

# Parallel execution with coverage
pytest tests/ -n auto --cov=src

# Run only changed files (requires pytest-testmon)
pip install pytest-testmon
pytest tests/ --testmon
```

## CI/CD Integration

### GitHub Actions

**Workflow file**: `.github/workflows/test.yml`

**Triggers**:
- Push to `main`, `develop`, `fix` branches
- Pull requests to `main`, `develop`

**Jobs**:
```yaml
1. test (matrix: Python 3.10, 3.11, 3.12)
   - Run unit tests in parallel
   - Upload coverage to Codecov
   - Generate coverage badge

2. integration-test (Python 3.12, on push only)
   - Run integration tests (no API keys)
   - Report coverage

3. security-test (Python 3.12)
   - Run security-specific tests
```

**Usage**:
```bash
# Local simulation
act  # Run GitHub Actions locally (requires act CLI)

# View workflow logs
# Go to: https://github.com/your-repo/actions
```

### Codecov Integration

**Setup**:
1. Sign up at https://codecov.io
2. Connect your GitHub repository
3. Get upload token (optional for public repos)
4. Add to GitHub Secrets: `CODECOV_TOKEN`

**Features**:
- Coverage tracking over time
- Pull request comments with coverage diff
- Coverage badges
- Detailed coverage reports
- Sunburst charts

**Badge**:
```markdown
[![codecov](https://codecov.io/gh/your-username/ai_search/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/ai_search)
```

## Coverage Badges

### Local Badge Generation

```bash
# Install coverage-badge
pip install coverage-badge

# Generate badge
coverage-badge -o coverage.svg -f

# Use in README
![Coverage](./coverage.svg)
```

### CI-Generated Badge

**GitHub Actions** automatically generates `coverage.svg` on Python 3.12 tests.

**Add to README.md**:
```markdown
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/your-username/gist-id/raw/coverage.json)
```

## Coverage Goals

### Phase 7.2 (Current): Setup
- ✅ Coverage configuration (`.coveragerc`)
- ✅ Pytest integration (`pytest.ini`)
- ✅ CI/CD workflow (`.github/workflows/test.yml`)
- ✅ Multiple report formats (HTML, XML, JSON, terminal)
- ✅ Codecov integration
- ✅ Coverage badges

### Phase 7.3: Increase Coverage
- 🎯 Target: 60% overall coverage
- 🎯 Core modules (routing, LLM, agents): 80%+
- 🎯 Tools (weather, finance, OCR, etc.): 50%+
- 🎯 Workflow: 60%+

### Phase 7.4: Maintain Coverage
- 🎯 Enable `--cov-fail-under=60` in pytest.ini
- 🎯 Pre-commit hook for coverage check
- 🎯 Coverage trend tracking
- 🎯 Regular coverage reviews

## Best Practices

### 1. Write Tests First (TDD)
```python
# Write test
def test_feature():
    result = my_feature()
    assert result == expected

# Run with coverage
pytest test_my_feature.py --cov=src.my_module

# Implement feature until test passes
```

### 2. Focus on High-Value Code
- Core logic (routing, agents, tools)
- Security-critical code (code executor, validators)
- Error handling paths
- Edge cases

### 3. Skip Low-Value Code
```python
# Use pragma: no cover for:
# - Debug code
# - Development utilities
# - Abstract methods
# - Type checking blocks

if __name__ == "__main__":  # pragma: no cover
    debug_function()
```

### 4. Review Coverage Reports
```bash
# After every test run, check:
pytest tests/ --cov=src --cov-report=term-missing

# Look for:
# - Missing critical code paths
# - Untested error handling
# - Low-coverage modules
```

### 5. Track Coverage Trends
```bash
# Save coverage percentage
coverage report | grep TOTAL | awk '{print $4}' > coverage.txt

# Compare with previous run
diff coverage.txt coverage_previous.txt
```

## Troubleshooting

### Issue: Coverage shows 0%
**Cause**: Source path not configured correctly

**Fix**:
```bash
# Ensure pytest is run from project root
cd /path/to/ai_search
pytest tests/

# Or specify source explicitly
pytest tests/ --cov=src --cov-config=.coveragerc
```

### Issue: Tests not discovered
**Cause**: Missing `conftest.py` or sys.path not set

**Fix**:
```python
# In conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: Coverage excludes important code
**Cause**: Incorrect omit patterns in `.coveragerc`

**Fix**:
```ini
[run]
omit =
    */tests/*  # Use wildcards carefully
    # Comment out lines to include them:
    # src/web/*
```

### Issue: CI/CD workflow fails
**Cause**: Missing dependencies or API keys

**Fix**:
```yaml
# In .github/workflows/test.yml
env:
  DASHSCOPE_API_KEY: test_key_for_ci  # Dummy key for CI
  LOG_LEVEL: WARNING  # Reduce log noise
```

## Next Steps

### Phase 7.3: Add Missing Unit Tests
1. Add tests for tools: VectorStore, DocumentProcessor, WeatherTool, FinanceTool
2. Add tests for agents: RAGAgent, ChatAgent
3. Add tests for workflow: ResultAggregator, TaskDecomposer

### Phase 7.4: Create Load Tests
1. Web API performance tests
2. Concurrent request handling
3. Rate limiting validation

## References

- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **coverage.py**: https://coverage.readthedocs.io/
- **Codecov**: https://docs.codecov.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Coverage badges**: https://github.com/dbrgn/coverage-badge

## Conclusion

✅ **Phase 7.2 completed successfully**

- Coverage configuration: `.coveragerc`, `pytest.ini`
- CI/CD workflow: `.github/workflows/test.yml`
- Multiple report formats: HTML, XML, JSON, terminal
- Codecov integration: Automatic upload
- Coverage badges: Automatic generation

**Current baseline**: 23% overall coverage
**Phase 7.3 target**: 60% overall coverage

All coverage infrastructure in place. Ready to add missing unit tests in Phase 7.3.
