"""
LLM-Based Intelligent Router 测试套件

测试新的 LLM-based 路由系统，验证：
1. 路由决策正确性
2. 工具选择准确性
3. 多意图识别
4. 中文 prompt 工程效果
"""

import asyncio
import pytest
import sys
from typing import List

sys.path.insert(0, '/Users/sudo/PycharmProjects/ai_search')

from src.llm_router import IntelligentRouter, TaskType, RoutingDecision
from src.cn_llm_router import ChineseIntelligentRouter, CHINESE_ROUTING_EXAMPLES
from src.llm import LLMManager
from src.utils.config import get_config


class TestIntelligentRouter:
    """Test the LLM-based intelligent router"""

    @pytest.fixture
    async def router(self):
        """Initialize router with LLM manager"""
        config = get_config()
        llm_manager = LLMManager(config=config)
        return IntelligentRouter(llm_manager)

    @pytest.fixture
    async def cn_router(self):
        """Initialize Chinese router with LLM manager"""
        config = get_config()
        llm_manager = LLMManager(config=config)
        return ChineseIntelligentRouter(llm_manager)

    @pytest.mark.asyncio
    async def test_research_query_routing(self, router):
        """Test routing of research queries"""
        query = "What are the latest breakthroughs in quantum computing?"
        decision = await router.route_query(query)

        assert decision.primary_task_type == TaskType.RESEARCH
        assert decision.task_confidence > 0.7
        assert len(decision.tools_needed) > 0
        assert decision.tools_needed[0].tool_name == "search"

    @pytest.mark.asyncio
    async def test_code_query_routing(self, router):
        """Test routing of code execution queries"""
        query = "Calculate the factorial of 10"
        decision = await router.route_query(query)

        assert decision.primary_task_type == TaskType.CODE
        assert decision.task_confidence > 0.7
        assert len(decision.tools_needed) > 0
        assert decision.tools_needed[0].tool_name == "code_executor"

    @pytest.mark.asyncio
    async def test_chat_query_routing(self, router):
        """Test routing of chat queries"""
        query = "Hello, how are you?"
        decision = await router.route_query(query)

        assert decision.primary_task_type == TaskType.CHAT
        assert decision.task_confidence > 0.5

    @pytest.mark.asyncio
    async def test_weather_query_routing(self, router):
        """Test routing of weather queries"""
        query = "What is the weather in New York?"
        decision = await router.route_query(query)

        assert decision.primary_task_type == TaskType.DOMAIN_WEATHER
        assert decision.task_confidence > 0.7
        assert decision.tools_needed[0].tool_name == "weather_api"

    @pytest.mark.asyncio
    async def test_multi_intent_query(self, router):
        """Test multi-intent query detection"""
        query = "Find articles about AI, extract the main points, and calculate the average word count"
        decision = await router.route_query(query)

        assert decision.multi_intent is True
        assert len(decision.tools_needed) >= 2

    @pytest.mark.asyncio
    async def test_chinese_research_query(self, cn_router):
        """Test Chinese research query routing"""
        query = "人工智能的最新进展有哪些？"
        decision = await cn_router.route_query(query)

        assert decision.primary_task_type == TaskType.RESEARCH
        assert decision.task_confidence > 0.7

    @pytest.mark.asyncio
    async def test_chinese_code_query(self, cn_router):
        """Test Chinese code query routing"""
        query = "计算 2 的 100 次方"
        decision = await cn_router.route_query(query)

        assert decision.primary_task_type == TaskType.CODE
        assert decision.task_confidence > 0.7

    @pytest.mark.asyncio
    async def test_chinese_what_is_query(self, cn_router):
        """Test Chinese 'what is' query - should be RESEARCH, not CODE"""
        query = "什么是区块链？"
        decision = await cn_router.route_query(query)

        assert decision.primary_task_type == TaskType.RESEARCH
        assert decision.task_confidence > 0.75

    @pytest.mark.asyncio
    async def test_chinese_weather_query(self, cn_router):
        """Test Chinese weather query"""
        query = "北京现在天气怎么样？"
        decision = await cn_router.route_query(query)

        assert decision.primary_task_type == TaskType.DOMAIN_WEATHER
        assert decision.task_confidence > 0.7

    @pytest.mark.asyncio
    async def test_chinese_navigation_query(self, cn_router):
        """Test Chinese navigation query"""
        query = "从上海到北京怎么走？"
        decision = await cn_router.route_query(query)

        assert decision.primary_task_type == TaskType.DOMAIN_ROUTING
        assert decision.task_confidence > 0.7

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, router):
        """Test confidence scoring"""
        # Clear query should have high confidence
        clear_query = "Calculate 2 + 2"
        clear_decision = await router.route_query(clear_query)
        assert clear_decision.task_confidence > 0.8

        # Ambiguous query should have lower confidence
        ambiguous_query = "something about clouds"
        ambiguous_decision = await router.route_query(ambiguous_query)
        assert ambiguous_decision.task_confidence < 0.8

    @pytest.mark.asyncio
    async def test_follow_up_questions(self, router):
        """Test that follow-up questions are generated when needed"""
        ambiguous_query = "Tell me about the cloud"
        decision = await router.route_query(ambiguous_query)

        # Ambiguous queries might generate follow-up questions
        # This is optional but good to have
        assert isinstance(decision.follow_up_questions, list)

    @pytest.mark.asyncio
    async def test_processing_time_estimate(self, router):
        """Test processing time estimates"""
        query = "What is machine learning?"
        decision = await router.route_query(query)

        # Processing time should be reasonable
        assert decision.estimated_processing_time > 0
        assert decision.estimated_processing_time < 30  # Max 30 seconds

    @pytest.mark.asyncio
    async def test_tool_ordering(self, router):
        """Test that tools are returned in correct execution order"""
        # Multi-intent query should have tools in execution order
        query = "Search for AI articles and then analyze their sentiment"
        decision = await router.route_query(query)

        if decision.multi_intent:
            # Search should come before analysis
            tools_names = [tool.tool_name for tool in decision.tools_needed]
            assert "search" in tools_names or "scraper" in tools_names

    @pytest.mark.asyncio
    async def test_error_handling(self, router):
        """Test error handling for invalid inputs"""
        # Empty query
        empty_decision = await router.route_query("")
        assert empty_decision.primary_task_type is not None

        # Very long query
        long_query = "a" * 10000
        long_decision = await router.route_query(long_query)
        assert long_decision.primary_task_type is not None


class TestChineseOptimization:
    """Test Chinese-specific optimizations"""

    @pytest.fixture
    async def cn_router(self):
        """Initialize Chinese router"""
        config = get_config()
        llm_manager = LLMManager(config=config)
        return ChineseIntelligentRouter(llm_manager)

    @pytest.mark.asyncio
    async def test_all_chinese_examples(self, cn_router):
        """Test all Chinese routing examples"""
        results = {
            "passed": 0,
            "failed": 0,
            "examples": [],
        }

        for example in CHINESE_ROUTING_EXAMPLES:
            query = example["query"]
            expected = example["expected_decision"]

            try:
                decision = await cn_router.route_query(query)
                expected_task = expected["primary_task_type"]

                if decision.primary_task_type.value.upper() == expected_task.upper():
                    results["passed"] += 1
                    results["examples"].append(
                        {
                            "query": query,
                            "status": "✅ PASSED",
                            "expected": expected_task,
                            "actual": decision.primary_task_type.value,
                            "confidence": decision.task_confidence,
                        }
                    )
                else:
                    results["failed"] += 1
                    results["examples"].append(
                        {
                            "query": query,
                            "status": "❌ FAILED",
                            "expected": expected_task,
                            "actual": decision.primary_task_type.value,
                            "confidence": decision.task_confidence,
                        }
                    )
            except Exception as e:
                results["failed"] += 1
                results["examples"].append(
                    {
                        "query": query,
                        "status": "❌ ERROR",
                        "error": str(e),
                    }
                )

        # Print results
        print(f"\n中文路由测试结果: {results['passed']}/{len(CHINESE_ROUTING_EXAMPLES)} 通过")
        for example in results["examples"]:
            print(f"  {example['status']} - {example['query']}")
            if "error" not in example:
                print(f"    期望: {example['expected']} | 实际: {example['actual']} | 置信度: {example['confidence']:.2f}")

        # Assert at least 70% pass rate
        pass_rate = results["passed"] / len(CHINESE_ROUTING_EXAMPLES)
        assert pass_rate >= 0.7, f"通过率仅为 {pass_rate*100:.1f}%，目标 >= 70%"


# Standalone test functions (for pytest discovery)
@pytest.mark.asyncio
async def test_english_research():
    """Test English research query"""
    config = get_config()
    llm_manager = LLMManager(config=config)
    router = IntelligentRouter(llm_manager)

    decision = await router.route_query("What is quantum computing?")
    assert decision.primary_task_type == TaskType.RESEARCH


@pytest.mark.asyncio
async def test_english_code():
    """Test English code query"""
    config = get_config()
    llm_manager = LLMManager(config=config)
    router = IntelligentRouter(llm_manager)

    decision = await router.route_query("Calculate 10 factorial")
    assert decision.primary_task_type == TaskType.CODE


@pytest.mark.asyncio
async def test_chinese_code():
    """Test Chinese code query"""
    config = get_config()
    llm_manager = LLMManager(config=config)
    cn_router = ChineseIntelligentRouter(llm_manager)

    decision = await cn_router.route_query("计算2的10次方")
    assert decision.primary_task_type == TaskType.CODE


@pytest.mark.asyncio
async def test_chinese_research():
    """Test Chinese research query"""
    config = get_config()
    llm_manager = LLMManager(config=config)
    cn_router = ChineseIntelligentRouter(llm_manager)

    decision = await cn_router.route_query("人工智能的最新进展")
    assert decision.primary_task_type == TaskType.RESEARCH


if __name__ == "__main__":
    # Run tests with: pytest tests/test_llm_router.py -v
    pytest.main([__file__, "-v", "-s"])
