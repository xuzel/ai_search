"""Test Router classification"""

import pytest
from src.router import Router, TaskType


class TestRouter:
    """Test Router task classification"""

    def test_classify_research_query(self):
        """Test research query classification"""
        queries = [
            "What is machine learning?",
            "Tell me about climate change",
            "查询最新的AI新闻",
            "搜索深度学习应用",
        ]

        for query in queries:
            task_type = Router.classify(query)
            assert task_type == TaskType.RESEARCH, f"Failed for: {query}"

    def test_classify_code_query(self):
        """Test code/math query classification"""
        queries = [
            "Calculate 2^10",
            "Solve x^2 + 5x + 6 = 0",
            "计算斐波那契数列",
            "write code to find prime numbers",
            "Plot sin(x) from 0 to 2π",
        ]

        for query in queries:
            task_type = Router.classify(query)
            assert task_type == TaskType.CODE, f"Failed for: {query}"

    def test_classify_chat_query(self):
        """Test chat query classification"""
        queries = [
            "Hello, how are you?",
            "Tell me a joke",
            "你好，今天天气怎么样？",
        ]

        for query in queries:
            task_type = Router.classify(query)
            # Most of these should default to chat
            assert task_type in [TaskType.CHAT, TaskType.RESEARCH]

    def test_confidence_score(self):
        """Test confidence scoring"""
        query = "Calculate the sum of first 100 prime numbers"
        task_type = Router.classify(query)
        confidence = Router.get_confidence(query, task_type)

        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should have high confidence for code task

    def test_question_mark_detection(self):
        """Test question mark detection"""
        query = "What is the capital of France?"
        task_type = Router.classify(query)

        assert task_type == TaskType.RESEARCH
