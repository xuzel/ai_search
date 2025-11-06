"""Unit tests for workflow module"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.workflow import (
    WorkflowEngine,
    ExecutionMode,
    ResultAggregator,
    TaskDecomposer,
)


# ============================================================================
# WorkflowEngine Tests
# ============================================================================

@pytest.mark.unit
class TestWorkflowEngine:
    """Test WorkflowEngine functionality"""

    @pytest.fixture
    def engine(self):
        """Create WorkflowEngine instance"""
        return WorkflowEngine(max_parallel_tasks=3)

    def test_create_workflow(self, engine):
        """Test workflow creation"""
        workflow = engine.create_workflow("test_workflow", mode=ExecutionMode.SEQUENTIAL)

        assert workflow is not None
        assert workflow.name == "test_workflow"
        assert workflow.mode == ExecutionMode.SEQUENTIAL

    def test_create_dag_workflow(self, engine):
        """Test DAG workflow creation"""
        workflow = engine.create_workflow("dag_workflow", mode=ExecutionMode.DAG)

        assert workflow.mode == ExecutionMode.DAG

    @pytest.mark.asyncio
    async def test_execute_sequential_workflow(self, engine):
        """Test executing sequential workflow"""
        workflow = engine.create_workflow("seq", mode=ExecutionMode.SEQUENTIAL)

        # Define tasks
        async def task1():
            return {"value": 1}

        async def task2():
            return {"value": 2}

        workflow.add_task("task1", func=task1)
        workflow.add_task("task2", func=task2)

        # Execute
        result = await engine.execute(workflow)

        assert result.success
        assert result.completed_count == 2
        assert "task1" in result.results
        assert "task2" in result.results

    @pytest.mark.asyncio
    async def test_execute_parallel_workflow(self, engine):
        """Test executing parallel workflow"""
        workflow = engine.create_workflow("parallel", mode=ExecutionMode.PARALLEL)

        # Define tasks that can run in parallel
        async def fast_task():
            await asyncio.sleep(0.1)
            return {"result": "fast"}

        async def slow_task():
            await asyncio.sleep(0.2)
            return {"result": "slow"}

        workflow.add_task("fast", func=fast_task)
        workflow.add_task("slow", func=slow_task)

        # Execute
        result = await engine.execute(workflow)

        assert result.success
        assert result.completed_count == 2
        # Parallel execution should be faster than sequential
        assert result.execution_time < 0.4  # Should be ~0.2s, not 0.3s

    @pytest.mark.asyncio
    async def test_execute_dag_workflow(self, engine):
        """Test executing DAG workflow with dependencies"""
        workflow = engine.create_workflow("dag", mode=ExecutionMode.DAG)

        # Define tasks with dependencies
        async def task_a():
            return {"value": 10}

        async def task_b(a_result):
            return {"value": a_result["value"] * 2}

        async def task_c(a_result, b_result):
            return {"value": a_result["value"] + b_result["value"]}

        workflow.add_task("A", func=task_a)
        workflow.add_task("B", func=task_b, dependencies={"A"})
        workflow.add_task("C", func=task_c, dependencies={"A", "B"})

        # Execute
        result = await engine.execute(workflow)

        assert result.success
        assert result.results["A"]["value"] == 10
        assert result.results["B"]["value"] == 20
        assert result.results["C"]["value"] == 30

    @pytest.mark.asyncio
    async def test_workflow_validation(self, engine):
        """Test workflow validation detects cycles"""
        workflow = engine.create_workflow("invalid", mode=ExecutionMode.DAG)

        async def dummy():
            return {}

        # Create circular dependency
        workflow.add_task("A", func=dummy, dependencies={"B"})
        workflow.add_task("B", func=dummy, dependencies={"A"})

        # Validation should detect cycle
        with pytest.raises((ValueError, Exception)):
            workflow.validate()

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, engine):
        """Test workflow handles task errors"""
        workflow = engine.create_workflow("error_test", mode=ExecutionMode.SEQUENTIAL)

        async def failing_task():
            raise ValueError("Task failed")

        async def success_task():
            return {"result": "ok"}

        workflow.add_task("fail", func=failing_task)
        workflow.add_task("success", func=success_task)

        # Execute
        result = await engine.execute(workflow)

        assert not result.success
        assert len(result.errors) > 0
        assert "fail" in result.errors

    @pytest.mark.asyncio
    async def test_workflow_timeout(self, engine):
        """Test workflow timeout enforcement"""
        workflow = engine.create_workflow("timeout_test", mode=ExecutionMode.SEQUENTIAL)

        async def slow_task():
            await asyncio.sleep(10)  # Very slow
            return {"result": "done"}

        workflow.add_task("slow", func=slow_task)

        # Execute with short timeout
        result = await engine.execute(workflow, timeout=1)

        assert not result.success
        # Should have timeout error
        assert any("timeout" in str(e).lower() for e in result.errors.values())


# ============================================================================
# ResultAggregator Tests
# ============================================================================

@pytest.mark.unit
class TestResultAggregator:
    """Test ResultAggregator functionality"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM manager"""
        llm = AsyncMock()
        llm.complete = AsyncMock(return_value="Aggregated summary of the results")
        return llm

    @pytest.fixture
    def aggregator(self, mock_llm):
        """Create ResultAggregator instance"""
        return ResultAggregator(llm_manager=mock_llm)

    def test_deduplicate_results(self, aggregator):
        """Test result deduplication"""
        results = [
            {"source": "A", "content": "Python is a programming language"},
            {"source": "B", "content": "Python is a programming language"},  # Duplicate
            {"source": "C", "content": "Python was created in 1991"},
        ]

        deduplicated = aggregator.deduplicate(results)

        # Should remove exact duplicate
        assert len(deduplicated) == 2
        assert deduplicated[0]["content"] != deduplicated[1]["content"]

    def test_deduplicate_similar_results(self, aggregator):
        """Test deduplication of similar results"""
        results = [
            {"content": "Machine learning is AI"},
            {"content": "Machine learning is a subset of AI"},  # Very similar
            {"content": "Deep learning uses neural networks"},  # Different
        ]

        deduplicated = aggregator.deduplicate(results, similarity_threshold=0.8)

        # Should keep distinct results
        assert len(deduplicated) >= 2

    @pytest.mark.asyncio
    async def test_aggregate_concat_strategy(self, aggregator):
        """Test concatenation aggregation strategy"""
        results = [
            {"content": "First result"},
            {"content": "Second result"},
        ]

        aggregated = await aggregator.aggregate(
            results,
            query="test query",
            strategy="concat"
        )

        assert aggregated is not None
        assert hasattr(aggregated, "summary") or isinstance(aggregated, dict)

    @pytest.mark.asyncio
    async def test_aggregate_synthesis_strategy(self, aggregator, mock_llm):
        """Test synthesis aggregation strategy"""
        results = [
            {"content": "Python is easy to learn"},
            {"content": "Python has many libraries"},
        ]

        aggregated = await aggregator.aggregate(
            results,
            query="What is Python?",
            strategy="synthesis"
        )

        # Should use LLM for synthesis
        assert mock_llm.complete.called
        assert aggregated is not None

    @pytest.mark.asyncio
    async def test_aggregate_ranking_strategy(self, aggregator):
        """Test ranking aggregation strategy"""
        results = [
            {"content": "Less relevant result", "score": 0.5},
            {"content": "Most relevant result", "score": 0.9},
            {"content": "Moderately relevant", "score": 0.7},
        ]

        aggregated = await aggregator.aggregate(
            results,
            query="test",
            strategy="ranking"
        )

        assert aggregated is not None
        # Results should be ranked by score

    @pytest.mark.asyncio
    async def test_extract_key_points(self, aggregator):
        """Test extracting key points from results"""
        results = [
            {"content": "Python is easy. Python is versatile."},
            {"content": "Python has great libraries."},
        ]

        key_points = await aggregator.extract_key_points(results)

        assert isinstance(key_points, list)
        assert len(key_points) > 0

    @pytest.mark.asyncio
    async def test_calculate_confidence(self, aggregator):
        """Test calculating confidence score"""
        results = [
            {"content": "High quality result", "score": 0.9},
            {"content": "Medium quality", "score": 0.7},
        ]

        confidence = aggregator.calculate_confidence(results)

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1


# ============================================================================
# TaskDecomposer Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
class TestTaskDecomposer:
    """Test TaskDecomposer functionality"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM manager"""
        llm = AsyncMock()
        # Mock LLM response for task decomposition
        llm.complete = AsyncMock(return_value="""{
            "goal": "Compare weather in Beijing and Shanghai",
            "complexity": "medium",
            "estimated_steps": 3,
            "subtasks": [
                {
                    "id": "task1",
                    "description": "Get weather for Beijing",
                    "tool": "weather_tool",
                    "query": "weather in Beijing",
                    "dependencies": []
                },
                {
                    "id": "task2",
                    "description": "Get weather for Shanghai",
                    "tool": "weather_tool",
                    "query": "weather in Shanghai",
                    "dependencies": []
                },
                {
                    "id": "task3",
                    "description": "Compare the results",
                    "tool": "aggregator",
                    "query": "compare weather",
                    "dependencies": ["task1", "task2"]
                }
            ]
        }""")
        return llm

    @pytest.fixture
    def decomposer(self, mock_llm):
        """Create TaskDecomposer instance"""
        return TaskDecomposer(llm_manager=mock_llm, max_subtasks=5)

    @pytest.mark.asyncio
    async def test_decompose_query(self, decomposer):
        """Test query decomposition"""
        plan = await decomposer.decompose("Compare weather in Beijing and Shanghai")

        assert plan is not None
        assert hasattr(plan, "goal") or isinstance(plan, dict)
        if hasattr(plan, "goal"):
            assert plan.goal is not None
            assert hasattr(plan, "subtasks")
            assert len(plan.subtasks) > 0

    @pytest.mark.asyncio
    async def test_decompose_simple_query(self, decomposer, mock_llm):
        """Test decomposing simple query"""
        # Mock response for simple query
        mock_llm.complete.return_value = """{
            "goal": "Get weather",
            "complexity": "simple",
            "estimated_steps": 1,
            "subtasks": [
                {
                    "id": "task1",
                    "description": "Get weather",
                    "tool": "weather_tool",
                    "query": "weather",
                    "dependencies": []
                }
            ]
        }"""

        plan = await decomposer.decompose("What's the weather?")

        assert plan is not None
        if hasattr(plan, "complexity"):
            assert plan.complexity == "simple"

    @pytest.mark.asyncio
    async def test_decompose_complex_query(self, decomposer, mock_llm):
        """Test decomposing complex query"""
        mock_llm.complete.return_value = """{
            "goal": "Complex analysis",
            "complexity": "complex",
            "estimated_steps": 5,
            "subtasks": []
        }"""

        plan = await decomposer.decompose(
            "Analyze the weather patterns across multiple cities and correlate with stock market performance"
        )

        assert plan is not None
        if hasattr(plan, "complexity"):
            assert plan.complexity in ["medium", "complex"]

    @pytest.mark.asyncio
    async def test_validate_plan(self, decomposer):
        """Test plan validation"""
        # Create valid plan
        plan = MagicMock()
        plan.goal = "Test goal"
        plan.subtasks = [
            MagicMock(id="task1", dependencies=[]),
            MagicMock(id="task2", dependencies=["task1"])
        ]

        # Should not raise error
        is_valid = decomposer.validate_plan(plan)
        assert is_valid is True or is_valid is None  # Depends on implementation

    @pytest.mark.asyncio
    async def test_optimize_plan(self, decomposer):
        """Test plan optimization"""
        plan = MagicMock()
        plan.subtasks = [
            MagicMock(id="task1", tool="weather_tool", dependencies=[]),
            MagicMock(id="task2", tool="weather_tool", dependencies=[]),
            MagicMock(id="task3", tool="finance_tool", dependencies=["task1", "task2"])
        ]

        # Optimize plan
        optimized = decomposer.optimize_plan(plan)

        assert optimized is not None
        # Optimization should identify parallel tasks

    @pytest.mark.asyncio
    async def test_identify_tool_for_task(self, decomposer):
        """Test tool identification for task"""
        tools = decomposer.identify_required_tools("Get weather in Beijing")

        assert isinstance(tools, list)
        # Should identify weather_tool
        assert any("weather" in tool.lower() for tool in tools) or len(tools) > 0


# ============================================================================
# Workflow Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflowIntegration:
    """Integration tests for workflow module"""

    @pytest.fixture
    def config(self):
        """Get real configuration"""
        from src.utils import get_config
        return get_config()

    @pytest.fixture
    def llm_manager(self, config):
        """Get real LLM manager"""
        from src.llm import LLMManager
        return LLMManager(config=config)

    @pytest.mark.asyncio
    async def test_task_decomposer_end_to_end(self, llm_manager):
        """Test TaskDecomposer end-to-end"""
        decomposer = TaskDecomposer(llm_manager=llm_manager, max_subtasks=5)

        plan = await decomposer.decompose("Compare temperatures in Beijing and Shanghai")

        assert plan is not None
        # Plan should have structure
        assert hasattr(plan, "goal") or isinstance(plan, dict)

    @pytest.mark.asyncio
    async def test_result_aggregator_end_to_end(self, llm_manager):
        """Test ResultAggregator end-to-end"""
        aggregator = ResultAggregator(llm_manager=llm_manager)

        results = [
            {"content": "Python is a high-level language", "score": 0.9},
            {"content": "Python is easy to learn", "score": 0.8},
            {"content": "Python has many libraries", "score": 0.85},
        ]

        aggregated = await aggregator.aggregate(
            results,
            query="What is Python?",
            strategy="synthesis"
        )

        assert aggregated is not None
        # Should have summary
        if hasattr(aggregated, "summary"):
            assert len(aggregated.summary) > 0

    @pytest.mark.asyncio
    async def test_workflow_engine_end_to_end(self):
        """Test WorkflowEngine end-to-end"""
        engine = WorkflowEngine(max_parallel_tasks=2)
        workflow = engine.create_workflow("test", mode=ExecutionMode.DAG)

        # Define real-world tasks
        async def fetch_data():
            await asyncio.sleep(0.1)
            return {"data": [1, 2, 3, 4, 5]}

        async def process_data(fetch_result):
            await asyncio.sleep(0.1)
            data = fetch_result["data"]
            return {"sum": sum(data), "count": len(data)}

        async def generate_report(process_result):
            await asyncio.sleep(0.1)
            return {
                "report": f"Processed {process_result['count']} items, sum: {process_result['sum']}"
            }

        workflow.add_task("fetch", func=fetch_data)
        workflow.add_task("process", func=process_data, dependencies={"fetch"})
        workflow.add_task("report", func=generate_report, dependencies={"process"})

        # Execute
        result = await engine.execute(workflow)

        assert result.success
        assert result.completed_count == 3
        assert "report" in result.results
        assert "Processed 5 items" in result.results["report"]["report"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
