"""Keyword-based Router

Fast routing using pattern matching and keyword detection.
Migrated from src/router.py with improved structure.
"""

import re
from typing import Optional, Dict, Any

from src.routing.base import BaseRouter, RoutingDecision, ToolRequirement
from src.routing.task_types import TaskType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeywordRouter(BaseRouter):
    """Fast keyword-based query routing

    Uses pattern matching and keyword detection for quick classification.
    Suitable for common queries where intent is clear.
    """

    # Keywords for task classification
    RESEARCH_KEYWORDS = [
        "search", "find", "查询", "搜索", "查找", "了解",
        "what is", "who is", "when was", "where is",
        "是什么", "什么是",
        "explain", "tell me about", "information about",
    ]

    CODE_KEYWORDS = [
        "compute", "calculate", "solve", "plot", "draw",
        "计算", "计数", "求解", "画", "绘制",
        "write code", "generate code", "code",
        "数学", "formula", "equation",
        "algorithm", "function", "program",
    ]

    RAG_KEYWORDS = [
        "document", "file", "pdf", "analyze document",
        "文档", "文件", "分析文档", "文档中",
    ]

    WEATHER_KEYWORDS = [
        "weather", "temperature", "humidity", "forecast", "rain", "snow",
        "天气", "温度", "湿度", "预报", "下雨", "下雪", "气温",
        "climate", "气候",
    ]

    FINANCE_KEYWORDS = [
        "stock", "price", "market", "ticker", "shares", "nasdaq", "dow",
        "股票", "股价", "市场", "股市", "证券", "涨", "跌",
        "crypto", "bitcoin", "ethereum", "加密货币", "比特币",
        "trading", "交易", "投资",
    ]

    ROUTING_KEYWORDS = [
        "route", "direction", "navigate", "travel", "driving", "distance",
        "路线", "导航", "行驶", "距离", "怎么走", "怎么去",
        "from", "to", "从", "到", "去",
    ]

    CALCULATION_INDICATORS = [
        "多少", "几个", "几", "多长",
        "how many", "how much", "total",
        "convert", "转换", "转",
        "average", "平均", "sum", "加起来",
        "percent", "百分比", "%",
        "is", "等于", "相等",
    ]

    MATH_PATTERNS = [
        r'[\+\-\*\/\^]',
        r'[=<>]',
        r'\d+\.\d+',
        r'∑|∫|∂|√|π|∞',
        r'(?:sin|cos|tan|log|sqrt|exp)\s*\(',
    ]

    QUESTION_MARKS = ['?', '？']

    UNIT_CONVERSION_PATTERNS = [
        r'(小時|小时|hour|hours?)\s*(?:in|per|a|的)\s*(天|day|星期|week|月|month|年|year)',
        r'(天|day|days?)\s*(?:in|per|a|的)\s*(周|星期|week|月|month|年|year)',
        r'(分鐘|分钟|minute|minutes?)\s*(?:in|per|a|的)\s*(小時|小时|hour|小時)',
    ]

    async def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Route query using keyword matching

        Args:
            query: User query
            context: Optional context (unused in keyword routing)

        Returns:
            RoutingDecision with task type and confidence
        """
        self.validate_query(query)

        # Classify using keyword patterns
        task_type = self._classify(query)
        confidence = self._get_confidence(query, task_type)
        reasoning = self._get_reasoning(query, task_type)
        tools = self._get_required_tools(task_type)

        return RoutingDecision(
            query=query,
            primary_task_type=task_type,
            task_confidence=confidence,
            reasoning=reasoning,
            tools_needed=tools,
            metadata={"method": "keyword"}
        )

    def _classify(self, query: str) -> TaskType:
        """Classify query into task type

        Priority order:
        1. Domain-specific (weather, finance, routing, RAG)
        2. Explicit CODE keywords
        3. Mathematical patterns
        4. Unit conversion patterns
        5. Calculation indicators
        6. RESEARCH keywords
        7. Question marks
        8. Default to CHAT
        """
        query_lower = query.lower().strip()

        # Priority 0: Domain-specific
        for keyword in self.WEATHER_KEYWORDS:
            if keyword in query_lower:
                return TaskType.DOMAIN_WEATHER

        for keyword in self.FINANCE_KEYWORDS:
            if keyword in query_lower:
                return TaskType.DOMAIN_FINANCE

        for keyword in self.ROUTING_KEYWORDS:
            if keyword in query_lower:
                if any(loc in query_lower for loc in ["from", "to", "从", "到", "去"]):
                    return TaskType.DOMAIN_ROUTING

        for keyword in self.RAG_KEYWORDS:
            if keyword in query_lower:
                return TaskType.RAG

        # Priority 1: Explicit CODE keywords
        for keyword in self.CODE_KEYWORDS:
            if keyword in query_lower:
                return TaskType.CODE

        # Priority 2: Mathematical patterns
        has_math_pattern = any(re.search(pattern, query) for pattern in self.MATH_PATTERNS)
        if has_math_pattern or "!" in query:
            return TaskType.CODE

        # Priority 3: Unit conversion
        for pattern in self.UNIT_CONVERSION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return TaskType.CODE

        # Priority 4: Calculation indicators
        for indicator in self.CALCULATION_INDICATORS:
            if indicator in query_lower:
                # Skip if asking for real-time data
                if any(kw in query_lower for kw in [
                    'now', 'current', 'today', 'present', 'real-time', 'live',
                    '現在', '现在', '當下', '当下', '今天', '目前', '實時', '实时'
                ]):
                    continue

                # Time/unit conversion
                if any(unit in query_lower for unit in [
                    'hour', 'day', 'week', 'month', 'year',
                    '小时', '小時', '天', '周', '星期', '月', '年',
                    'second', 'minute', '秒', '分', 'km', 'meter', 'mile',
                    'kilogram', 'pound', 'degree', '度', '米', '克'
                ]):
                    if not any(kw in query_lower for kw in ['current', '現在', '实时']):
                        return TaskType.CODE

                # Percentage calculations
                if '%' in query or 'percent' in query_lower or '百分比' in query_lower:
                    return TaskType.CODE

                # Conversion verb
                if indicator in ['convert', '转换', '转'] and 'to' in query_lower:
                    return TaskType.CODE

        # Priority 5: RESEARCH keywords
        for keyword in self.RESEARCH_KEYWORDS:
            if keyword in query_lower:
                return TaskType.RESEARCH

        # Priority 6: Question marks
        for qmark in self.QUESTION_MARKS:
            if query.endswith(qmark):
                return TaskType.RESEARCH

        # Default to CHAT
        return TaskType.CHAT

    def _get_confidence(self, query: str, task_type: TaskType) -> float:
        """Calculate confidence score for classification"""
        query_lower = query.lower()
        score = 0.5  # Base score

        if task_type == TaskType.CODE:
            for keyword in self.CODE_KEYWORDS:
                if keyword in query_lower:
                    score += 0.25
            for pattern in self.MATH_PATTERNS:
                if re.search(pattern, query):
                    score += 0.15
            for pattern in self.UNIT_CONVERSION_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 0.2
            for indicator in self.CALCULATION_INDICATORS:
                if indicator in query_lower:
                    score += 0.1

        elif task_type == TaskType.RESEARCH:
            for keyword in self.RESEARCH_KEYWORDS:
                if keyword in query_lower:
                    score += 0.25
            for qmark in self.QUESTION_MARKS:
                if query.endswith(qmark):
                    score += 0.15
                    break

        elif task_type in (TaskType.DOMAIN_WEATHER, TaskType.DOMAIN_FINANCE, TaskType.DOMAIN_ROUTING):
            # High confidence for domain-specific matches
            score += 0.3

        return min(score, 1.0)

    def _get_reasoning(self, query: str, task_type: TaskType) -> str:
        """Generate reasoning for classification decision"""
        query_lower = query.lower()

        if task_type == TaskType.DOMAIN_WEATHER:
            matched = [kw for kw in self.WEATHER_KEYWORDS if kw in query_lower]
            return f"Weather keywords detected: {', '.join(matched[:3])}"

        elif task_type == TaskType.DOMAIN_FINANCE:
            matched = [kw for kw in self.FINANCE_KEYWORDS if kw in query_lower]
            return f"Finance keywords detected: {', '.join(matched[:3])}"

        elif task_type == TaskType.DOMAIN_ROUTING:
            return "Routing keywords detected with location indicators"

        elif task_type == TaskType.CODE:
            reasons = []
            if any(kw in query_lower for kw in self.CODE_KEYWORDS):
                reasons.append("code keywords")
            if any(re.search(p, query) for p in self.MATH_PATTERNS):
                reasons.append("math operators")
            if any(re.search(p, query, re.IGNORECASE) for p in self.UNIT_CONVERSION_PATTERNS):
                reasons.append("unit conversion")
            return f"Code execution required: {', '.join(reasons)}" if reasons else "Math/code query"

        elif task_type == TaskType.RESEARCH:
            matched = [kw for kw in self.RESEARCH_KEYWORDS if kw in query_lower]
            if matched:
                return f"Research keywords: {', '.join(matched[:3])}"
            return "Question pattern detected"

        elif task_type == TaskType.RAG:
            return "Document analysis keywords detected"

        else:
            return "General conversation"

    def _get_required_tools(self, task_type: TaskType) -> list[ToolRequirement]:
        """Determine required tools for task type"""
        tools_map = {
            TaskType.RESEARCH: [
                ToolRequirement("search_tool", "search", required=True),
                ToolRequirement("scraper_tool", "web_scraper", required=True),
            ],
            TaskType.CODE: [
                ToolRequirement("code_executor", "code_execution", required=True),
            ],
            TaskType.DOMAIN_WEATHER: [
                ToolRequirement("weather_tool", "weather_api", required=True),
            ],
            TaskType.DOMAIN_FINANCE: [
                ToolRequirement("finance_tool", "finance_api", required=True),
            ],
            TaskType.DOMAIN_ROUTING: [
                ToolRequirement("routing_tool", "routing_api", required=True),
            ],
            TaskType.RAG: [
                ToolRequirement("vector_store", "embedding_db", required=True),
                ToolRequirement("document_processor", "doc_processor", required=True),
            ],
        }

        return tools_map.get(task_type, [])

    @property
    def name(self) -> str:
        return "KeywordRouter"
