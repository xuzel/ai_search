"""
Tests for newly implemented features:
- LLM Streaming Infrastructure
- Agent Streaming Methods
- SearchTool Caching
- HybridRouter Feedback
- ChatAgent History Compression
- VectorStore Hybrid Search
- TaskTracker
- WorkflowEngine Checkpoints
"""

import asyncio
import json
import os
import tempfile
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# ============================================================================
# Test 1: LLM Streaming Infrastructure
# ============================================================================

class TestLLMStreaming:
    """Test LLM streaming infrastructure"""

    def test_llm_manager_has_stream_complete(self):
        """Verify LLMManager has stream_complete method"""
        from src.llm.manager import LLMManager
        assert hasattr(LLMManager, 'stream_complete')
        assert hasattr(LLMManager, '_get_provider_order')

    def test_openai_client_has_stream_complete(self):
        """Verify OpenAIClient has stream_complete method"""
        from src.llm.openai_client import OpenAIClient
        assert hasattr(OpenAIClient, 'stream_complete')

    def test_ollama_client_has_stream_complete(self):
        """Verify OllamaClient has stream_complete method"""
        from src.llm.ollama_client import OllamaClient
        assert hasattr(OllamaClient, 'stream_complete')

    @pytest.mark.asyncio
    async def test_llm_manager_get_provider_order(self):
        """Test provider ordering logic"""
        from src.llm.manager import LLMManager

        # Create manager with mocked config
        mock_config = MagicMock()
        mock_config.llm.openai_enabled = False
        mock_config.llm.openai_api_key = None
        mock_config.llm.dashscope_enabled = False
        mock_config.llm.dashscope_api_key = None
        mock_config.llm.deepseek_enabled = False
        mock_config.llm.deepseek_api_key = None
        mock_config.llm.local_compatible_enabled = False
        mock_config.llm.ollama_enabled = False

        manager = LLMManager(config=mock_config)

        # Test provider order with no providers
        order = manager._get_provider_order(None)
        assert order == []

    @pytest.mark.asyncio
    async def test_llm_manager_stream_complete_no_providers(self):
        """Test stream_complete raises error when no providers"""
        from src.llm.manager import LLMManager

        mock_config = MagicMock()
        mock_config.llm.openai_enabled = False
        mock_config.llm.openai_api_key = None
        mock_config.llm.dashscope_enabled = False
        mock_config.llm.dashscope_api_key = None
        mock_config.llm.deepseek_enabled = False
        mock_config.llm.deepseek_api_key = None
        mock_config.llm.local_compatible_enabled = False
        mock_config.llm.ollama_enabled = False

        manager = LLMManager(config=mock_config)

        with pytest.raises(RuntimeError, match="No LLM providers available"):
            async for _ in manager.stream_complete([{"role": "user", "content": "test"}]):
                pass


# ============================================================================
# Test 2: Agent Streaming Methods
# ============================================================================

class TestAgentStreaming:
    """Test Agent streaming methods"""

    def test_chat_agent_has_stream_chat(self):
        """Verify ChatAgent has stream_chat method"""
        from src.agents.chat_agent import ChatAgent
        assert hasattr(ChatAgent, 'stream_chat')

    def test_research_agent_has_stream_research(self):
        """Verify ResearchAgent has stream_research method"""
        from src.agents.research_agent import ResearchAgent
        assert hasattr(ResearchAgent, 'stream_research')
        assert hasattr(ResearchAgent, '_stream_synthesize_information')

    def test_code_agent_has_stream_solve(self):
        """Verify CodeAgent has stream_solve and auto-fix methods"""
        from src.agents.code_agent import CodeAgent
        assert hasattr(CodeAgent, 'stream_solve')
        assert hasattr(CodeAgent, '_fix_code')
        assert hasattr(CodeAgent, '_stream_explain_results')

    def test_rag_agent_has_stream_query(self):
        """Verify RAGAgent has stream_query and query expansion"""
        from src.agents.rag_agent import RAGAgent
        assert hasattr(RAGAgent, 'stream_query')
        assert hasattr(RAGAgent, '_expand_query')
        assert hasattr(RAGAgent, '_stream_generate_answer')
        assert hasattr(RAGAgent, 'set_query_expansion')

    @pytest.mark.asyncio
    async def test_chat_agent_stream_chat(self):
        """Test ChatAgent stream_chat method"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = AsyncMock()

        # Mock stream_complete to yield chunks
        async def mock_stream():
            for chunk in ["Hello", " ", "World", "!"]:
                yield chunk

        mock_llm.stream_complete = MagicMock(return_value=mock_stream())

        agent = ChatAgent(llm_manager=mock_llm)

        chunks = []
        async for chunk in agent.stream_chat("Hi"):
            chunks.append(chunk)

        assert chunks == ["Hello", " ", "World", "!"]
        assert len(agent.conversation_history) == 2  # user + assistant


# ============================================================================
# Test 3: SearchTool Caching
# ============================================================================

class TestSearchToolCaching:
    """Test SearchTool caching functionality"""

    def test_search_cache_init(self):
        """Test SearchCache initialization"""
        from src.tools.search import SearchCache

        cache = SearchCache(max_size=50, ttl=1800)
        assert cache.max_size == 50
        assert cache.ttl == 1800
        assert len(cache._cache) == 0

    def test_search_cache_set_get(self):
        """Test SearchCache set and get"""
        from src.tools.search import SearchCache

        cache = SearchCache(max_size=10, ttl=3600)

        # Set a value
        results = [{"title": "Test", "link": "http://test.com", "snippet": "Test snippet"}]
        cache.set("test query", 5, "serpapi", results)

        # Get the value
        cached = cache.get("test query", 5, "serpapi")
        assert cached is not None
        assert cached == results

    def test_search_cache_miss(self):
        """Test SearchCache miss"""
        from src.tools.search import SearchCache

        cache = SearchCache()
        result = cache.get("nonexistent", 5, "serpapi")
        assert result is None

    def test_search_cache_expiry(self):
        """Test SearchCache TTL expiry"""
        from src.tools.search import SearchCache

        cache = SearchCache(max_size=10, ttl=1)  # 1 second TTL

        results = [{"title": "Test"}]
        cache.set("test", 5, "serpapi", results)

        # Should be available immediately
        assert cache.get("test", 5, "serpapi") is not None

        # Wait for expiry
        time.sleep(1.5)

        # Should be expired now
        assert cache.get("test", 5, "serpapi") is None

    def test_search_cache_lru_eviction(self):
        """Test SearchCache LRU eviction"""
        from src.tools.search import SearchCache

        cache = SearchCache(max_size=3, ttl=3600)

        # Add 3 items
        cache.set("q1", 5, "serpapi", [{"title": "1"}])
        cache.set("q2", 5, "serpapi", [{"title": "2"}])
        cache.set("q3", 5, "serpapi", [{"title": "3"}])

        # All should be present
        assert cache.get("q1", 5, "serpapi") is not None
        assert cache.get("q2", 5, "serpapi") is not None
        assert cache.get("q3", 5, "serpapi") is not None

        # Add 4th item, should evict q1 (LRU)
        cache.set("q4", 5, "serpapi", [{"title": "4"}])

        # q1 should be evicted
        assert cache.get("q1", 5, "serpapi") is None
        assert cache.get("q4", 5, "serpapi") is not None

    def test_search_tool_cache_enabled(self):
        """Test SearchTool with cache enabled"""
        from src.tools.search import SearchTool

        tool = SearchTool(cache_enabled=True, cache_max_size=100, cache_ttl=3600)
        assert tool._cache is not None
        assert tool.cache_enabled is True

    def test_search_tool_cache_disabled(self):
        """Test SearchTool with cache disabled"""
        from src.tools.search import SearchTool

        tool = SearchTool(cache_enabled=False)
        assert tool._cache is None
        assert tool.cache_enabled is False

    def test_search_tool_cache_stats(self):
        """Test SearchTool cache statistics"""
        from src.tools.search import SearchTool

        tool = SearchTool(cache_enabled=True, cache_max_size=50, cache_ttl=1800)
        stats = tool.get_cache_stats()

        assert stats is not None
        assert stats["size"] == 0
        assert stats["max_size"] == 50
        assert stats["ttl"] == 1800

    def test_search_tool_clear_cache(self):
        """Test SearchTool clear cache"""
        from src.tools.search import SearchTool

        tool = SearchTool(cache_enabled=True)
        tool._cache.set("test", 5, "serpapi", [{"title": "test"}])

        assert tool.get_cache_stats()["size"] == 1

        tool.clear_cache()

        assert tool.get_cache_stats()["size"] == 0


# ============================================================================
# Test 4: HybridRouter Feedback
# ============================================================================

class TestHybridRouterFeedback:
    """Test HybridRouter feedback mechanism"""

    def test_routing_feedback_tracker_init(self):
        """Test RoutingFeedbackTracker initialization"""
        from src.routing.hybrid_router import RoutingFeedbackTracker

        tracker = RoutingFeedbackTracker(max_history=500)
        assert tracker.max_history == 500
        assert len(tracker._feedback_history) == 0

    def test_record_feedback_correct(self):
        """Test recording correct feedback"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker()
        tracker.record_feedback(
            query="What's the weather?",
            routed_task=TaskType.DOMAIN_WEATHER,
            is_correct=True
        )

        assert len(tracker._feedback_history) == 1
        assert tracker._feedback_history[0].is_correct is True
        assert tracker.get_accuracy() == 1.0

    def test_record_feedback_incorrect(self):
        """Test recording incorrect feedback with correction"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker()
        tracker.record_feedback(
            query="Tell me about Python",
            routed_task=TaskType.CHAT,
            correct_task=TaskType.RESEARCH,
            is_correct=False
        )

        assert len(tracker._feedback_history) == 1
        assert tracker._feedback_history[0].is_correct is False
        assert tracker.get_accuracy() == 0.0

        # Check correction counts
        corrections = tracker.get_common_corrections()
        assert len(corrections) == 1
        assert corrections[0]["from"] == "chat"
        assert corrections[0]["to"] == "research"
        assert corrections[0]["count"] == 1

    def test_get_accuracy_by_task_type(self):
        """Test accuracy calculation by task type"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker()

        # Add some feedback
        tracker.record_feedback("q1", TaskType.CHAT, is_correct=True)
        tracker.record_feedback("q2", TaskType.CHAT, is_correct=True)
        tracker.record_feedback("q3", TaskType.CHAT, correct_task=TaskType.RESEARCH, is_correct=False)
        tracker.record_feedback("q4", TaskType.RESEARCH, is_correct=True)

        # Overall accuracy: 3/4 = 0.75
        assert tracker.get_accuracy() == 0.75

        # Chat accuracy: 2/3 ≈ 0.667
        assert abs(tracker.get_accuracy(TaskType.CHAT) - 0.667) < 0.01

        # Research accuracy: 1/1 = 1.0
        assert tracker.get_accuracy(TaskType.RESEARCH) == 1.0

    def test_feedback_stats(self):
        """Test feedback statistics"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker()
        tracker.record_feedback("q1", TaskType.CHAT, is_correct=True)
        tracker.record_feedback("q2", TaskType.CHAT, is_correct=False, correct_task=TaskType.RESEARCH)

        stats = tracker.get_stats()

        assert stats["total_feedback"] == 2
        assert stats["correct_count"] == 1
        assert stats["incorrect_count"] == 1
        assert stats["overall_accuracy"] == 0.5

    def test_should_adjust_threshold(self):
        """Test threshold adjustment suggestions"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker()

        # Add mostly incorrect feedback
        for i in range(10):
            tracker.record_feedback(
                f"q{i}",
                TaskType.CHAT,
                correct_task=TaskType.RESEARCH,
                is_correct=(i < 5)  # 50% accuracy
            )

        # Should suggest lowering threshold
        adjustment = tracker.should_adjust_threshold(TaskType.CHAT)
        assert adjustment == -0.1

    def test_feedback_history_limit(self):
        """Test feedback history limit"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker(max_history=5)

        # Add more than max_history
        for i in range(10):
            tracker.record_feedback(f"q{i}", TaskType.CHAT, is_correct=True)

        # Should only keep last 5
        assert len(tracker._feedback_history) == 5


# ============================================================================
# Test 5: ChatAgent History Compression
# ============================================================================

class TestChatAgentCompression:
    """Test ChatAgent history compression"""

    def test_chat_agent_compression_init(self):
        """Test ChatAgent initialization with compression settings"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = MagicMock()
        agent = ChatAgent(
            llm_manager=mock_llm,
            max_history=30,
            compression_threshold=20,
            enable_compression=True
        )

        assert agent.max_history == 30
        assert agent.compression_threshold == 20
        assert agent.enable_compression is True
        assert agent._compressed_summary is None

    def test_build_messages_without_summary(self):
        """Test message building without compressed summary"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = MagicMock()
        agent = ChatAgent(llm_manager=mock_llm)

        agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        messages = agent._build_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"

    def test_build_messages_with_summary(self):
        """Test message building with compressed summary"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = MagicMock()
        agent = ChatAgent(llm_manager=mock_llm)

        agent._compressed_summary = "Previous discussion about weather"
        agent.conversation_history = [
            {"role": "user", "content": "What about tomorrow?"},
            {"role": "assistant", "content": "It will be sunny."}
        ]

        messages = agent._build_messages()

        # Should have summary as first message
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert "Previous conversation summary" in messages[0]["content"]

    def test_get_history_stats(self):
        """Test history statistics"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = MagicMock()
        agent = ChatAgent(llm_manager=mock_llm, enable_compression=True)

        agent.conversation_history = [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Response"}
        ]

        stats = agent.get_history_stats()

        assert stats["message_count"] == 2
        assert stats["has_summary"] is False
        assert stats["compression_enabled"] is True

    def test_clear_history_clears_summary(self):
        """Test that clear_history also clears summary"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = MagicMock()
        agent = ChatAgent(llm_manager=mock_llm)

        agent._compressed_summary = "Some summary"
        agent.conversation_history = [{"role": "user", "content": "test"}]

        agent.clear_history()

        assert agent._compressed_summary is None
        assert len(agent.conversation_history) == 0

    def test_set_compression_enabled(self):
        """Test enabling/disabling compression"""
        from src.agents.chat_agent import ChatAgent

        mock_llm = MagicMock()
        agent = ChatAgent(llm_manager=mock_llm, enable_compression=False)

        assert agent.enable_compression is False

        agent.set_compression_enabled(True)
        assert agent.enable_compression is True


# ============================================================================
# Test 6: VectorStore Hybrid Search
# ============================================================================

class TestVectorStoreHybridSearch:
    """Test VectorStore hybrid search functionality"""

    def test_tokenize(self):
        """Test text tokenization"""
        from src.tools.vector_store import VectorStore

        # Create minimal mock to test tokenization
        with patch.object(VectorStore, '__init__', lambda x: None):
            vs = VectorStore.__new__(VectorStore)

            tokens = vs._tokenize("Hello World! This is a test.")
            assert "hello" in tokens
            assert "world" in tokens
            assert "test" in tokens
            # Single character tokens should be filtered
            assert "a" not in tokens

    def test_tokenize_chinese(self):
        """Test tokenization with Chinese text"""
        from src.tools.vector_store import VectorStore

        with patch.object(VectorStore, '__init__', lambda x: None):
            vs = VectorStore.__new__(VectorStore)

            tokens = vs._tokenize("Hello 你好 World")
            assert "hello" in tokens
            assert "world" in tokens

    def test_compute_keyword_score(self):
        """Test keyword score computation"""
        from src.tools.vector_store import VectorStore

        with patch.object(VectorStore, '__init__', lambda x: None):
            vs = VectorStore.__new__(VectorStore)

            # Exact match
            query_terms = ["python", "programming"]
            doc_text = "Python programming is fun. Python is great."
            score = vs._compute_keyword_score(query_terms, doc_text)
            assert score > 0.5  # High match

            # Partial match
            doc_text2 = "Python is a language."
            score2 = vs._compute_keyword_score(query_terms, doc_text2)
            assert score2 > 0
            assert score2 < score  # Lower than full match

            # No match
            doc_text3 = "Java and JavaScript are different."
            score3 = vs._compute_keyword_score(query_terms, doc_text3)
            assert score3 == 0

    def test_compute_keyword_score_empty(self):
        """Test keyword score with empty inputs"""
        from src.tools.vector_store import VectorStore

        with patch.object(VectorStore, '__init__', lambda x: None):
            vs = VectorStore.__new__(VectorStore)

            assert vs._compute_keyword_score([], "some text") == 0.0
            assert vs._compute_keyword_score(["test"], "") == 0.0


# ============================================================================
# Test 7: TaskTracker
# ============================================================================

class TestTaskTracker:
    """Test TaskTracker functionality"""

    def test_task_tracker_init(self):
        """Test TaskTracker initialization"""
        from src.workflow.task_tracker import TaskTracker

        tracker = TaskTracker(max_history=50)
        assert tracker.max_history == 50
        assert len(tracker._active_workflows) == 0

    def test_create_workflow(self):
        """Test workflow creation"""
        from src.workflow.task_tracker import TaskTracker

        tracker = TaskTracker()
        workflow = tracker.create_workflow(
            workflow_id="wf1",
            workflow_name="Test Workflow",
            task_names=["Task 1", "Task 2", "Task 3"]
        )

        assert workflow.workflow_id == "wf1"
        assert workflow.workflow_name == "Test Workflow"
        assert len(workflow.tasks) == 3
        assert workflow.tasks[0].task_name == "Task 1"

    def test_start_workflow(self):
        """Test starting a workflow"""
        from src.workflow.task_tracker import TaskTracker, TaskStatus

        tracker = TaskTracker()
        tracker.create_workflow("wf1", "Test", ["Task 1"])

        tracker.start_workflow("wf1")

        workflow = tracker.get_workflow("wf1")
        assert workflow.status == TaskStatus.RUNNING
        assert workflow.started_at is not None

    def test_task_lifecycle(self):
        """Test complete task lifecycle"""
        from src.workflow.task_tracker import TaskTracker, TaskStatus

        tracker = TaskTracker()
        tracker.create_workflow("wf1", "Test", ["Task 1", "Task 2"])
        tracker.start_workflow("wf1")

        # Start task 0
        tracker.start_task("wf1", 0, "Starting task 1")
        workflow = tracker.get_workflow("wf1")
        assert workflow.tasks[0].status == TaskStatus.RUNNING

        # Update progress
        tracker.update_task_progress("wf1", 0, 0.5, "Halfway done")
        assert workflow.tasks[0].progress == 0.5

        # Complete task
        tracker.complete_task("wf1", 0, result="Task 1 done", message="Completed!")
        assert workflow.tasks[0].status == TaskStatus.COMPLETED
        assert workflow.tasks[0].result == "Task 1 done"

    def test_fail_task(self):
        """Test failing a task"""
        from src.workflow.task_tracker import TaskTracker, TaskStatus

        tracker = TaskTracker()
        tracker.create_workflow("wf1", "Test", ["Task 1"])
        tracker.start_workflow("wf1")
        tracker.start_task("wf1", 0)

        tracker.fail_task("wf1", 0, error="Something went wrong")

        workflow = tracker.get_workflow("wf1")
        assert workflow.tasks[0].status == TaskStatus.FAILED
        assert workflow.tasks[0].error == "Something went wrong"

    def test_complete_workflow(self):
        """Test completing a workflow"""
        from src.workflow.task_tracker import TaskTracker, TaskStatus

        tracker = TaskTracker()
        tracker.create_workflow("wf1", "Test", ["Task 1"])
        tracker.start_workflow("wf1")
        tracker.start_task("wf1", 0)
        tracker.complete_task("wf1", 0)

        completed = tracker.complete_workflow("wf1", success=True)

        assert completed.status == TaskStatus.COMPLETED
        assert "wf1" not in tracker._active_workflows
        assert len(tracker._completed_workflows) == 1

    def test_overall_progress(self):
        """Test overall workflow progress calculation"""
        from src.workflow.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.create_workflow("wf1", "Test", ["T1", "T2", "T3", "T4"])
        tracker.start_workflow("wf1")

        # Complete 2 out of 4 tasks
        tracker.start_task("wf1", 0)
        tracker.complete_task("wf1", 0)
        tracker.start_task("wf1", 1)
        tracker.complete_task("wf1", 1)

        workflow = tracker.get_workflow("wf1")
        assert workflow.overall_progress == 0.5  # 2/4 tasks at 100%

    def test_callback_subscription(self):
        """Test callback subscription"""
        from src.workflow.task_tracker import TaskTracker

        tracker = TaskTracker()
        callback_results = []

        def on_workflow_update(workflow):
            callback_results.append(workflow.workflow_id)

        tracker.subscribe_workflow(on_workflow_update)

        tracker.create_workflow("wf1", "Test", ["Task 1"])
        tracker.start_workflow("wf1")

        assert "wf1" in callback_results

    def test_get_stats(self):
        """Test tracker statistics"""
        from src.workflow.task_tracker import TaskTracker

        tracker = TaskTracker()

        # Create and complete a workflow
        tracker.create_workflow("wf1", "Test", ["Task 1"])
        tracker.start_workflow("wf1")
        tracker.start_task("wf1", 0)
        tracker.complete_task("wf1", 0)
        tracker.complete_workflow("wf1", success=True)

        stats = tracker.get_stats()

        assert stats["workflows_created"] == 1
        assert stats["workflows_completed"] == 1
        assert stats["tasks_completed"] == 1

    def test_workflow_to_dict(self):
        """Test workflow serialization"""
        from src.workflow.task_tracker import TaskTracker

        tracker = TaskTracker()
        tracker.create_workflow("wf1", "Test Workflow", ["Task 1", "Task 2"])
        tracker.start_workflow("wf1")

        workflow = tracker.get_workflow("wf1")
        data = workflow.to_dict()

        assert data["workflow_id"] == "wf1"
        assert data["workflow_name"] == "Test Workflow"
        assert data["total_tasks"] == 2
        assert "tasks" in data


# ============================================================================
# Test 8: WorkflowEngine Checkpoints
# ============================================================================

class TestWorkflowEngineCheckpoints:
    """Test WorkflowEngine checkpoint functionality"""

    def test_workflow_engine_init_with_checkpoints(self):
        """Test WorkflowEngine initialization with checkpoints"""
        from src.workflow.workflow_engine import WorkflowEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = WorkflowEngine(
                enable_checkpoints=True,
                checkpoint_dir=tmpdir
            )
            assert engine.enable_checkpoints is True
            assert engine.checkpoint_dir == tmpdir

    def test_workflow_engine_init_without_checkpoints(self):
        """Test WorkflowEngine initialization without checkpoints"""
        from src.workflow.workflow_engine import WorkflowEngine

        engine = WorkflowEngine(enable_checkpoints=False)
        assert engine.enable_checkpoints is False

    def test_save_checkpoint(self):
        """Test saving a checkpoint"""
        from src.workflow.workflow_engine import WorkflowEngine, TaskStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = WorkflowEngine(
                enable_checkpoints=True,
                checkpoint_dir=tmpdir
            )

            # Create a workflow with some completed tasks
            workflow = engine.create_workflow("test_wf", "Test Workflow")
            workflow.add_task("task1", "Task 1", func=AsyncMock())
            workflow.add_task("task2", "Task 2", func=AsyncMock())

            # Simulate some completion
            workflow.tasks["task1"].status = TaskStatus.COMPLETED
            workflow.tasks["task1"].result = {"data": "result1"}

            # Save checkpoint
            filepath = engine.save_checkpoint(workflow)

            assert filepath is not None
            assert os.path.exists(filepath)

            # Verify file content
            with open(filepath) as f:
                data = json.load(f)

            assert data["workflow_id"] == "test_wf"
            assert "task1" in data["completed_tasks"]
            assert "task2" in data["pending_tasks"]

    def test_load_checkpoint(self):
        """Test loading a checkpoint"""
        from src.workflow.workflow_engine import WorkflowEngine, TaskStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = WorkflowEngine(
                enable_checkpoints=True,
                checkpoint_dir=tmpdir
            )

            # Create and save checkpoint
            workflow = engine.create_workflow("test_wf", "Test Workflow")
            workflow.add_task("task1", "Task 1", func=AsyncMock())
            workflow.tasks["task1"].status = TaskStatus.COMPLETED
            workflow.tasks["task1"].result = "done"

            engine.save_checkpoint(workflow)

            # Load checkpoint
            checkpoint = engine.load_checkpoint("test_wf")

            assert checkpoint is not None
            assert checkpoint.workflow_id == "test_wf"
            assert "task1" in checkpoint.completed_tasks

    def test_load_nonexistent_checkpoint(self):
        """Test loading a non-existent checkpoint"""
        from src.workflow.workflow_engine import WorkflowEngine

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = WorkflowEngine(
                enable_checkpoints=True,
                checkpoint_dir=tmpdir
            )

            checkpoint = engine.load_checkpoint("nonexistent")
            assert checkpoint is None

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint"""
        from src.workflow.workflow_engine import WorkflowEngine, TaskStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = WorkflowEngine(
                enable_checkpoints=True,
                checkpoint_dir=tmpdir
            )

            # Create and save checkpoint
            workflow = engine.create_workflow("test_wf", "Test")
            workflow.add_task("task1", "Task 1", func=AsyncMock())
            workflow.tasks["task1"].status = TaskStatus.COMPLETED

            filepath = engine.save_checkpoint(workflow)
            assert os.path.exists(filepath)

            # Delete
            result = engine.delete_checkpoint("test_wf")
            assert result is True
            assert not os.path.exists(filepath)

    def test_list_checkpoints(self):
        """Test listing all checkpoints"""
        from src.workflow.workflow_engine import WorkflowEngine, TaskStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = WorkflowEngine(
                enable_checkpoints=True,
                checkpoint_dir=tmpdir
            )

            # Create multiple workflows with checkpoints
            for i in range(3):
                workflow = engine.create_workflow(f"wf{i}", f"Workflow {i}")
                workflow.add_task("task1", "Task 1", func=AsyncMock())
                workflow.tasks["task1"].status = TaskStatus.COMPLETED
                engine.save_checkpoint(workflow)

            # List checkpoints
            checkpoints = engine.list_checkpoints()

            assert len(checkpoints) == 3
            ids = [cp.workflow_id for cp in checkpoints]
            assert "wf0" in ids
            assert "wf1" in ids
            assert "wf2" in ids

    def test_checkpoint_disabled(self):
        """Test that checkpoints are not saved when disabled"""
        from src.workflow.workflow_engine import WorkflowEngine

        engine = WorkflowEngine(enable_checkpoints=False)
        workflow = engine.create_workflow("test", "Test")

        result = engine.save_checkpoint(workflow)
        assert result is None

    def test_workflow_checkpoint_serialization(self):
        """Test WorkflowCheckpoint serialization"""
        from src.workflow.workflow_engine import WorkflowCheckpoint

        checkpoint = WorkflowCheckpoint(
            workflow_id="wf1",
            workflow_name="Test",
            mode="dag",
            completed_tasks=["t1", "t2"],
            task_results={"t1": "result1", "t2": "result2"},
            failed_tasks=["t3"],
            pending_tasks=["t4"],
            created_at="2024-01-01T00:00:00",
            metadata={"custom": "data"}
        )

        # To dict
        data = checkpoint.to_dict()
        assert data["workflow_id"] == "wf1"
        assert data["completed_tasks"] == ["t1", "t2"]

        # From dict
        restored = WorkflowCheckpoint.from_dict(data)
        assert restored.workflow_id == "wf1"
        assert restored.completed_tasks == ["t1", "t2"]
        assert restored.metadata == {"custom": "data"}


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components"""

    @pytest.mark.asyncio
    async def test_search_tool_with_caching_integration(self):
        """Test SearchTool caching in realistic scenario"""
        from src.tools.search import SearchTool

        tool = SearchTool(
            provider="serpapi",
            api_key="fake_key",
            cache_enabled=True,
            cache_max_size=10,
            cache_ttl=3600
        )

        # Manually add to cache (simulating a previous search)
        cached_results = [
            {"title": "Test Result", "link": "http://test.com", "snippet": "Test"}
        ]
        tool._cache.set("python tutorial", 5, "serpapi", cached_results)

        # This should return cached results without making API call
        results = await tool.search("python tutorial", num_results=5, use_cache=True)
        assert results == cached_results

    def test_feedback_and_threshold_adjustment(self):
        """Test feedback collection and threshold adjustment"""
        from src.routing.hybrid_router import RoutingFeedbackTracker
        from src.routing.task_types import TaskType

        tracker = RoutingFeedbackTracker()

        # Simulate many incorrect routings
        for i in range(20):
            tracker.record_feedback(
                f"query_{i}",
                TaskType.CHAT,
                correct_task=TaskType.RESEARCH,
                is_correct=False
            )

        # Accuracy should be 0
        assert tracker.get_accuracy() == 0.0

        # Should suggest lowering threshold
        adjustment = tracker.should_adjust_threshold(TaskType.CHAT)
        assert adjustment == -0.1

    def test_task_tracker_full_workflow(self):
        """Test complete workflow through TaskTracker"""
        from src.workflow.task_tracker import TaskTracker, TaskStatus

        tracker = TaskTracker()

        # Create workflow
        workflow = tracker.create_workflow(
            "analysis_wf",
            "Data Analysis Workflow",
            ["Load Data", "Process Data", "Generate Report"]
        )

        # Start workflow
        tracker.start_workflow("analysis_wf")

        # Execute tasks
        for i in range(3):
            tracker.start_task("analysis_wf", i, f"Running task {i+1}")
            tracker.update_task_progress("analysis_wf", i, 0.5)
            tracker.complete_task("analysis_wf", i, result=f"Result {i+1}")

        # Complete workflow
        completed = tracker.complete_workflow("analysis_wf", success=True)

        assert completed.status == TaskStatus.COMPLETED
        assert completed.completed_tasks == 3
        assert completed.failed_tasks == 0

        # Check stats
        stats = tracker.get_stats()
        assert stats["workflows_completed"] == 1
        assert stats["tasks_completed"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
