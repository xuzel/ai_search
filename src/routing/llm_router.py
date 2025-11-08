"""LLM-based Router

Accurate routing using LLM for semantic understanding.
Merges functionality from src/llm_router.py and src/cn_llm_router.py
"""

import json
import re
from typing import Optional, Dict, Any, TYPE_CHECKING

from src.routing.base import BaseRouter, RoutingDecision, ToolRequirement
from src.routing.task_types import TaskType
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


class LLMRouter(BaseRouter):
    """LLM-based router for accurate semantic understanding

    Uses language model to understand query intent, especially useful for:
    - Ambiguous queries
    - Multi-intent queries
    - Natural language understanding
    - Cross-lingual queries

    Supports both English and Chinese prompts based on context.
    """

    def __init__(self, llm_manager: 'LLMManager', config: Optional[Any] = None):
        """Initialize LLM router

        Args:
            llm_manager: LLM manager instance
            config: Optional configuration
        """
        super().__init__(config)
        self.llm_manager = llm_manager

    async def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Route query using LLM

        Args:
            query: User query
            context: Optional context with 'language' key ('zh' or 'en')

        Returns:
            RoutingDecision with detailed analysis
        """
        self.validate_query(query)

        # Determine language for prompt
        language = context.get('language', 'en') if context else 'en'

        # Create routing prompt
        if language == 'zh':
            prompt = self._create_chinese_prompt(query)
        else:
            prompt = self._create_english_prompt(query)

        try:
            # Call LLM
            response = await self.llm_manager.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Low temperature for consistency
                max_tokens=500,
            )

            # Parse JSON response
            result = self._parse_response(response)

            # Build routing decision
            task_type = TaskType.from_string(result.get('task_type', 'chat'))
            confidence = float(result.get('confidence', 0.5))
            reasoning = result.get('reasoning', 'LLM classification')
            tools = self._parse_tools(result.get('tools_needed', []))
            multi_intent = result.get('multi_intent', False)
            alternatives = self._parse_alternatives(result.get('alternative_tasks', []))

            return RoutingDecision(
                query=query,
                primary_task_type=task_type,
                task_confidence=confidence,
                reasoning=reasoning,
                tools_needed=tools,
                multi_intent=multi_intent,
                alternative_task_types=alternatives,
                metadata={
                    "method": "llm",
                    "language": language,
                    "raw_response": result
                }
            )

        except Exception as e:
            logger.error(f"LLM routing failed: {e}", exc_info=True)
            # Fallback to simple classification
            return RoutingDecision(
                query=query,
                primary_task_type=TaskType.CHAT,
                task_confidence=0.3,
                reasoning=f"LLM routing error: {str(e)}, using fallback",
                metadata={"method": "llm_fallback", "error": str(e)}
            )

    def _create_english_prompt(self, query: str) -> str:
        """Create English routing prompt"""
        return f"""You are a query routing assistant. Analyze the following user query and determine the best task type.

## User Query
"{query}"

## Available Task Types

### 1. RESEARCH
Web search + content aggregation
- When: Need latest information, multiple sources, web search
- Examples: "What's new in AI?", "How to learn Python?", "Latest news"

### 2. CODE
Generate and execute Python code
- When: Math calculations, data processing, programming tasks
- Examples: "Calculate 2^10", "Sort this list", "Draw a bar chart"

### 3. CHAT
General conversation
- When: Greetings, casual talk, general advice
- Examples: "Hello", "Who are you?", "Tell me a joke"

### 4. RAG
Query uploaded documents
- When: User mentions specific documents
- Examples: "What does this PDF say?", "Analyze this report"

### 5. DOMAIN_WEATHER
Weather information
- When: Weather-related queries
- Examples: "Weather in Beijing?", "Will it rain tomorrow?"

### 6. DOMAIN_FINANCE
Stock prices, market data
- When: Financial queries
- Examples: "AAPL stock price", "Bitcoin value", "How's the market?"

### 7. DOMAIN_ROUTING
Navigation and directions
- When: Route planning
- Examples: "Directions from A to B", "How to get to the airport?"

## Response Format
Return ONLY valid JSON (no other text):

{{
    "task_type": "RESEARCH|CODE|CHAT|RAG|DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "tools_needed": [
        {{"tool_name": "tool1", "tool_type": "type1", "required": true}}
    ],
    "multi_intent": false,
    "alternative_tasks": ["TASK2", "TASK3"]
}}

Priority Rules:
1. Domain-specific tasks (weather, finance, routing, RAG) - highest priority
2. CODE for calculations and programming
3. RESEARCH for information needs
4. CHAT for general conversation
"""

    def _create_chinese_prompt(self, query: str) -> str:
        """Create Chinese routing prompt with pattern rules"""
        return f"""请分析以下用户查询，确定最优的路由决策。

## 用户查询
"{query}"

## 可用的任务类型

### 1. RESEARCH (研究模式)
网络搜索 + 内容整合
- 何时使用：需要最新信息、多个来源、网络搜索
- 示例："人工智能的最新突破"，"如何学习机器学习"，"最近的新闻"

### 2. CODE (代码执行)
生成并执行 Python 代码
- 何时使用：数学计算、数据处理、编程任务
- 示例："计算 2 的 10 次方"，"排序列表"，"画柱状图"

### 3. CHAT (聊天模式)
常规对话
- 何时使用：闲聊、问候、通用知识
- 示例："你好"，"你是谁"，"讲个笑话"

### 4. RAG (文档问答)
查询已上传的文档
- 何时使用：用户提到具体文档
- 示例："这个 PDF 讲了什么"，"分析这份报告"

### 5. DOMAIN_WEATHER (天气查询)
获取天气信息
- 何时使用：天气相关查询
- 示例："北京天气怎样"，"明天会下雨吗"

### 6. DOMAIN_FINANCE (金融数据)
股票价格、市场数据
- 何时使用：金融查询
- 示例："苹果股价"，"比特币价格"，"股市行情"

### 7. DOMAIN_ROUTING (路线导航)
导航和路线规划
- 何时使用：路线查询
- 示例："从 A 到 B 怎么走"，"去机场的路线"

## 中文特殊处理规则

### "是什么" / "什么是" 模式
- "什么是人工智能？" → RESEARCH
- "Python 是什么？" → RESEARCH (不是 CODE)
- "这是什么意思？" → CHAT

### "怎样" / "怎么" 模式
- "怎样学习编程？" → RESEARCH (知识)
- "怎么计算?" → CODE (如果有数字/算式)
- "怎么去北京？" → DOMAIN_ROUTING

### "如何" 模式
- "如何使用 Python？" → RESEARCH/CODE (看上下文)
- "如何到达机场？" → DOMAIN_ROUTING

### "目前" / "现在" 强调实时性
- "现在 Bitcoin 多少钱？" → DOMAIN_FINANCE
- "目前天气怎样？" → DOMAIN_WEATHER
- "现在的 AI 进展" → RESEARCH

## 返回格式
只返回有效的 JSON（不要其他文字）：

{{
    "task_type": "RESEARCH|CODE|CHAT|RAG|DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING",
    "confidence": 0.0-1.0,
    "reasoning": "简短解释",
    "tools_needed": [
        {{"tool_name": "工具1", "tool_type": "类型1", "required": true}}
    ],
    "multi_intent": false,
    "alternative_tasks": ["任务2", "任务3"]
}}

优先级规则：
1. 领域专用任务（天气、金融、路线、文档）- 最高优先级
2. CODE 用于计算和编程
3. RESEARCH 用于信息查询
4. CHAT 用于日常对话
"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response

        Args:
            response: Raw LLM response

        Returns:
            Parsed dictionary

        Raises:
            ValueError: If response is not valid JSON
        """
        # Extract JSON from response (handle cases where LLM adds extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"No JSON found in response: {response[:100]}")

        try:
            result: Dict[str, Any] = json.loads(json_match.group())
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")

    def _parse_tools(self, tools_data: list) -> list[ToolRequirement]:
        """Parse tools from LLM response"""
        tools = []
        for tool in tools_data:
            if isinstance(tool, dict):
                tools.append(ToolRequirement(
                    tool_name=tool.get('tool_name', ''),
                    tool_type=tool.get('tool_type', ''),
                    required=tool.get('required', True),
                    parameters=tool.get('parameters', {})
                ))
        return tools

    def _parse_alternatives(self, alternatives_data: list) -> list[TaskType]:
        """Parse alternative task types"""
        alternatives = []
        for task in alternatives_data:
            try:
                alternatives.append(TaskType.from_string(task))
            except ValueError:
                logger.warning(f"Invalid alternative task type: {task}")
        return alternatives

    @property
    def name(self) -> str:
        return "LLMRouter"
