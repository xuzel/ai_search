"""
Workflow Engine Examples

Demonstrates how to use the WorkflowEngine, TaskDecomposer, and ResultAggregator
for complex multi-step tasks.
"""

import asyncio
from src.workflow import (
    WorkflowEngine,
    TaskDecomposer,
    ResultAggregator,
    ExecutionMode,
    TaskStatus,
)
from src.llm import LLMManager
from src.utils import get_config
from src.tools import WeatherTool, FinanceTool, SearchTool


# ============================================================================
# Example 1: Simple Sequential Workflow
# ============================================================================

async def example_sequential_workflow():
    """
    Simple sequential workflow: Search -> Scrape -> Summarize
    """
    print("=" * 60)
    print("Example 1: Sequential Workflow")
    print("=" * 60)

    engine = WorkflowEngine()
    workflow = engine.create_workflow(
        "simple_research",
        mode=ExecutionMode.SEQUENTIAL
    )

    # Define tasks
    async def search_step(query):
        print(f"  Searching for: {query}")
        await asyncio.sleep(1)  # Simulate API call
        return {"query": query, "results": ["Result 1", "Result 2"]}

    async def process_step(search_result):
        print(f"  Processing {len(search_result['results'])} results")
        await asyncio.sleep(1)
        return {"processed": True, "count": len(search_result['results'])}

    async def summarize_step(search_result, process_result):
        print(f"  Creating summary")
        await asyncio.sleep(1)
        return {
            "summary": f"Found {process_result['count']} results for '{search_result['query']}'",
            "status": "complete"
        }

    # Add tasks to workflow
    workflow.add_task(
        task_id="search",
        name="Search for information",
        func=search_step,
        args=("Python async programming",),
        retry_count=3,
    )

    workflow.add_task(
        task_id="process",
        name="Process results",
        func=process_step,
        dependencies={"search"},
    )

    workflow.add_task(
        task_id="summarize",
        name="Create summary",
        func=summarize_step,
        dependencies={"search", "process"},
    )

    # Execute
    print("\nExecuting sequential workflow...\n")
    result = await engine.execute(workflow)

    print(f"\n✅ Workflow completed in {result.execution_time:.2f}s")
    print(f"Results: {result.results}")


# ============================================================================
# Example 2: Parallel Workflow
# ============================================================================

async def example_parallel_workflow():
    """
    Parallel workflow: Fetch multiple data sources simultaneously
    """
    print("\n" + "=" * 60)
    print("Example 2: Parallel Workflow")
    print("=" * 60)

    engine = WorkflowEngine(max_parallel_tasks=3)
    workflow = engine.create_workflow(
        "parallel_fetch",
        mode=ExecutionMode.PARALLEL
    )

    # Simulate fetching from different sources
    async def fetch_source_1():
        print("  Fetching from Source 1...")
        await asyncio.sleep(2)
        return {"source": 1, "data": "Data from source 1"}

    async def fetch_source_2():
        print("  Fetching from Source 2...")
        await asyncio.sleep(1.5)
        return {"source": 2, "data": "Data from source 2"}

    async def fetch_source_3():
        print("  Fetching from Source 3...")
        await asyncio.sleep(1)
        return {"source": 3, "data": "Data from source 3"}

    # Add tasks
    workflow.add_task("source1", func=fetch_source_1)
    workflow.add_task("source2", func=fetch_source_2)
    workflow.add_task("source3", func=fetch_source_3)

    print("\nExecuting parallel workflow...\n")
    result = await engine.execute(workflow)

    print(f"\n✅ All sources fetched in {result.execution_time:.2f}s (in parallel)")
    for task_id, data in result.results.items():
        print(f"  {task_id}: {data}")


# ============================================================================
# Example 3: DAG Workflow with Dependencies
# ============================================================================

async def example_dag_workflow():
    """
    DAG workflow: Complex dependency graph

    Dependency graph:
        A ──┬──> B ──┐
            │        ├──> D
            └──> C ──┘
    """
    print("\n" + "=" * 60)
    print("Example 3: DAG Workflow")
    print("=" * 60)

    engine = WorkflowEngine()
    workflow = engine.create_workflow(
        "dag_example",
        mode=ExecutionMode.DAG
    )

    # Define tasks
    async def task_a():
        print("  Task A: Starting...")
        await asyncio.sleep(1)
        return {"task": "A", "value": 10}

    async def task_b(a_result):
        print(f"  Task B: Processing A's result ({a_result['value']})")
        await asyncio.sleep(1)
        return {"task": "B", "value": a_result['value'] * 2}

    async def task_c(a_result):
        print(f"  Task C: Processing A's result ({a_result['value']})")
        await asyncio.sleep(1.5)
        return {"task": "C", "value": a_result['value'] + 5}

    async def task_d(a_result, b_result, c_result):
        print(f"  Task D: Combining B and C")
        await asyncio.sleep(1)
        return {
            "task": "D",
            "final": b_result['value'] + c_result['value'],
            "original": a_result['value']
        }

    # Add tasks with dependencies
    workflow.add_task("A", func=task_a)
    workflow.add_task("B", func=task_b, dependencies={"A"})
    workflow.add_task("C", func=task_c, dependencies={"A"})
    workflow.add_task("D", func=task_d, dependencies={"A", "B", "C"})

    # Validate (checks for circular dependencies)
    workflow.validate()

    print("\nExecuting DAG workflow...\n")

    # Execute with progress callback
    async def on_progress(task_id, status, result):
        if status == TaskStatus.COMPLETED:
            print(f"    ✓ {task_id} completed")

    result = await engine.execute(workflow, on_progress=on_progress)

    print(f"\n✅ DAG workflow completed in {result.execution_time:.2f}s")
    print(f"Final result: {result.results['D']}")


# ============================================================================
# Example 4: Task Decomposition
# ============================================================================

async def example_task_decomposition():
    """
    Use TaskDecomposer to break down complex queries
    """
    print("\n" + "=" * 60)
    print("Example 4: Task Decomposition")
    print("=" * 60)

    config = get_config()
    llm = LLMManager(config=config)
    decomposer = TaskDecomposer(llm, max_subtasks=10)

    # Complex query
    queries = [
        "Compare weather in Beijing and Tokyo",
        "What is the stock price of AAPL and how has it changed this year?",
        "Calculate the difference between 2^10 and 1000",
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)

        # Decompose
        plan = await decomposer.decompose(query)

        print(f"Goal: {plan.goal}")
        print(f"Complexity: {plan.complexity}")
        print(f"Steps: {plan.estimated_steps}\n")

        for i, subtask in enumerate(plan.subtasks, 1):
            deps = f" (depends on: {', '.join(subtask.dependencies)})" if subtask.dependencies else ""
            print(f"{i}. [{subtask.tool}] {subtask.description}{deps}")
            print(f"   Query: {subtask.query}")
            print(f"   Output: {subtask.output_variable}\n")


# ============================================================================
# Example 5: Result Aggregation
# ============================================================================

async def example_result_aggregation():
    """
    Aggregate results from multiple sources
    """
    print("\n" + "=" * 60)
    print("Example 5: Result Aggregation")
    print("=" * 60)

    config = get_config()
    llm = LLMManager(config=config)
    aggregator = ResultAggregator(
        llm_manager=llm,
        similarity_threshold=0.85
    )

    # Simulate results from different sources
    results = [
        {
            "source": "Wikipedia",
            "title": "Python (programming language)",
            "content": "Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum in 1991.",
        },
        {
            "source": "Official Docs",
            "title": "What is Python?",
            "content": "Python is an interpreted, high-level programming language. It emphasizes code readability and allows programmers to express concepts in fewer lines of code.",
        },
        {
            "source": "Tutorial",
            "title": "Introduction to Python",
            "content": "Python is a versatile programming language created in 1991. It is widely used for web development, data analysis, and automation.",
        },
        # Duplicate for testing deduplication
        {
            "source": "Mirror Site",
            "title": "Python Overview",
            "content": "Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum in 1991.",
        },
    ]

    print(f"\nAggregating {len(results)} results...\n")

    # Test deduplication
    deduplicated = aggregator.deduplicate(results)
    print(f"Deduplication: {len(results)} -> {len(deduplicated)} results")

    # Aggregate with synthesis strategy
    aggregated = await aggregator.aggregate(
        results,
        query="What is Python?",
        strategy="synthesis"
    )

    print(f"\n{'='*60}")
    print("Synthesized Summary:")
    print(f"{'='*60}")
    print(aggregated.summary)

    print(f"\n{'='*60}")
    print("Key Points:")
    print(f"{'='*60}")
    for i, point in enumerate(aggregated.key_points, 1):
        print(f"{i}. {point}")

    print(f"\nConfidence: {aggregated.confidence:.2f}")
    print(f"Sources: {len(aggregated.sources)}")


# ============================================================================
# Example 6: Real-world Scenario - Multi-source Research
# ============================================================================

async def example_real_world_research():
    """
    Real-world example: Research a topic using multiple sources and synthesize
    """
    print("\n" + "=" * 60)
    print("Example 6: Real-world Multi-source Research")
    print("=" * 60)

    config = get_config()
    llm = LLMManager(config=config)

    # Check if API keys are configured
    if not config.search.serpapi_key:
        print("\n⚠️  SERPAPI_API_KEY not configured. Using mock data.")

        # Create mock workflow with simulated results
        engine = WorkflowEngine()
        workflow = engine.create_workflow("mock_research", mode=ExecutionMode.DAG)

        async def mock_search(query):
            await asyncio.sleep(1)
            return [
                {"title": f"Result 1 for {query}", "content": f"Content about {query}..."},
                {"title": f"Result 2 for {query}", "content": f"More info on {query}..."},
            ]

        async def mock_aggregate(search1_result, search2_result):
            aggregator = ResultAggregator(llm)
            all_results = search1_result + search2_result
            return await aggregator.aggregate(all_results, strategy="concatenate")

        workflow.add_task("search1", func=mock_search, args=("AI trends",))
        workflow.add_task("search2", func=mock_search, args=("machine learning 2025",))
        workflow.add_task("aggregate", func=mock_aggregate, dependencies={"search1", "search2"})

        result = await engine.execute(workflow)

        if result.success:
            final = result.results["aggregate"]
            print(f"\n✅ Research completed")
            print(f"Summary: {final.summary[:200]}...")

        return

    # Real implementation with SearchTool
    search_tool = SearchTool(api_key=config.search.serpapi_key)
    aggregator = ResultAggregator(llm)
    engine = WorkflowEngine()

    workflow = engine.create_workflow("research", mode=ExecutionMode.DAG)

    # Research topic
    topic = "artificial intelligence trends 2025"

    # Define search tasks
    async def search_general():
        print(f"  Searching: {topic}")
        results = await search_tool.search(topic, num_results=5)
        return results

    async def search_academic():
        print(f"  Searching academic sources")
        results = await search_tool.search(f"{topic} site:arxiv.org OR site:edu", num_results=3)
        return results

    async def aggregate_results(general_result, academic_result):
        print(f"  Aggregating {len(general_result) + len(academic_result)} results")
        all_results = general_result + academic_result
        return await aggregator.aggregate(
            all_results,
            query=topic,
            strategy="synthesis"
        )

    # Add tasks
    workflow.add_task("general", func=search_general, timeout=30.0)
    workflow.add_task("academic", func=search_academic, timeout=30.0)
    workflow.add_task(
        "aggregate",
        func=aggregate_results,
        dependencies={"general", "academic"}
    )

    print(f"\nResearching: '{topic}'\n")
    result = await engine.execute(workflow)

    if result.success:
        final = result.results["aggregate"]
        print(f"\n{'='*60}")
        print("Research Summary:")
        print(f"{'='*60}")
        print(final.summary)

        print(f"\n{'='*60}")
        print("Key Findings:")
        print(f"{'='*60}")
        for i, point in enumerate(final.key_points, 1):
            print(f"{i}. {point}")

        print(f"\nSources: {len(final.sources)}")
        print(f"Confidence: {final.confidence:.2f}")
        print(f"Execution time: {result.execution_time:.2f}s")
    else:
        print(f"\n❌ Research failed: {result.errors}")


# ============================================================================
# Example 7: Error Handling and Retry
# ============================================================================

async def example_error_handling():
    """
    Demonstrate error handling and retry mechanism
    """
    print("\n" + "=" * 60)
    print("Example 7: Error Handling and Retry")
    print("=" * 60)

    engine = WorkflowEngine()
    workflow = engine.create_workflow("retry_demo", mode=ExecutionMode.SEQUENTIAL)

    # Task that fails first 2 times, succeeds on 3rd attempt
    attempt_counter = {"count": 0}

    async def flaky_task():
        attempt_counter["count"] += 1
        print(f"  Attempt {attempt_counter['count']}")

        if attempt_counter["count"] < 3:
            raise Exception(f"Simulated failure (attempt {attempt_counter['count']})")

        print(f"  ✓ Success on attempt {attempt_counter['count']}")
        return {"status": "success", "attempts": attempt_counter["count"]}

    # Task that always fails
    async def failing_task():
        print("  This task will fail")
        raise Exception("Permanent failure")

    # Success callback
    async def on_success(result):
        print(f"  ✅ Task succeeded after {result['attempts']} attempts")

    # Failure callback
    async def on_failure(error):
        print(f"  ❌ Task failed permanently: {error}")

    # Add tasks
    workflow.add_task(
        "flaky",
        func=flaky_task,
        retry_count=3,
        on_success=on_success,
    )

    workflow.add_task(
        "failing",
        func=failing_task,
        retry_count=2,
        on_failure=on_failure,
    )

    print("\nExecuting workflow with error handling...\n")
    result = await engine.execute(workflow)

    print(f"\n{'='*60}")
    print(f"Workflow result: {'Success' if result.success else 'Failed'}")
    print(f"Completed: {result.completed_count}/{result.task_count}")
    print(f"Failed: {result.failed_count}")
    print(f"Execution time: {result.execution_time:.2f}s")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all examples"""

    print("\n" + "=" * 60)
    print("WORKFLOW ENGINE EXAMPLES")
    print("=" * 60)

    # Run examples
    await example_sequential_workflow()
    await example_parallel_workflow()
    await example_dag_workflow()
    await example_task_decomposition()
    await example_result_aggregation()
    await example_real_world_research()
    await example_error_handling()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
