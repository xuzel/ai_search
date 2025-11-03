"""
LLM-Based Intelligent Router with Prompt Engineering

This module provides a sophisticated routing system that uses LLM with prompt
engineering to:
1. Understand user intent
2. Determine optimal agent and tools to use
3. Support multi-intent workflows
4. Provide adaptive routing based on context
"""

import json
import re
from typing import Optional, Dict, List, Tuple, Any, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


class TaskType(Enum):
    """Task type enumeration"""
    RESEARCH = "research"
    CODE = "code"
    CHAT = "chat"
    RAG = "rag"
    DOMAIN_WEATHER = "domain_weather"
    DOMAIN_FINANCE = "domain_finance"
    DOMAIN_ROUTING = "domain_routing"


@dataclass
class ToolDecision:
    """Represents a decision to use a specific tool"""
    tool_name: str  # "search", "code_executor", "scraper", "weather_api", etc.
    confidence: float  # 0.0-1.0
    reasoning: str  # Why this tool was chosen
    required_params: Dict[str, Any]  # Parameters needed for the tool


@dataclass
class RoutingDecision:
    """Complete routing decision from LLM"""
    primary_task_type: TaskType
    task_confidence: float  # 0.0-1.0
    reasoning: str  # Why this task type
    tools_needed: List[ToolDecision]  # Tools to execute in order
    multi_intent: bool  # Whether this query has multiple intents
    follow_up_questions: List[str]  # Clarifying questions if needed
    estimated_processing_time: float  # Seconds, for UX


class IntelligentRouter:
    """
    LLM-based intelligent router that uses prompt engineering
    to determine optimal routing and tool selection.

    Key advantages over keyword-based routing:
    - Understands semantic meaning, not just keywords
    - Can handle complex, ambiguous queries
    - Supports multi-intent workflows
    - Provides reasoning for decisions
    - Adapts to context and conversation history
    """

    def __init__(self, llm_manager: "LLMManager"):
        """Initialize the intelligent router with an LLM manager."""
        self.llm_manager = llm_manager

    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RoutingDecision:
        """
        Route a query using LLM-based intelligent analysis.

        Args:
            query: User query
            context: Optional context about user, environment, etc.
            conversation_history: Previous messages for context

        Returns:
            RoutingDecision with task type, tools, and reasoning
        """
        # Build comprehensive context for the LLM
        system_context = self._build_system_context(context, conversation_history)

        # Create the routing prompt
        routing_prompt = self._create_routing_prompt(query, system_context)

        try:
            # Call LLM for intelligent routing
            response = await self.llm_manager.complete(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert query routing agent. Your job is to analyze user queries and determine the optimal route and tools needed. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": routing_prompt},
                ],
                temperature=0.3,  # Low temp for consistency
                max_tokens=1000,
            )

            # Parse the LLM response
            decision = self._parse_routing_response(response, query)
            logger.info(
                f"Routing decision: {decision.primary_task_type.value} "
                f"(confidence: {decision.task_confidence:.2f})"
            )
            return decision

        except Exception as e:
            logger.error(f"LLM routing failed: {e}, falling back to default")
            # Graceful fallback
            return RoutingDecision(
                primary_task_type=TaskType.CHAT,
                task_confidence=0.5,
                reasoning="Fallback due to LLM error",
                tools_needed=[],
                multi_intent=False,
                follow_up_questions=[],
                estimated_processing_time=1.0,
            )

    def _build_system_context(
        self,
        user_context: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]],
    ) -> str:
        """Build context information to send to the LLM."""
        context_parts = []

        # User context
        if user_context:
            context_parts.append("## User Context")
            context_parts.append(f"- Language: {user_context.get('language', 'unknown')}")
            context_parts.append(f"- Location: {user_context.get('location', 'unknown')}")
            context_parts.append(
                f"- Previous queries: {user_context.get('recent_queries', 0)}"
            )

        # Conversation history
        if conversation_history and len(conversation_history) > 0:
            context_parts.append("## Recent Conversation")
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                context_parts.append(f"- {msg['role'].upper()}: {msg['content'][:100]}")

        return "\n".join(context_parts) if context_parts else "No additional context"

    def _create_routing_prompt(self, query: str, system_context: str) -> str:
        """Create a detailed routing prompt for the LLM."""
        return f"""
Analyze the following user query and determine the optimal routing decision.

{system_context}

## User Query
"{query}"

## Available Task Types
1. **RESEARCH** (Web Search + Synthesis)
   - Need to search the internet for information
   - Examples: "What are the latest AI breakthroughs?", "Recent news about..."
   - Use when: Need current information, need multiple sources

2. **CODE** (Code Generation & Execution)
   - Generate and execute Python code
   - Examples: "Calculate 2^10", "Sort this list", "Plot a graph"
   - Use when: Mathematical computation, data processing, coding tasks

3. **CHAT** (General Conversation)
   - General conversational responses
   - Examples: "Hello", "How are you?", "Tell me a joke"
   - Use when: Small talk, general knowledge, simple questions

4. **RAG** (Document Q&A)
   - Query uploaded documents
   - Examples: "What's in this PDF?", "Analyze the document"
   - Use when: User is asking about specific documents

5. **DOMAIN_WEATHER** (Weather Queries)
   - Get weather information
   - Examples: "What's the weather in Beijing?", "Will it rain?"
   - Use when: Weather-related queries

6. **DOMAIN_FINANCE** (Financial/Stock Data)
   - Stock prices, market data
   - Examples: "AAPL stock price", "Bitcoin price"
   - Use when: Finance-related queries

7. **DOMAIN_ROUTING** (Navigation/Directions)
   - Route planning and navigation
   - Examples: "How to get from A to B?", "Distance to..."
   - Use when: Navigation queries

## Available Tools (can use multiple in sequence)
- **search**: Web search via SerpAPI
- **scraper**: Extract content from web pages
- **code_executor**: Execute Python code in sandbox
- **weather_api**: OpenWeatherMap weather data
- **stock_api**: Financial market data
- **routing_api**: OpenRouteService navigation

## Routing Guidelines

### Multi-Intent Queries
If a query has multiple intents, break it down:
- First: "Find articles about X" (RESEARCH + search)
- Then: "Extract data from them" (CODE + scraper)
- Finally: "Calculate average" (CODE + code_executor)

### Confidence Scoring
- 0.9-1.0: Very clear intent
- 0.7-0.9: Clear but could be ambiguous
- 0.5-0.7: Moderately clear, might need clarification
- <0.5: Very unclear, ask follow-up questions

### Processing Time Estimates
- RESEARCH: 3-5 seconds (search + scrape)
- CODE: 1-3 seconds (execution)
- CHAT: 0.5-1 second
- DOMAIN_*: 1-3 seconds (API call)

## Response Format
Respond ONLY with valid JSON (no markdown, no extra text):

{{
    "primary_task_type": "RESEARCH|CODE|CHAT|RAG|DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING",
    "task_confidence": 0.0-1.0,
    "reasoning": "Why you chose this task type",
    "multi_intent": true/false,
    "tools": [
        {{
            "tool_name": "search|scraper|code_executor|weather_api|stock_api|routing_api",
            "confidence": 0.0-1.0,
            "reasoning": "Why this tool",
            "required_params": {{}},
            "optional_params": {{}}
        }}
    ],
    "follow_up_questions": ["question1?", "question2?"],
    "estimated_processing_time": 2.5
}}

Now analyze the query and provide your routing decision:
"""

    def _parse_routing_response(self, response: str, query: str) -> RoutingDecision:
        """Parse the LLM routing response into a RoutingDecision."""
        try:
            # Extract JSON from response (LLM might include extra text)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                logger.warning(f"No JSON found in response: {response[:200]}")
                return self._create_fallback_decision(query)

            data = json.loads(json_match.group())

            # Map task type string to enum
            task_type_map = {
                "RESEARCH": TaskType.RESEARCH,
                "CODE": TaskType.CODE,
                "CHAT": TaskType.CHAT,
                "RAG": TaskType.RAG,
                "DOMAIN_WEATHER": TaskType.DOMAIN_WEATHER,
                "DOMAIN_FINANCE": TaskType.DOMAIN_FINANCE,
                "DOMAIN_ROUTING": TaskType.DOMAIN_ROUTING,
            }

            primary_task = task_type_map.get(
                data.get("primary_task_type", "CHAT").upper(), TaskType.CHAT
            )

            # Parse tools
            tools_list = []
            for tool_data in data.get("tools", []):
                tools_list.append(
                    ToolDecision(
                        tool_name=tool_data.get("tool_name", ""),
                        confidence=float(tool_data.get("confidence", 0.5)),
                        reasoning=tool_data.get("reasoning", ""),
                        required_params=tool_data.get("required_params", {}),
                    )
                )

            return RoutingDecision(
                primary_task_type=primary_task,
                task_confidence=float(data.get("task_confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                tools_needed=tools_list,
                multi_intent=data.get("multi_intent", False),
                follow_up_questions=data.get("follow_up_questions", []),
                estimated_processing_time=float(data.get("estimated_processing_time", 2.0)),
            )

        except Exception as e:
            logger.error(f"Error parsing routing response: {e}")
            return self._create_fallback_decision(query)

    def _create_fallback_decision(self, query: str) -> RoutingDecision:
        """Create a fallback decision when LLM parsing fails."""
        # Simple heuristic fallback
        query_lower = query.lower()

        if any(word in query_lower for word in ["calculate", "compute", "solve", "计算"]):
            task_type = TaskType.CODE
        elif any(word in query_lower for word in ["search", "find", "查询", "搜索"]):
            task_type = TaskType.RESEARCH
        elif any(word in query_lower for word in ["weather", "天气"]):
            task_type = TaskType.DOMAIN_WEATHER
        else:
            task_type = TaskType.CHAT

        return RoutingDecision(
            primary_task_type=task_type,
            task_confidence=0.6,
            reasoning="Fallback heuristic routing",
            tools_needed=[],
            multi_intent=False,
            follow_up_questions=[],
            estimated_processing_time=2.0,
        )


# Few-shot examples for improved LLM routing
ROUTING_EXAMPLES = [
    {
        "query": "What are the latest breakthroughs in quantum computing?",
        "expected_decision": {
            "primary_task_type": "RESEARCH",
            "task_confidence": 0.95,
            "tools": [{"tool_name": "search"}, {"tool_name": "scraper"}],
            "multi_intent": False,
        },
    },
    {
        "query": "Calculate the factorial of 10 and show the code",
        "expected_decision": {
            "primary_task_type": "CODE",
            "task_confidence": 0.98,
            "tools": [{"tool_name": "code_executor"}],
            "multi_intent": False,
        },
    },
    {
        "query": "Find recent articles about AI safety, extract the main points, and summarize them",
        "expected_decision": {
            "primary_task_type": "RESEARCH",
            "task_confidence": 0.92,
            "tools": [
                {"tool_name": "search"},
                {"tool_name": "scraper"},
                {"tool_name": "code_executor"},
            ],
            "multi_intent": True,
        },
    },
    {
        "query": "What's the weather in Tokyo and should I bring an umbrella?",
        "expected_decision": {
            "primary_task_type": "DOMAIN_WEATHER",
            "task_confidence": 0.93,
            "tools": [{"tool_name": "weather_api"}],
            "multi_intent": False,
        },
    },
    {
        "query": "Find the cheapest flight from NYC to LA next week",
        "expected_decision": {
            "primary_task_type": "RESEARCH",
            "task_confidence": 0.85,
            "tools": [{"tool_name": "search"}],
            "multi_intent": False,
        },
    },
]
