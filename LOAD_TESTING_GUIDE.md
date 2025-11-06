# Load Testing Guide

**Date**: 2025-11-05
**Phase**: 7.4 - Load Tests
**Status**: ✅ COMPLETED

## Overview

Comprehensive load and performance testing suite for the AI Search Engine, covering:
- ✅ Performance benchmarks (response times, throughput)
- ✅ Concurrent load tests (multiple simultaneous requests)
- ✅ Memory and resource usage tests
- ✅ Stress tests (rapid-fire, large documents)
- ✅ Cache performance tests
- ✅ API load tests (requires running server)
- ✅ Rate limiting tests
- ✅ Sustained load tests
- ✅ Spike tests (sudden traffic increases)
- ✅ Response time percentile tests

## Test Files

### 1. `test_performance.py` - Performance & Benchmarks

**Purpose**: Unit-level performance testing for core components

**Test Classes**:
- `TestPerformanceBenchmarks` - Benchmark core components
- `TestConcurrentLoad` - Concurrent request handling
- `TestResourceUsage` - Memory and resource tests
- `TestStressConditions` - Stress testing
- `TestCachePerformance` - Cache effectiveness

**Total**: 15 tests

### 2. `test_load.py` - API Load Tests

**Purpose**: Integration-level load testing for web API

**Test Classes**:
- `TestBasicLoad` - Basic endpoint load tests
- `TestRateLimiting` - Rate limit enforcement
- `TestSustainedLoad` - Sustained traffic over time
- `TestSpikeLoad` - Sudden traffic spikes
- `TestResponseTimes` - Response time analysis
- `TestErrorRates` - Error rate monitoring

**Total**: 12 tests

**Note**: Requires web server running: `python -m src.web.app`

## Installation

```bash
# Install performance testing dependencies
pip install pytest-benchmark pytest-timeout psutil

# Verify installation
pip list | grep -E "pytest-benchmark|pytest-timeout|psutil"
```

## Running Tests

### Performance Tests

```bash
# Run all performance tests
pytest tests/test_performance.py -v -s

# Run specific test class
pytest tests/test_performance.py::TestPerformanceBenchmarks -v

# Run with benchmark comparison
pytest tests/test_performance.py --benchmark-only

# Save benchmark results
pytest tests/test_performance.py --benchmark-save=baseline

# Compare with baseline
pytest tests/test_performance.py --benchmark-compare=baseline
```

### Load Tests

**Important**: Start web server first!

```bash
# Terminal 1: Start web server
python -m src.web.app

# Terminal 2: Run load tests
pytest tests/test_load.py -v -s

# Run specific load test
pytest tests/test_load.py::TestBasicLoad -v

# Run without rate limiting tests (slow)
pytest tests/test_load.py -v -k "not rate_limit"
```

### All Load Tests

```bash
# Run all performance and load tests (slow)
pytest tests/ -m slow -v -s

# Skip slow tests in regular test runs
pytest tests/ -m "not slow"
```

## Test Details

### Performance Benchmarks

#### 1. Router Classification Speed
**File**: `test_performance.py::TestPerformanceBenchmarks::test_router_classification_speed`

**What it tests**:
- Router query classification speed
- Keyword-based routing performance

**Expected**:
- Mean time < 100ms per classification
- Throughput > 50 queries/second

**Example output**:
```
Router throughput: 127.3 queries/second
test_router_classification_speed (0001_baseline)
Mean: 7.85ms, Median: 7.23ms, StdDev: 2.14ms
```

#### 2. Vector Search Speed
**File**: `test_performance.py::TestPerformanceBenchmarks::test_vector_search_speed`

**What it tests**:
- Vector similarity search performance
- Search over 100 documents

**Expected**:
- Mean time < 500ms for k=10 search
- Cached queries significantly faster

**Example output**:
```
test_vector_search_speed (0001_baseline)
Mean: 234.5ms, Median: 221.3ms, StdDev: 45.2ms
```

#### 3. Code Execution Speed
**File**: `test_performance.py::TestPerformanceBenchmarks::test_code_execution_speed`

**What it tests**:
- Python code execution performance
- Subprocess sandbox overhead

**Expected**:
- Mean time < 2s for simple code
- Validation overhead < 100ms

#### 4. Router Throughput
**File**: `test_performance.py::TestPerformanceBenchmarks::test_router_throughput`

**What it tests**:
- Concurrent query classification
- 50 queries processed in parallel

**Expected**:
- Throughput > 50 queries/second
- All queries classified correctly

**Example output**:
```
Router throughput: 89.4 queries/second
```

### Concurrent Load Tests

#### 5. Concurrent Routing
**File**: `test_performance.py::TestConcurrentLoad::test_concurrent_routing`

**What it tests**:
- 100 concurrent routing requests
- System behavior under concurrent load

**Expected**:
- All requests succeed
- Total time < 5s
- Average < 50ms per request

**Example output**:
```
100 concurrent routing requests: 1.86s
Average: 18.6ms per request
```

#### 6. Concurrent Vector Search
**File**: `test_performance.py::TestConcurrentLoad::test_concurrent_vector_search`

**What it tests**:
- 50 concurrent vector searches
- Thread pool performance (CPU-bound)

**Expected**:
- All searches return results
- Reasonable parallelization

**Example output**:
```
50 concurrent vector searches: 3.42s
Average: 68.4ms per search
```

#### 7. Concurrent Code Execution
**File**: `test_performance.py::TestConcurrentLoad::test_concurrent_code_execution`

**What it tests**:
- 20 concurrent code executions
- Subprocess pool behavior

**Expected**:
- Success rate ≥ 75%
- No resource exhaustion

**Example output**:
```
20 concurrent code executions: 4.21s
Success rate: 18/20
```

### Resource Usage Tests

#### 8. Vector Store Memory Usage
**File**: `test_performance.py::TestResourceUsage::test_vector_store_memory_usage`

**What it tests**:
- Memory usage with 1000 documents
- Embedding model memory footprint

**Expected**:
- Memory increase < 500MB
- No memory leaks

**Example output**:
```
Memory usage for 1000 documents: 234.5MB
```

#### 9. Router Memory Leak Detection
**File**: `test_performance.py::TestResourceUsage::test_router_memory_leak`

**What it tests**:
- Memory leaks in router after 1000 calls
- Long-running process stability

**Expected**:
- Memory increase < 50MB
- No accumulation over time

**Example output**:
```
Memory increase after 1000 routing calls: 12.3MB
```

### Stress Tests

#### 10. Rapid-Fire Requests
**File**: `test_performance.py::TestStressConditions::test_rapid_fire_requests`

**What it tests**:
- 500 requests as fast as possible
- System stability under stress

**Expected**:
- Success rate ≥ 90%
- No crashes or deadlocks

**Example output**:
```
500 rapid-fire requests: 4.56s
Success rate: 478/500
Throughput: 104.8 req/s
```

#### 11. Large Document Processing
**File**: `test_performance.py::TestStressConditions::test_large_document_processing`

**What it tests**:
- Processing 1MB text file
- Document processor performance

**Expected**:
- Completes successfully
- Processing time < 5s

**Example output**:
```
1MB document processing: 2.34s
```

#### 12. Large Query Results
**File**: `test_performance.py::TestStressConditions::test_vector_store_large_query_result`

**What it tests**:
- Returning top 500 results from 1000 docs
- Result set handling

**Expected**:
- Returns results
- Query time < 2s

**Example output**:
```
Vector search (k=500 from 1000 docs): 1.23s
```

### Cache Performance Tests

#### 13. Vector Store Cache Hit Performance
**File**: `test_performance.py::TestCachePerformance::test_vector_store_cache_hit`

**What it tests**:
- Query cache effectiveness
- Cache hit vs cache miss performance

**Expected**:
- Cache hit ≥ 2x faster than cache miss
- Identical results

**Example output**:
```
Cache performance:
  First query (miss): 234.5ms
  Second query (hit): 12.3ms
  Speedup: 19.1x
```

### API Load Tests

#### 14. Health Endpoint Load
**File**: `test_load.py::TestBasicLoad::test_health_endpoint_load`

**What it tests**:
- 100 concurrent requests to /health
- Basic API responsiveness

**Expected**:
- Success rate ≥ 95%
- Total time < 2s

**Example output**:
```
100 concurrent /health requests: 0.87s
Success rate: 98/100
Average: 8.7ms per request
```

#### 15. Homepage Load
**File**: `test_load.py::TestBasicLoad::test_homepage_load`

**What it tests**:
- 50 concurrent requests to homepage
- HTML rendering under load

**Expected**:
- Success rate ≥ 90%
- No server errors

**Example output**:
```
50 concurrent homepage requests: 2.34s
Success rate: 47/50
```

#### 16. Classification Endpoint Load
**File**: `test_load.py::TestBasicLoad::test_classification_endpoint_load`

**What it tests**:
- 50 concurrent POST requests to /classify
- Router performance via API

**Expected**:
- Success rate ≥ 90%
- Throughput measured

**Example output**:
```
50 classification requests: 3.21s
Success rate: 48/50
Throughput: 15.0 req/s
```

### Rate Limiting Tests

#### 17. Rate Limit Enforcement
**File**: `test_load.py::TestRateLimiting::test_rate_limit_enforcement`

**What it tests**:
- Rate limit triggers correctly
- 429 responses when exceeded

**Expected**:
- Some 429 responses if rate limiting enabled
- Graceful handling

**Example output**:
```
35 rapid requests:
  200 OK: 30
  429 Rate Limited: 5
```

#### 18. Rate Limit Recovery
**File**: `test_load.py::TestRateLimiting::test_rate_limit_recovery`

**What it tests**:
- System recovers after rate limit window
- Rate limit window reset (60s)

**Expected**:
- Requests work again after window resets
- No permanent blocking

**Note**: This test takes 60+ seconds to complete

### Sustained Load Tests

#### 19. Sustained Requests
**File**: `test_load.py::TestSustainedLoad::test_sustained_requests`

**What it tests**:
- 5 req/s for 30 seconds
- System stability over time

**Expected**:
- Success rate ≥ 90%
- Consistent performance

**Example output**:
```
Sustained load test:
  Duration: 30.2s
  Total requests: 150
  Successful: 147
  Success rate: 98.0%
  Actual rate: 4.97 req/s
```

### Spike Tests

#### 20. Sudden Spike
**File**: `test_load.py::TestSpikeLoad::test_sudden_spike`

**What it tests**:
- Normal load → sudden spike → recovery
- System resilience to traffic bursts

**Test phases**:
1. Normal: 5 req/s for 10s
2. Spike: 50 concurrent requests
3. Recovery: 5 req/s for 10s

**Expected**:
- Spike: ≥ 80% success
- Recovery: ≥ 90% success

**Example output**:
```
Phase 1: Normal load (5 req/s for 10s)
  Success: 49/50

Phase 2: Sudden spike (50 concurrent)
  Success: 42/50
  Duration: 1.23s

Phase 3: Recovery (5 req/s for 10s)
  Success: 48/50
```

### Response Time Tests

#### 21. Response Time Percentiles
**File**: `test_load.py::TestResponseTimes::test_response_time_percentiles`

**What it tests**:
- Response time distribution (P50, P90, P95, P99)
- Performance consistency

**Expected**:
- P95 < 500ms
- Consistent performance

**Example output**:
```
Response time percentiles (ms):
  P50: 45.3ms
  P90: 123.7ms
  P95: 234.5ms
  P99: 456.2ms
```

### Error Rate Tests

#### 22. Error Rate Under Load
**File**: `test_load.py::TestErrorRates::test_error_rate_under_load`

**What it tests**:
- 200 concurrent requests
- Server error rate monitoring

**Expected**:
- Error rate < 5%
- Few/no 5xx errors

**Example output**:
```
200 concurrent requests:
  200 OK: 192
  4xx Client Error: 3
  5xx Server Error: 2
  Network Error: 3
  Error rate: 2.5%
```

## Performance Targets

### Response Times
| Endpoint | Target | Stretch Goal |
|----------|--------|--------------|
| /health | < 50ms | < 20ms |
| / (homepage) | < 200ms | < 100ms |
| /classify | < 100ms | < 50ms |
| /query (research) | < 5s | < 3s |
| /query (code) | < 3s | < 2s |

### Throughput
| Component | Target | Stretch Goal |
|-----------|--------|--------------|
| Router | > 50 q/s | > 100 q/s |
| Vector Search | > 10 q/s | > 20 q/s |
| Code Execution | > 5 exec/s | > 10 exec/s |

### Resource Usage
| Resource | Target | Max Limit |
|----------|--------|-----------|
| Memory (1000 docs) | < 300MB | < 500MB |
| Memory (1000 routes) | < 30MB | < 50MB |
| CPU (idle) | < 10% | < 20% |

### Reliability
| Metric | Target | Critical |
|--------|--------|----------|
| Success rate (normal) | > 95% | > 90% |
| Success rate (spike) | > 80% | > 70% |
| Error rate | < 5% | < 10% |

## Interpreting Results

### Good Performance Indicators
- ✅ Response times within targets
- ✅ High success rates (>95%)
- ✅ Low error rates (<5%)
- ✅ Linear scaling with load
- ✅ Fast cache hit times
- ✅ Stable memory usage

### Warning Signs
- ⚠️ Increasing response times with load
- ⚠️ Success rate drops below 90%
- ⚠️ Memory usage grows unbounded
- ⚠️ Many 5xx server errors
- ⚠️ Degraded performance after spikes

### Critical Issues
- 🔴 Response times > 10x targets
- 🔴 Success rate < 70%
- 🔴 Server crashes or hangs
- 🔴 Memory leaks (continuous growth)
- 🔴 Error rate > 10%

## Optimization Recommendations

### If Router is Slow
1. Switch to keyword router (fastest)
2. Increase confidence threshold for hybrid router
3. Cache classification results
4. Optimize keyword patterns

### If Vector Search is Slow
1. Reduce embedding dimension
2. Enable query caching
3. Limit top_k results
4. Use approximate search

### If API is Slow
1. Enable response caching
2. Optimize database queries
3. Add connection pooling
4. Use CDN for static files

### If Memory Usage is High
1. Reduce cache sizes
2. Limit concurrent requests
3. Enable periodic garbage collection
4. Use smaller embedding models

## CI/CD Integration

### GitHub Actions Workflow

Add performance tests to `.github/workflows/test.yml`:

```yaml
performance-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run performance tests
      run: |
        pytest tests/test_performance.py -v --benchmark-only
    - name: Save benchmark results
      run: |
        pytest tests/test_performance.py --benchmark-save=ci_${{ github.run_number }}
```

### Scheduled Load Tests

Run load tests on schedule:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      # Start web server
      - name: Start web server
        run: |
          python -m src.web.app &
          sleep 5
      # Run load tests
      - name: Run load tests
        run: |
          pytest tests/test_load.py -v
```

## Monitoring Integration

### Prometheus Metrics

Export performance metrics:

```python
from prometheus_client import Histogram, Counter

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

request_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
```

### Grafana Dashboards

Create dashboards for:
- Response time percentiles (P50, P90, P95, P99)
- Request rate (req/s)
- Error rate (%)
- Memory usage (MB)
- CPU usage (%)

## Troubleshooting

### Tests Fail with Connection Errors
**Problem**: Cannot connect to localhost:8000

**Solution**:
```bash
# Start web server first
python -m src.web.app

# In another terminal, run tests
pytest tests/test_load.py
```

### Tests Timeout
**Problem**: Tests take too long and timeout

**Solution**:
```bash
# Increase timeout
pytest tests/test_load.py --timeout=300

# Or skip slow tests
pytest tests/ -m "not slow"
```

### Memory Tests Fail
**Problem**: psutil not installed

**Solution**:
```bash
pip install psutil
```

### Benchmark Tests Fail
**Problem**: pytest-benchmark not installed

**Solution**:
```bash
pip install pytest-benchmark
```

## Next Steps

1. ✅ Run baseline performance tests
2. ✅ Establish performance targets
3. ⏳ Monitor performance over time
4. ⏳ Optimize slow components
5. ⏳ Add more specific load tests
6. ⏳ Integrate with monitoring tools

## Conclusion

✅ **Phase 7.4 completed successfully!**

**Created**:
- `test_performance.py` - 15 performance & benchmark tests
- `test_load.py` - 12 API load tests
- `LOAD_TESTING_GUIDE.md` - This comprehensive guide

**Coverage**:
- Performance benchmarks (router, vector search, code execution)
- Concurrent load tests (100+ concurrent requests)
- Resource usage tests (memory, CPU)
- Stress tests (rapid-fire, large data)
- Cache performance tests
- API load tests (requires running server)
- Rate limiting tests
- Sustained load tests
- Spike tests
- Response time analysis
- Error rate monitoring

**Total**: 27 new performance and load tests

All load testing infrastructure is now complete! 🚀
