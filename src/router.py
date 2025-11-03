"""Task Router - Routes queries to appropriate agents

Supports two classification methods:
1. Keyword-based (fast): Pattern matching and keywords
2. LLM-based (accurate): Uses LLM for semantic understanding
"""

import re
from enum import Enum
from typing import Optional, TYPE_CHECKING

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


class TaskType(Enum):
    """Task type enumeration"""
    RESEARCH = "research"
    CODE = "code"
    CHAT = "chat"
    RAG = "rag"  # Document Q&A
    DOMAIN_WEATHER = "domain_weather"  # Weather queries
    DOMAIN_FINANCE = "domain_finance"  # Stock/finance queries
    DOMAIN_ROUTING = "domain_routing"  # Routing/navigation queries


class Router:
    """Routes queries to appropriate agents"""

    # Keywords for task classification
    RESEARCH_KEYWORDS = [
        "search", "find", "查询", "搜索", "查找", "了解",
        "what is", "who is", "when was", "where is",
        "explain", "tell me about", "information about",
    ]

    CODE_KEYWORDS = [
        "compute", "calculate", "solve", "plot", "draw",
        "计算", "计数", "求解", "画", "绘制",
        "write code", "generate code", "code",
        "数学", "formula", "equation",
        "algorithm", "function", "program",
    ]

    # Domain-specific keywords
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

    # Keywords that suggest calculation/computation (more lenient than CODE_KEYWORDS)
    # These help identify simple math questions like "how many hours in a week"
    CALCULATION_INDICATORS = [
        "多少", "几个", "几", "多长",  # Chinese: how many, how much, how long
        "how many", "how much", "total",  # English
        "convert", "转换", "转",  # Unit conversion
        "average", "平均", "sum", "加起来",  # Aggregation
        "percent", "百分比", "%",  # Percentage calculations
        "is", "等于", "相等",  # Equality (for simple math)
    ]

    MATH_PATTERNS = [
        r'[\+\-\*\/\^]',  # Math operators
        r'[=<>]',  # Comparison operators
        r'\d+\.\d+',  # Decimals
        r'∑|∫|∂|√|π|∞',  # Math symbols
        r'(?:sin|cos|tan|log|sqrt|exp)\s*\(',  # Math functions
    ]

    # Question marks in different languages/character sets
    # English: ? (U+003F)
    # Chinese: ？ (U+FF1F - Full-width question mark)
    QUESTION_MARKS = ['?', '？']

    # Common calculation units and time periods that suggest arithmetic
    # Used to identify questions like "hours in a week", "days in a month"
    UNIT_CONVERSION_PATTERNS = [
        r'(小時|小时|hour|hours?)\s*(?:in|per|a|的)\s*(天|day|星期|week|月|month|年|year)',
        r'(天|day|days?)\s*(?:in|per|a|的)\s*(周|星期|week|月|month|年|year)',
        r'(分鐘|分钟|minute|minutes?)\s*(?:in|per|a|的)\s*(小時|小时|hour|小時)',
    ]

    @staticmethod
    def classify(query: str) -> TaskType:
        """
        Classify a query into a task type

        Priority order:
        1. Explicit CODE keywords (highest priority)
        2. Mathematical patterns (operators, math symbols)
        3. Unit conversion patterns (e.g., "hours in a week")
        4. Calculation indicators (e.g., "how many", "多少")
        5. RESEARCH keywords
        6. Question mark (lowest priority)

        Args:
            query: User query

        Returns:
            TaskType
        """

        query_lower = query.lower().strip()

        # Priority 0: Domain-specific queries (highest priority)
        # Weather queries
        for keyword in Router.WEATHER_KEYWORDS:
            if keyword in query_lower:
                return TaskType.DOMAIN_WEATHER

        # Finance queries (check for stock symbols or finance terms)
        for keyword in Router.FINANCE_KEYWORDS:
            if keyword in query_lower:
                return TaskType.DOMAIN_FINANCE

        # Routing queries
        for keyword in Router.ROUTING_KEYWORDS:
            if keyword in query_lower:
                # Additional check: must have location indicators
                if any(loc in query_lower for loc in ["from", "to", "从", "到", "去"]):
                    return TaskType.DOMAIN_ROUTING

        # RAG/Document queries
        for keyword in Router.RAG_KEYWORDS:
            if keyword in query_lower:
                return TaskType.RAG

        # Priority 1: Explicit CODE keywords
        for keyword in Router.CODE_KEYWORDS:
            if keyword in query_lower:
                return TaskType.CODE

        # Priority 2: Mathematical content + math function names
        has_math_pattern = False
        for pattern in Router.MATH_PATTERNS:
            if re.search(pattern, query):
                has_math_pattern = True
                break

        # If has math symbols or factorial notation, likely code/math task
        if has_math_pattern or "!" in query:
            return TaskType.CODE

        # Priority 3: Unit conversion patterns (time, distance, etc.)
        # Identifies questions like "hours in a week", "小时 in a day"
        for pattern in Router.UNIT_CONVERSION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return TaskType.CODE

        # Priority 4: Calculation indicators (more lenient, catches simple math questions)
        # Identifies "how many", "多少", "几个", etc.
        for indicator in Router.CALCULATION_INDICATORS:
            if indicator in query_lower:
                # Additional check: must have at least some context
                # Check if it looks like a calculation question

                # BUT: Check if it's asking for real-time data (like weather, humidity, current price)
                # These should go to RESEARCH, not CODE
                if any(realtime_kw in query_lower for realtime_kw in [
                    'now', 'current', 'today', 'present', 'real-time', 'live',
                    '現在', '现在', '當下', '当下', '今天', '目前', '實時', '实时'
                ]):
                    # Skip CODE classification, let it fall through to RESEARCH
                    continue

                # Time/unit conversion (not tied to current time)
                if any(unit in query_lower for unit in [
                    'hour', 'day', 'week', 'month', 'year',
                    '小时', '小時', '天', '周', '星期', '月', '年',
                    'second', 'minute', '秒', '分', 'km', 'meter', 'mile',
                    'kilogram', 'pound', 'degree', '度', '米', '克'
                ]):
                    # Make sure it's not asking about "current" real-time values
                    # e.g., "現在有多少濕度" should not match this
                    if 'current' not in query_lower and '現在' not in query and '实时' not in query_lower:
                        return TaskType.CODE

                # Percentage calculations (e.g., "How much is 30% of 500")
                if '%' in query or 'percent' in query_lower or '百分比' in query_lower:
                    return TaskType.CODE

                # Conversion verb (convert X to Y)
                if indicator in ['convert', '转换', '转'] and 'to' in query_lower:
                    return TaskType.CODE

        # Priority 5: RESEARCH keywords
        for keyword in Router.RESEARCH_KEYWORDS:
            if keyword in query_lower:
                return TaskType.RESEARCH

        # Priority 6: Question marks (lowest priority for classification)
        # But if it has math content, it should have been caught above
        # Support question marks in different languages/character sets
        for qmark in Router.QUESTION_MARKS:
            if query.endswith(qmark):
                return TaskType.RESEARCH

        # Default to chat
        return TaskType.CHAT

    @staticmethod
    def get_confidence(query: str, task_type: TaskType) -> float:
        """
        Get confidence score for classification (0.0-1.0)

        Args:
            query: User query
            task_type: Classified task type

        Returns:
            Confidence score
        """

        query_lower = query.lower()
        score = 0.5  # Base score

        if task_type == TaskType.CODE:
            # Boost score for explicit CODE keywords
            for keyword in Router.CODE_KEYWORDS:
                if keyword in query_lower:
                    score += 0.25

            # Boost score for mathematical patterns
            for pattern in Router.MATH_PATTERNS:
                if re.search(pattern, query):
                    score += 0.15

            # Boost score for unit conversion patterns
            for pattern in Router.UNIT_CONVERSION_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 0.2

            # Boost score for calculation indicators
            for indicator in Router.CALCULATION_INDICATORS:
                if indicator in query_lower:
                    score += 0.1

        elif task_type == TaskType.RESEARCH:
            for keyword in Router.RESEARCH_KEYWORDS:
                if keyword in query_lower:
                    score += 0.25
            # Check for question marks in different languages
            for qmark in Router.QUESTION_MARKS:
                if query.endswith(qmark):
                    score += 0.15
                    break

        # Cap at 1.0
        return min(score, 1.0)

    @staticmethod
    async def classify_with_llm(
        query: str,
        llm_manager: "LLMManager",
    ) -> tuple[TaskType, float]:
        """
        Classify query using LLM for semantic understanding.

        This method uses the LLM to understand the intent of the query,
        which is more accurate for ambiguous or complex queries.

        Args:
            query: User query
            llm_manager: LLM manager instance for inference

        Returns:
            Tuple of (TaskType, confidence_score)
        """

        classification_prompt = f"""你是一个查询分类助手。请分析以下用户查询，并判断它属于以下哪个类别：

1. **DOMAIN_WEATHER**: 天气查询
   - 天气、温度、湿度、预报
   - 示例: "北京今天天气", "What's the weather in Tokyo", "会下雨吗"

2. **DOMAIN_FINANCE**: 金融/股票查询
   - 股票价格、市场数据、加密货币
   - 示例: "AAPL股价", "Bitcoin price", "特斯拉今天涨了吗"

3. **DOMAIN_ROUTING**: 路线/导航查询
   - 路线规划、距离、行程时间
   - 示例: "从上海到北京怎么走", "How to get from A to B", "路线距离多远"

4. **RAG**: 文档问答
   - 查询已上传的文档内容
   - 示例: "文档中提到了什么", "这个PDF的主要内容", "分析这份报告"

5. **CODE**: 代码执行/计算问题
   - 数学计算、编程任务
   - 示例: "一周有多少小时", "计算10!", "Convert 2km to miles"

6. **RESEARCH**: 信息查询/网络搜索
   - 需要网络搜索的知识查询
   - 示例: "What is machine learning", "最近的AI突破", "谁发明了电灯"

7. **CHAT**: 常规对话
   - 闲聊、问候
   - 示例: "你好", "Hi there"

用户查询: "{query}"

请按以下JSON格式返回结果（只返回JSON，不要其他内容）：
{{
    "task_type": "DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING|RAG|CODE|RESEARCH|CHAT",
    "confidence": 0.0-1.0,
    "reason": "简短的分类理由"
}}

重要规则:
- 领域专用查询优先级最高（天气、金融、路线、文档）
- 计算问题 → CODE
- 需要网络搜索的知识查询 → RESEARCH
- 含糊不清时倾向于RESEARCH"""

        try:
            response = await llm_manager.complete(
                messages=[
                    {
                        "role": "user",
                        "content": classification_prompt,
                    }
                ],
                temperature=0.3,  # Lower temp for consistency
                max_tokens=200,
            )

            # Parse JSON response
            import json

            # Extract JSON from response (might have extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning(f"LLM returned invalid JSON format: {response}")
                return TaskType.CHAT, 0.5

            result = json.loads(json_match.group())

            task_type_str = result.get("task_type", "CHAT").upper()
            confidence = float(result.get("confidence", 0.5))

            # Map string to TaskType
            task_type_map = {
                "DOMAIN_WEATHER": TaskType.DOMAIN_WEATHER,
                "DOMAIN_FINANCE": TaskType.DOMAIN_FINANCE,
                "DOMAIN_ROUTING": TaskType.DOMAIN_ROUTING,
                "RAG": TaskType.RAG,
                "CODE": TaskType.CODE,
                "RESEARCH": TaskType.RESEARCH,
                "CHAT": TaskType.CHAT,
            }

            return task_type_map.get(task_type_str, TaskType.CHAT), confidence

        except Exception as e:
            logger.error(f"LLM classification failed: {e}, falling back to keyword-based")
            # Fallback to keyword classification
            return Router.classify(query), 0.5

    @staticmethod
    async def classify_hybrid(
        query: str,
        llm_manager: Optional["LLMManager"] = None,
        use_llm_threshold: float = 0.6,
    ) -> tuple[TaskType, float, str]:
        """
        Hybrid classification: uses keyword-based for high confidence cases,
        LLM for ambiguous cases.

        This is the recommended method as it combines speed and accuracy.

        Args:
            query: User query
            llm_manager: Optional LLM manager for uncertain classifications
            use_llm_threshold: Confidence threshold below which to use LLM
                             (default: 0.6, use LLM if keyword confidence < 0.6)

        Returns:
            Tuple of (TaskType, confidence_score, method_used)
        """

        # Step 1: Try keyword-based classification
        task_type = Router.classify(query)
        confidence = Router.get_confidence(query, task_type)

        # Step 2: If confidence is high enough, use keyword result
        if confidence >= use_llm_threshold:
            logger.debug(f"Using keyword-based classification (confidence: {confidence})")
            return task_type, confidence, "keyword"

        # Step 3: If confidence is low and LLM manager available, use LLM
        if llm_manager is not None:
            try:
                logger.debug(f"Keyword confidence too low ({confidence}), using LLM")
                task_type, confidence = await Router.classify_with_llm(
                    query, llm_manager
                )
                return task_type, confidence, "llm"
            except Exception as e:
                logger.error(f"LLM classification failed: {e}, using keyword result")
                return task_type, confidence, "keyword_fallback"

        # Step 4: No LLM available, use keyword result
        logger.debug(f"No LLM available, using keyword result (confidence: {confidence})")
        return task_type, confidence, "keyword"
