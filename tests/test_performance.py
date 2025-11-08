"""Performance and load tests for AI Search Engine

Tests response times, throughput, and resource usage under load.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

from src.tools import VectorStore, CodeExecutor
from src.routing import create_router, TaskType
from src.llm import LLMManager
from src.utils import get_config


# ============================================================================
# Performance Benchmarks
# ============================================================================

@pytest.mark.slow
@pytest.mark.unit
class TestPerformanceBenchmarks:
    """Performance benchmarks for core components"""

    @pytest.fixture
    def config(self):
        """Get configuration"""
        return get_config()

    @pytest.fixture
    def llm_manager(self, config):
        """Get LLM manager"""
        return LLMManager(config=config)

    def test_router_classification_speed(self, config, llm_manager, benchmark):
        """Benchmark router classification speed"""
        router = create_router(config, llm_manager, router_type='keyword')

        def classify_query():
            return asyncio.run(router.route("What is Python programming?"))

        result = benchmark(classify_query)

        # Should be fast (< 100ms for keyword router)
        assert benchmark.stats['mean'] < 0.1  # 100ms

    def test_vector_search_speed(self, tmp_path, benchmark):
        """Benchmark vector search speed"""
        vector_store = VectorStore(
            persist_directory=str(tmp_path / "bench_vector"),
            collection_name="bench"
        )

        # Add documents
        texts = [f"Document {i} with some content" for i in range(100)]
        vector_store.add_documents(
            texts=texts,
            ids=[f"id{i}" for i in range(100)]
        )

        def search():
            return vector_store.similarity_search("Document content", k=10)

        result = benchmark(search)

        # Should be reasonably fast (< 500ms for 100 docs)
        assert benchmark.stats['mean'] < 0.5

    @pytest.mark.asyncio
    async def test_code_execution_speed(self, benchmark):
        """Benchmark code execution speed"""
        executor = CodeExecutor(
            timeout=5,
            enable_docker=False,
            enable_validation=True
        )

        code = "result = sum(range(100))\nprint(result)"

        def execute():
            return asyncio.run(executor.execute(code))

        result = benchmark(execute)

        # Code execution should be reasonably fast (< 2s)
        assert benchmark.stats['mean'] < 2.0

    def test_router_throughput(self, config, llm_manager):
        """Test router throughput (queries per second)"""
        router = create_router(config, llm_manager, router_type='keyword')

        queries = [
            "What is Python?",
            "Calculate 2 + 2",
            "Hello there",
            "Weather in Beijing",
            "Stock price of AAPL"
        ] * 10  # 50 queries total

        start_time = time.time()

        async def classify_all():
            tasks = [router.route(q) for q in queries]
            return await asyncio.gather(*tasks)

        results = asyncio.run(classify_all())

        end_time = time.time()
        duration = end_time - start_time
        throughput = len(queries) / duration

        # Should handle at least 50 queries/second
        assert throughput > 50
        print(f"\nRouter throughput: {throughput:.1f} queries/second")


# ============================================================================
# Concurrent Load Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.integration
class TestConcurrentLoad:
    """Test system behavior under concurrent load"""

    @pytest.fixture
    def config(self):
        """Get configuration"""
        return get_config()

    @pytest.fixture
    def llm_manager(self, config):
        """Get LLM manager"""
        return LLMManager(config=config)

    @pytest.mark.asyncio
    async def test_concurrent_routing(self, config, llm_manager):
        """Test concurrent routing requests"""
        router = create_router(config, llm_manager, router_type='keyword')

        # 100 concurrent queries
        queries = [
            "What is machine learning?",
            "Calculate 10 * 5",
            "Hello",
            "Weather today",
            "AAPL stock"
        ] * 20

        start_time = time.time()

        # Execute concurrently
        tasks = [router.route(q) for q in queries]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All should succeed
        assert len(results) == 100
        assert all(r.primary_task_type is not None for r in results)

        # Should handle 100 concurrent requests reasonably fast (< 5s)
        assert duration < 5.0

        print(f"\n100 concurrent routing requests: {duration:.2f}s")
        print(f"Average: {duration/100*1000:.1f}ms per request")

    @pytest.mark.asyncio
    async def test_concurrent_vector_search(self, tmp_path):
        """Test concurrent vector searches"""
        vector_store = VectorStore(
            persist_directory=str(tmp_path / "concurrent_vector"),
            collection_name="concurrent"
        )

        # Add documents
        texts = [f"Document {i} about topic {i%10}" for i in range(100)]
        vector_store.add_documents(texts=texts, ids=[f"id{i}" for i in range(100)])

        # 50 concurrent searches
        queries = [f"topic {i}" for i in range(50)]

        start_time = time.time()

        # Execute searches concurrently using threads (vector search is CPU-bound)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(vector_store.similarity_search, q, 5)
                for q in queries
            ]
            results = [f.result() for f in futures]

        end_time = time.time()
        duration = end_time - start_time

        # All should return results
        assert len(results) == 50
        assert all(len(r) > 0 for r in results)

        print(f"\n50 concurrent vector searches: {duration:.2f}s")
        print(f"Average: {duration/50*1000:.1f}ms per search")

    @pytest.mark.asyncio
    async def test_concurrent_code_execution(self):
        """Test concurrent code executions"""
        executor = CodeExecutor(
            timeout=5,
            enable_docker=False,
            enable_validation=True
        )

        # Different code snippets
        code_snippets = [
            "print(2 + 2)",
            "print(sum(range(10)))",
            "print('Hello')",
            "x = 10; print(x * 2)",
            "import math; print(math.pi)"
        ] * 4  # 20 executions

        start_time = time.time()

        # Execute concurrently
        tasks = [executor.execute(code) for code in code_snippets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Most should succeed (some may fail validation)
        successful = [r for r in results if isinstance(r, dict) and r.get('success')]
        assert len(successful) >= 15  # At least 75% success

        print(f"\n20 concurrent code executions: {duration:.2f}s")
        print(f"Success rate: {len(successful)}/20")


# ============================================================================
# Memory and Resource Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.unit
class TestResourceUsage:
    """Test memory and resource usage"""

    def test_vector_store_memory_usage(self, tmp_path):
        """Test vector store memory usage with large dataset"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        vector_store = VectorStore(
            persist_directory=str(tmp_path / "memory_test"),
            collection_name="memory"
        )

        # Add 1000 documents
        texts = [f"Document {i} " * 20 for i in range(1000)]  # ~20 words each
        vector_store.add_documents(texts=texts, ids=[f"id{i}" for i in range(1000)])

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 500MB)
        assert memory_increase < 500

        print(f"\nMemory usage for 1000 documents: {memory_increase:.1f}MB")

    @pytest.mark.asyncio
    async def test_router_memory_leak(self, config):
        """Test router for memory leaks"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Create router without LLM to avoid LLM memory
        from src.routing import KeywordRouter
        router = KeywordRouter()

        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Route 1000 queries
        for i in range(1000):
            await router.route(f"Query number {i}")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory should not increase significantly (< 50MB)
        assert memory_increase < 50

        print(f"\nMemory increase after 1000 routing calls: {memory_increase:.1f}MB")


# ============================================================================
# Stress Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.integration
class TestStressConditions:
    """Test system under stress conditions"""

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, config):
        """Test rapid-fire requests without delay"""
        from src.routing import KeywordRouter
        router = KeywordRouter()

        # 500 requests as fast as possible
        queries = [f"Query {i}" for i in range(500)]

        start_time = time.time()

        # No delay between requests
        tasks = [router.route(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Should handle all requests
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 450  # At least 90% success

        print(f"\n500 rapid-fire requests: {duration:.2f}s")
        print(f"Success rate: {len(successful)}/500")
        print(f"Throughput: {len(successful)/duration:.1f} req/s")

    def test_large_document_processing(self, tmp_path):
        """Test processing very large documents"""
        from src.tools import DocumentProcessor

        processor = DocumentProcessor()

        # Create large text file (1MB)
        large_file = tmp_path / "large.txt"
        large_text = "This is a test document. " * 50000  # ~1MB
        large_file.write_text(large_text)

        start_time = time.time()

        docs = processor.process_file(str(large_file))

        end_time = time.time()
        duration = end_time - start_time

        # Should process successfully
        assert len(docs) > 0

        # Should be reasonably fast (< 5s for 1MB)
        assert duration < 5.0

        print(f"\n1MB document processing: {duration:.2f}s")

    def test_vector_store_large_query_result(self, tmp_path):
        """Test vector store with large result sets"""
        vector_store = VectorStore(
            persist_directory=str(tmp_path / "large_result"),
            collection_name="large"
        )

        # Add 1000 documents
        texts = [f"Document {i}" for i in range(1000)]
        vector_store.add_documents(texts=texts, ids=[f"id{i}" for i in range(1000)])

        start_time = time.time()

        # Request top 500 results
        results = vector_store.similarity_search("Document", k=500)

        end_time = time.time()
        duration = end_time - start_time

        # Should return results
        assert len(results) > 0

        # Should be reasonably fast (< 2s)
        assert duration < 2.0

        print(f"\nVector search (k=500 from 1000 docs): {duration:.2f}s")


# ============================================================================
# Cache Performance Tests
# ============================================================================

@pytest.mark.slow
@pytest.mark.unit
class TestCachePerformance:
    """Test cache performance improvements"""

    def test_vector_store_cache_hit(self, tmp_path):
        """Test vector store query cache performance"""
        vector_store = VectorStore(
            persist_directory=str(tmp_path / "cache_test"),
            collection_name="cache",
            cache_size=100,
            cache_ttl=3600
        )

        # Add documents
        texts = [f"Document {i}" for i in range(100)]
        vector_store.add_documents(texts=texts, ids=[f"id{i}" for i in range(100)])

        query = "Document content"

        # First query (cache miss)
        start1 = time.time()
        result1 = vector_store.similarity_search(query, k=10)
        duration1 = time.time() - start1

        # Second query (cache hit)
        start2 = time.time()
        result2 = vector_store.similarity_search(query, k=10)
        duration2 = time.time() - start2

        # Results should be identical
        assert len(result1) == len(result2)

        # Cached query should be significantly faster
        speedup = duration1 / duration2 if duration2 > 0 else 1
        assert speedup > 2  # At least 2x faster

        print(f"\nCache performance:")
        print(f"  First query (miss): {duration1*1000:.1f}ms")
        print(f"  Second query (hit): {duration2*1000:.1f}ms")
        print(f"  Speedup: {speedup:.1f}x")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
