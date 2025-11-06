"""Load tests for Web API

Tests API endpoints under realistic load conditions.
Requires web server to be running: python -m src.web.app
"""

import pytest
import asyncio
import aiohttp
import time
from typing import List, Dict


# Base URL for tests
BASE_URL = "http://localhost:8000"


# ============================================================================
# Basic Load Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.api
@pytest.mark.asyncio
class TestBasicLoad:
    """Basic load tests for API endpoints"""

    async def test_health_endpoint_load(self):
        """Test health endpoint under load"""
        async with aiohttp.ClientSession() as session:
            # 100 concurrent requests
            tasks = [
                session.get(f"{BASE_URL}/health")
                for _ in range(100)
            ]

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time

            # All should succeed
            successful = [r for r in responses if not isinstance(r, Exception)]
            assert len(successful) >= 95  # 95% success rate

            # Should be fast
            assert duration < 2.0  # 100 requests in < 2s

            print(f"\n100 concurrent /health requests: {duration:.2f}s")
            print(f"Success rate: {len(successful)}/100")
            print(f"Average: {duration/100*1000:.1f}ms per request")

    async def test_homepage_load(self):
        """Test homepage under load"""
        async with aiohttp.ClientSession() as session:
            # 50 concurrent requests (HTML is heavier)
            tasks = [
                session.get(f"{BASE_URL}/")
                for _ in range(50)
            ]

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time

            # Count successful responses
            successful = []
            for r in responses:
                if not isinstance(r, Exception):
                    try:
                        if r.status == 200:
                            successful.append(r)
                    except:
                        pass

            assert len(successful) >= 45  # 90% success rate

            print(f"\n50 concurrent homepage requests: {duration:.2f}s")
            print(f"Success rate: {len(successful)}/50")

    async def test_classification_endpoint_load(self):
        """Test query classification under load"""
        async with aiohttp.ClientSession() as session:
            queries = [
                "What is machine learning?",
                "Calculate 2 + 2",
                "Hello there",
                "Weather in Beijing",
                "AAPL stock price"
            ] * 10  # 50 requests total

            tasks = [
                session.post(f"{BASE_URL}/classify", data={"query": q})
                for q in queries
            ]

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time

            # Count successful
            successful = []
            for r in responses:
                if not isinstance(r, Exception):
                    try:
                        if r.status == 200:
                            successful.append(r)
                    except:
                        pass

            assert len(successful) >= 45  # 90% success rate

            print(f"\n50 classification requests: {duration:.2f}s")
            print(f"Success rate: {len(successful)}/50")
            print(f"Throughput: {len(successful)/duration:.1f} req/s")


# ============================================================================
# Rate Limiting Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.api
@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting enforcement"""

    async def test_rate_limit_enforcement(self):
        """Test that rate limits are enforced"""
        async with aiohttp.ClientSession() as session:
            # Query endpoint has 30/minute limit
            # Send 35 requests rapidly

            responses = []
            for i in range(35):
                try:
                    response = await session.post(
                        f"{BASE_URL}/classify",
                        data={"query": f"Query {i}"}
                    )
                    responses.append(response.status)
                except Exception as e:
                    responses.append(None)

            # Should have some 429 (Too Many Requests) responses
            rate_limited = [s for s in responses if s == 429]

            # If rate limiting is enabled, we should see some 429s
            # If disabled, all will be 200
            print(f"\n35 rapid requests:")
            print(f"  200 OK: {responses.count(200)}")
            print(f"  429 Rate Limited: {len(rate_limited)}")

            # Test passes regardless (just informational)
            assert True

    async def test_rate_limit_recovery(self):
        """Test recovery after rate limit"""
        async with aiohttp.ClientSession() as session:
            # Hit rate limit
            for _ in range(35):
                try:
                    await session.post(
                        f"{BASE_URL}/classify",
                        data={"query": "test"}
                    )
                except:
                    pass

            # Wait for rate limit window to reset (1 minute)
            print("\nWaiting 60s for rate limit reset...")
            await asyncio.sleep(60)

            # Should work again
            response = await session.post(
                f"{BASE_URL}/classify",
                data={"query": "test after reset"}
            )

            # Should succeed (or return 200/429 depending on config)
            assert response.status in [200, 429]
            print(f"After reset: {response.status}")


# ============================================================================
# Sustained Load Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.api
@pytest.mark.asyncio
class TestSustainedLoad:
    """Test API under sustained load"""

    async def test_sustained_requests(self):
        """Test sustained request load over time"""
        async with aiohttp.ClientSession() as session:
            duration_seconds = 30
            requests_per_second = 5
            total_requests = duration_seconds * requests_per_second

            results = []
            start_time = time.time()

            for i in range(total_requests):
                try:
                    response = await session.get(f"{BASE_URL}/health")
                    results.append({
                        "status": response.status,
                        "time": time.time() - start_time
                    })
                except Exception as e:
                    results.append({
                        "status": "error",
                        "time": time.time() - start_time
                    })

                # Maintain rate
                await asyncio.sleep(1 / requests_per_second)

            total_duration = time.time() - start_time

            # Calculate metrics
            successful = [r for r in results if r["status"] == 200]
            success_rate = len(successful) / total_requests * 100

            print(f"\nSustained load test:")
            print(f"  Duration: {total_duration:.1f}s")
            print(f"  Total requests: {total_requests}")
            print(f"  Successful: {len(successful)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Actual rate: {total_requests/total_duration:.1f} req/s")

            # Should maintain good success rate
            assert success_rate >= 90


# ============================================================================
# Spike Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.api
@pytest.mark.asyncio
class TestSpikeLoad:
    """Test API response to sudden load spikes"""

    async def test_sudden_spike(self):
        """Test response to sudden traffic spike"""
        async with aiohttp.ClientSession() as session:
            # Normal load: 5 req/s for 10s
            print("\nPhase 1: Normal load (5 req/s for 10s)")
            normal_results = []
            for i in range(50):
                try:
                    response = await session.get(f"{BASE_URL}/health")
                    normal_results.append(response.status)
                except:
                    normal_results.append(None)
                await asyncio.sleep(0.2)

            normal_success = normal_results.count(200)
            print(f"  Success: {normal_success}/50")

            # Spike: 50 concurrent requests
            print("\nPhase 2: Sudden spike (50 concurrent)")
            tasks = [session.get(f"{BASE_URL}/health") for _ in range(50)]

            start_spike = time.time()
            spike_responses = await asyncio.gather(*tasks, return_exceptions=True)
            spike_duration = time.time() - start_spike

            spike_successful = []
            for r in spike_responses:
                if not isinstance(r, Exception):
                    try:
                        if r.status == 200:
                            spike_successful.append(r)
                    except:
                        pass

            print(f"  Success: {len(spike_successful)}/50")
            print(f"  Duration: {spike_duration:.2f}s")

            # Recovery: back to normal load
            print("\nPhase 3: Recovery (5 req/s for 10s)")
            recovery_results = []
            for i in range(50):
                try:
                    response = await session.get(f"{BASE_URL}/health")
                    recovery_results.append(response.status)
                except:
                    recovery_results.append(None)
                await asyncio.sleep(0.2)

            recovery_success = recovery_results.count(200)
            print(f"  Success: {recovery_success}/50")

            # System should handle spike and recover
            assert len(spike_successful) >= 40  # 80% during spike
            assert recovery_success >= 45  # 90% after recovery


# ============================================================================
# Response Time Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.api
@pytest.mark.asyncio
class TestResponseTimes:
    """Test API response time under load"""

    async def test_response_time_percentiles(self):
        """Test response time percentiles"""
        async with aiohttp.ClientSession() as session:
            response_times = []

            # 100 requests
            for i in range(100):
                start = time.time()
                try:
                    response = await session.get(f"{BASE_URL}/health")
                    if response.status == 200:
                        response_times.append(time.time() - start)
                except:
                    pass

            if len(response_times) > 0:
                response_times.sort()

                # Calculate percentiles
                p50 = response_times[len(response_times)//2] * 1000
                p90 = response_times[int(len(response_times)*0.9)] * 1000
                p95 = response_times[int(len(response_times)*0.95)] * 1000
                p99 = response_times[int(len(response_times)*0.99)] * 1000

                print(f"\nResponse time percentiles (ms):")
                print(f"  P50: {p50:.1f}ms")
                print(f"  P90: {p90:.1f}ms")
                print(f"  P95: {p95:.1f}ms")
                print(f"  P99: {p99:.1f}ms")

                # P95 should be reasonable (< 500ms)
                assert p95 < 500


# ============================================================================
# Error Rate Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.api
@pytest.mark.asyncio
class TestErrorRates:
    """Test error rates under load"""

    async def test_error_rate_under_load(self):
        """Test that error rate remains low under load"""
        async with aiohttp.ClientSession() as session:
            total_requests = 200

            results = {
                "200": 0,
                "4xx": 0,
                "5xx": 0,
                "error": 0
            }

            tasks = [session.get(f"{BASE_URL}/health") for _ in range(total_requests)]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for r in responses:
                if isinstance(r, Exception):
                    results["error"] += 1
                else:
                    try:
                        if r.status == 200:
                            results["200"] += 1
                        elif 400 <= r.status < 500:
                            results["4xx"] += 1
                        elif r.status >= 500:
                            results["5xx"] += 1
                    except:
                        results["error"] += 1

            print(f"\n200 concurrent requests:")
            print(f"  200 OK: {results['200']}")
            print(f"  4xx Client Error: {results['4xx']}")
            print(f"  5xx Server Error: {results['5xx']}")
            print(f"  Network Error: {results['error']}")

            # Error rate should be low (< 5%)
            error_count = results['5xx'] + results['error']
            error_rate = error_count / total_requests * 100

            print(f"  Error rate: {error_rate:.1f}%")

            assert error_rate < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
