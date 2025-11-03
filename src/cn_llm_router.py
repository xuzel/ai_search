"""
中文优化版 LLM-Based 智能路由器 (Chinese-Optimized LLM Router)

这个模块为中文用户提供专门优化的智能路由：
- 中文 prompt 工程
- 中文语言理解
- 适配中文查询习惯
- 支持繁简体
"""

import json
import re
from typing import Optional, Dict, List, Any, TYPE_CHECKING

from src.utils.logger import get_logger
from src.llm_router import (
    TaskType,
    ToolDecision,
    RoutingDecision,
    IntelligentRouter,
)

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


class ChineseIntelligentRouter(IntelligentRouter):
    """
    中文优化的智能路由器，继承自 IntelligentRouter

    特点：
    - 完全中文 prompt 工程
    - 理解中文查询习惯和表达方式
    - 支持繁简体混用
    - 更好的多意图识别
    """

    def _create_routing_prompt(self, query: str, system_context: str) -> str:
        """创建中文优化的路由 prompt"""
        return f"""
请分析以下用户查询，确定最优的路由决策。

{system_context}

## 用户查询
"{query}"

## 可用的任务类型

### 1. 研究模式 (RESEARCH)
网络搜索 + 内容整合
- 需要从互联网查询信息
- 示例：
  * "人工智能的最新突破有哪些？"
  * "如何学习机器学习？"
  * "最近发生了什么新闻？"
- 何时使用：需要最新信息、需要多个来源、需要网络搜索

### 2. 代码执行模式 (CODE)
生成并执行 Python 代码
- 执行数学计算、数据处理、编程任务
- 示例：
  * "计算 2 的 10 次方"
  * "对这个列表排序"
  * "画一个柱状图"
  * "写一个函数来计算斐波那契数列"
- 何时使用：需要计算、编程、数据处理

### 3. 聊天模式 (CHAT)
常规对话
- 闲聊、问候、通用知识
- 示例：
  * "你好"
  * "你是谁？"
  * "讲个笑话"
  * "怎样才能成功？"
- 何时使用：日常对话、需要建议、通用知识

### 4. 文档问答 (RAG)
查询已上传的文档
- 从用户上传的文档中提取信息
- 示例：
  * "这个 PDF 讲了什么？"
  * "文档中的主要观点是什么？"
  * "分析这份报告"
- 何时使用：用户提到了具体文档

### 5. 天气查询 (DOMAIN_WEATHER)
获取天气信息
- 实时天气数据
- 示例：
  * "北京现在天气怎样？"
  * "明天会下雨吗？"
  * "上海的温度是多少？"
- 何时使用：天气相关查询

### 6. 金融数据 (DOMAIN_FINANCE)
股票价格、市场数据
- 金融和加密货币信息
- 示例：
  * "AAPL 股票多少钱？"
  * "比特币价格"
  * "沪深 300 指数"
- 何时使用：金融、股票、加密货币相关

### 7. 路线导航 (DOMAIN_ROUTING)
路线规划、导航
- 地点之间的路线和距离
- 示例：
  * "从北京到上海怎么走？"
  * "这两个地方距离多远？"
  * "怎么从 A 去 B？"
- 何时使用：导航、路线规划

## 可用工具 (可按顺序组合使用)
- **search**: 网络搜索 (SerpAPI)
- **scraper**: 网页内容提取
- **code_executor**: Python 代码执行沙箱
- **weather_api**: 天气数据 (OpenWeatherMap)
- **stock_api**: 股票和金融数据
- **routing_api**: 路线导航服务

## 路由决策指南

### 多意图查询
如果查询包含多个意图，按顺序分解：
- 第一步："搜索关于 X 的文章" (RESEARCH + search)
- 第二步："从中提取关键数据" (CODE + scraper)
- 第三步："计算平均值" (CODE + code_executor)

示例：
- "查找最新的 AI 论文，提取其中的关键指标，然后计算平均值"
  → RESEARCH (search) → CODE (code_executor) → Multi-intent=true

### 置信度评分
- 0.9-1.0: 非常明确的意图
- 0.7-0.9: 明确但有些歧义
- 0.5-0.7: 中等明确，可能需要澄清
- <0.5: 非常不明确，需要追问

### 处理时间估计
- RESEARCH: 3-5 秒 (搜索 + 提取)
- CODE: 1-3 秒 (代码执行)
- CHAT: 0.5-1 秒
- DOMAIN_*: 1-3 秒 (API 调用)

## 中文特殊处理规则

### 1. "是什么" 和 "什么是" 模式
- "什么是人工智能？" → RESEARCH
- "Python 是什么？" → RESEARCH (不是 CODE)
- "这是什么意思？" → CHAT

### 2. "怎样" / "怎么" 模式
- "怎样学习编程？" → RESEARCH (知识)
- "怎么计算?" → CODE (如果有数字/算式)
- "怎么去北京？" → DOMAIN_ROUTING

### 3. "如何" 模式
- "如何使用 Python？" → RESEARCH/CODE (看上下文)
- "如何到达机场？" → DOMAIN_ROUTING

### 4. "目前" / "现在" 强调
- "现在 Bitcoin 多少钱？" → DOMAIN_FINANCE
- "目前天气怎样？" → DOMAIN_WEATHER
- "现在的 AI 进展" → RESEARCH

## 响应格式 (仅返回有效 JSON，无 Markdown，无额外文本)

{{
    "primary_task_type": "RESEARCH|CODE|CHAT|RAG|DOMAIN_WEATHER|DOMAIN_FINANCE|DOMAIN_ROUTING",
    "task_confidence": 0.0-1.0,
    "reasoning": "为什么选择这个任务类型的详细说明",
    "multi_intent": true/false,
    "tools": [
        {{
            "tool_name": "search|scraper|code_executor|weather_api|stock_api|routing_api",
            "confidence": 0.0-1.0,
            "reasoning": "为什么使用这个工具",
            "required_params": {{}},
            "optional_params": {{}}
        }}
    ],
    "follow_up_questions": ["问题1？", "问题2？"],
    "estimated_processing_time": 2.5,
    "notes": "任何额外的注意事项或上下文"
}}

## 中文示例

### 示例 1: 研究查询
用户查询: "Python 有哪些最新的库？"
预期决策:
- primary_task_type: RESEARCH
- task_confidence: 0.95
- tools: [search, scraper]
- multi_intent: false

### 示例 2: 代码计算
用户查询: "计算 100 的阶乘"
预期决策:
- primary_task_type: CODE
- task_confidence: 0.98
- tools: [code_executor]
- multi_intent: false

### 示例 3: 多意图
用户查询: "查找最新的机器学习论文，分析其中的数学公式"
预期决策:
- primary_task_type: RESEARCH
- task_confidence: 0.90
- tools: [search, scraper, code_executor]
- multi_intent: true

### 示例 4: 天气查询
用户查询: "北京现在天气如何，明天需要带伞吗？"
预期决策:
- primary_task_type: DOMAIN_WEATHER
- task_confidence: 0.92
- tools: [weather_api]
- multi_intent: false

### 示例 5: 澄清需求
用户查询: "告诉我关于云的信息"
预期决策:
- primary_task_type: RESEARCH (默认)
- task_confidence: 0.6 (不明确)
- follow_up_questions: ["您是指云计算、天气中的云，还是云存储？"]

现在分析以下用户查询，并提供路由决策：
"""

    def _parse_routing_response(self, response: str, query: str) -> RoutingDecision:
        """解析 LLM 的路由响应（中文版本）"""
        try:
            # 从响应中提取 JSON (LLM 可能包含额外文本)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                logger.warning(f"响应中未找到 JSON: {response[:200]}")
                return self._create_fallback_decision(query)

            data = json.loads(json_match.group())

            # 映射任务类型字符串到枚举
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

            # 解析工具列表
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

            logger.info(
                f"中文路由决策: {primary_task.value} "
                f"(置信度: {data.get('task_confidence', 0.5):.2f})"
            )

            return RoutingDecision(
                primary_task_type=primary_task,
                task_confidence=float(data.get("task_confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                tools_needed=tools_list,
                multi_intent=data.get("multi_intent", False),
                follow_up_questions=data.get("follow_up_questions", []),
                estimated_processing_time=float(
                    data.get("estimated_processing_time", 2.0)
                ),
            )

        except Exception as e:
            logger.error(f"解析路由响应错误: {e}")
            return self._create_fallback_decision(query)


# 中文示例用于改进 LLM 路由
CHINESE_ROUTING_EXAMPLES = [
    {
        "query": "人工智能的最新进展有哪些？",
        "expected_decision": {
            "primary_task_type": "RESEARCH",
            "task_confidence": 0.95,
            "tools": [{"tool_name": "search"}, {"tool_name": "scraper"}],
            "multi_intent": False,
        },
    },
    {
        "query": "计算 2 的 100 次方",
        "expected_decision": {
            "primary_task_type": "CODE",
            "task_confidence": 0.98,
            "tools": [{"tool_name": "code_executor"}],
            "multi_intent": False,
        },
    },
    {
        "query": "查找最新的机器学习论文，提取其中的关键算法",
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
        "query": "北京现在天气怎么样？",
        "expected_decision": {
            "primary_task_type": "DOMAIN_WEATHER",
            "task_confidence": 0.93,
            "tools": [{"tool_name": "weather_api"}],
            "multi_intent": False,
        },
    },
    {
        "query": "什么是区块链？",
        "expected_decision": {
            "primary_task_type": "RESEARCH",
            "task_confidence": 0.90,
            "tools": [{"tool_name": "search"}],
            "multi_intent": False,
        },
    },
    {
        "query": "怎样才能学好编程？",
        "expected_decision": {
            "primary_task_type": "RESEARCH",
            "task_confidence": 0.85,
            "tools": [{"tool_name": "search"}],
            "multi_intent": False,
        },
    },
    {
        "query": "从上海到北京怎么走？",
        "expected_decision": {
            "primary_task_type": "DOMAIN_ROUTING",
            "task_confidence": 0.94,
            "tools": [{"tool_name": "routing_api"}],
            "multi_intent": False,
        },
    },
    {
        "query": "你好",
        "expected_decision": {
            "primary_task_type": "CHAT",
            "task_confidence": 0.99,
            "tools": [],
            "multi_intent": False,
        },
    },
]
