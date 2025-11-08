"""Unit tests for agents module"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents import RAGAgent, ChatAgent


# ============================================================================
# RAGAgent Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
class TestRAGAgent:
    """Test RAGAgent functionality"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM manager"""
        llm = AsyncMock()
        llm.complete = AsyncMock(return_value="This is a test answer based on the context.")
        return llm

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = MagicMock()
        config.rag.chunk_size = 256
        config.rag.chunk_overlap = 50
        config.rag.top_k = 5
        config.rag.similarity_threshold = 0.7
        config.rag.enable_reranking = False
        return config

    @pytest.fixture
    def rag_agent(self, mock_llm, mock_config, tmp_path):
        """Create RAGAgent instance"""
        return RAGAgent(
            llm_manager=mock_llm,
            config=mock_config,
            persist_directory=str(tmp_path / "vector_store")
        )

    @pytest.mark.asyncio
    async def test_ingest_document(self, rag_agent, tmp_path):
        """Test document ingestion"""
        # Create test document
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is test content for RAG system.")

        # Ingest document
        result = await rag_agent.ingest_document(str(test_file))

        assert result is not None
        assert "chunks" in result or "success" in result

    @pytest.mark.asyncio
    async def test_query(self, rag_agent, tmp_path):
        """Test querying RAG system"""
        # Ingest test document first
        test_file = tmp_path / "test.txt"
        test_file.write_text(
            "Python is a high-level programming language. "
            "It is widely used for web development and data science."
        )
        await rag_agent.ingest_document(str(test_file))

        # Query
        result = await rag_agent.query("What is Python?")

        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

    @pytest.mark.asyncio
    async def test_query_with_sources(self, rag_agent, tmp_path):
        """Test query returns sources"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Machine learning is a subset of artificial intelligence.")
        await rag_agent.ingest_document(str(test_file))

        result = await rag_agent.query("What is machine learning?")

        assert "sources" in result
        assert isinstance(result["sources"], list)

    @pytest.mark.asyncio
    async def test_query_empty_store(self, rag_agent):
        """Test querying empty vector store"""
        result = await rag_agent.query("What is Python?")

        # Should return result indicating no documents found
        assert "answer" in result
        # Answer should indicate no context available
        assert "no" in result["answer"].lower() or "not found" in result["answer"].lower()

    @pytest.mark.asyncio
    async def test_clear_documents(self, rag_agent, tmp_path):
        """Test clearing documents"""
        # Ingest document
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        await rag_agent.ingest_document(str(test_file))

        # Clear
        rag_agent.clear_documents()

        # Query should return no results
        result = await rag_agent.query("test")
        assert "sources" in result
        assert len(result.get("sources", [])) == 0

    @pytest.mark.asyncio
    async def test_get_relevant_context(self, rag_agent, tmp_path):
        """Test retrieving relevant context"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Deep learning uses neural networks for pattern recognition.")
        await rag_agent.ingest_document(str(test_file))

        # Get context
        context = await rag_agent.get_relevant_context("neural networks")

        assert isinstance(context, (list, str))
        if isinstance(context, list):
            assert len(context) > 0
        else:
            assert len(context) > 0


# ============================================================================
# ChatAgent Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
class TestChatAgent:
    """Test ChatAgent functionality"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM manager"""
        llm = AsyncMock()
        llm.complete = AsyncMock(return_value="Hello! How can I help you today?")
        return llm

    @pytest.fixture
    def chat_agent(self, mock_llm):
        """Create ChatAgent instance"""
        return ChatAgent(llm_manager=mock_llm)

    @pytest.mark.asyncio
    async def test_chat_basic(self, chat_agent):
        """Test basic chat functionality"""
        response = await chat_agent.chat("Hello")

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_history(self, chat_agent, mock_llm):
        """Test chat with conversation history"""
        # First message
        response1 = await chat_agent.chat("My name is Alice")
        assert len(response1) > 0

        # Second message referencing first
        mock_llm.complete.return_value = "Nice to meet you, Alice!"
        response2 = await chat_agent.chat("What's my name?")

        assert isinstance(response2, str)
        # Should have context from previous message
        assert len(chat_agent.conversation_history) >= 2

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, chat_agent):
        """Test chat with empty message"""
        with pytest.raises((ValueError, Exception)):
            await chat_agent.chat("")

    @pytest.mark.asyncio
    async def test_clear_history(self, chat_agent):
        """Test clearing conversation history"""
        await chat_agent.chat("Hello")
        await chat_agent.chat("How are you?")

        # Clear history
        chat_agent.clear_history()

        assert len(chat_agent.conversation_history) == 0

    @pytest.mark.asyncio
    async def test_get_history(self, chat_agent):
        """Test getting conversation history"""
        await chat_agent.chat("First message")
        await chat_agent.chat("Second message")

        history = chat_agent.get_history()

        assert isinstance(history, list)
        assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, chat_agent, mock_llm):
        """Test chat with custom system prompt"""
        system_prompt = "You are a helpful coding assistant."

        response = await chat_agent.chat(
            "Help me with Python",
            system_prompt=system_prompt
        )

        assert isinstance(response, str)
        # Verify system prompt was used (check mock was called)
        assert mock_llm.complete.called

    @pytest.mark.asyncio
    async def test_chat_max_history(self, chat_agent):
        """Test chat history limit"""
        # Send many messages
        for i in range(20):
            await chat_agent.chat(f"Message {i}")

        history = chat_agent.get_history()

        # History should be limited (exact limit depends on implementation)
        assert len(history) <= 20  # Reasonable max history size

    @pytest.mark.asyncio
    async def test_chat_handles_llm_error(self, chat_agent, mock_llm):
        """Test chat handles LLM errors gracefully"""
        mock_llm.complete.side_effect = Exception("LLM error")

        with pytest.raises(Exception):
            await chat_agent.chat("Hello")


# ============================================================================
# Agent Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentIntegration:
    """Integration tests for agents"""

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
    async def test_rag_agent_end_to_end(self, llm_manager, config, tmp_path):
        """Test RAG agent end-to-end"""
        rag_agent = RAGAgent(
            llm_manager=llm_manager,
            config=config,
            persist_directory=str(tmp_path / "rag_test")
        )

        # Create test document
        test_file = tmp_path / "test_doc.txt"
        test_file.write_text(
            "FastAPI is a modern web framework for Python. "
            "It is based on standard Python type hints and is very fast."
        )

        # Ingest and query
        await rag_agent.ingest_document(str(test_file))
        result = await rag_agent.query("What is FastAPI?")

        assert "answer" in result
        assert "fastapi" in result["answer"].lower() or "fast" in result["answer"].lower()

    @pytest.mark.asyncio
    async def test_chat_agent_end_to_end(self, llm_manager):
        """Test chat agent end-to-end"""
        chat_agent = ChatAgent(llm_manager=llm_manager)

        response = await chat_agent.chat("Say hello in one word")

        assert isinstance(response, str)
        assert len(response) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
