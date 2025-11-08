"""Task Decomposer - Breaks down complex queries into subtasks

Uses LLM to understand complex queries and generate step-by-step execution plans.
"""

import json
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


@dataclass
class SubTask:
    """
    Represents a subtask in a decomposed plan

    Attributes:
        id: Unique subtask identifier
        description: What this subtask does
        tool: Tool/agent to use (search, code, rag, weather, etc.)
        query: Query/input for the tool
        dependencies: List of subtask IDs this depends on
        output_variable: Variable name to store result
    """
    id: str
    description: str
    tool: str
    query: str
    dependencies: List[str]
    output_variable: str


@dataclass
class TaskPlan:
    """
    Execution plan for a complex task

    Attributes:
        original_query: The original user query
        goal: High-level goal/objective
        subtasks: List of subtasks to execute
        estimated_steps: Number of steps
        complexity: Complexity level (low, medium, high)
    """
    original_query: str
    goal: str
    subtasks: List[SubTask]
    estimated_steps: int
    complexity: str


class TaskDecomposer:
    """
    Decomposes complex queries into executable subtasks

    Example:
        decomposer = TaskDecomposer(llm_manager)
        plan = await decomposer.decompose(
            "Compare weather in Beijing and Tokyo, then find cheapest flight"
        )

        # Returns plan with subtasks:
        # 1. Get weather in Beijing (weather tool)
        # 2. Get weather in Tokyo (weather tool)
        # 3. Compare weather (code/chat)
        # 4. Search for flights (search)
        # 5. Analyze flight prices (code)
    """

    # Available tools/agents
    AVAILABLE_TOOLS = {
        "search": "Web search for information",
        "code": "Execute Python code for calculations",
        "chat": "General conversation and reasoning",
        "rag": "Query documents and knowledge base",
        "weather": "Get weather information",
        "finance": "Get stock and financial data",
        "routing": "Get route and navigation information",
        "vision": "Analyze images",
        "ocr": "Extract text from images",
    }

    def __init__(
        self,
        llm_manager: "LLMManager",
        max_subtasks: int = 10,
    ):
        """
        Initialize Task Decomposer

        Args:
            llm_manager: LLM manager for query understanding
            max_subtasks: Maximum number of subtasks to generate
        """
        self.llm_manager = llm_manager
        self.max_subtasks = max_subtasks

        logger.info("TaskDecomposer initialized")

    async def decompose(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskPlan:
        """
        Decompose a complex query into subtasks

        Args:
            query: User query
            context: Optional context (previous results, user preferences, etc.)

        Returns:
            TaskPlan with subtasks
        """
        logger.info(f"Decomposing query: {query}")

        # Build prompt
        prompt = self._build_decomposition_prompt(query, context)

        try:
            # Get LLM response
            response = await self.llm_manager.complete(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent planning
                max_tokens=1500,
            )

            # Parse JSON response
            plan = self._parse_plan(query, response)

            logger.info(
                f"Decomposed query into {len(plan.subtasks)} subtasks "
                f"(complexity: {plan.complexity})"
            )

            return plan

        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")

            # Fallback: create simple single-task plan
            return self._create_fallback_plan(query)

    def _build_decomposition_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build LLM prompt for task decomposition"""

        tools_description = "\n".join(
            f"- {name}: {desc}" for name, desc in self.AVAILABLE_TOOLS.items()
        )

        context_str = ""
        if context:
            context_str = f"\n\nContext:\n{json.dumps(context, indent=2)}"

        prompt = f"""You are a task planning assistant. Analyze the user's query and break it down into a sequence of subtasks.

User Query: "{query}"{context_str}

Available Tools:
{tools_description}

Instructions:
1. Understand the user's goal
2. Break down the task into logical subtasks (max {self.max_subtasks})
3. For each subtask:
   - Assign an ID (step1, step2, etc.)
   - Write a clear description
   - Choose the appropriate tool
   - Specify the query/input for that tool
   - List dependencies (IDs of subtasks that must complete first)
   - Assign an output variable name

4. Return ONLY a JSON response (no other text) in this format:
{{
    "goal": "High-level objective",
    "complexity": "low|medium|high",
    "subtasks": [
        {{
            "id": "step1",
            "description": "What this step does",
            "tool": "search|code|chat|rag|weather|finance|routing|vision|ocr",
            "query": "Input for the tool",
            "dependencies": [],
            "output_variable": "result1"
        }},
        {{
            "id": "step2",
            "description": "What this step does",
            "tool": "code",
            "query": "Calculate using {{{{result1}}}}",
            "dependencies": ["step1"],
            "output_variable": "result2"
        }}
    ]
}}

Guidelines:
- Use dependencies wisely (only when output from one task is needed by another)
- Keep queries specific and actionable
- Choose the most appropriate tool for each subtask
- For simple queries, use 1-2 subtasks
- For complex queries, break into logical steps
- Use {{variable_name}} in queries to reference previous results

Examples:

Query: "What's the weather in Beijing?"
{{
    "goal": "Get current weather in Beijing",
    "complexity": "low",
    "subtasks": [
        {{
            "id": "step1",
            "description": "Get current weather in Beijing",
            "tool": "weather",
            "query": "Beijing",
            "dependencies": [],
            "output_variable": "weather_data"
        }}
    ]
}}

Query: "Compare AAPL and TSLA stock prices and tell me which is better value"
{{
    "goal": "Compare stock prices and determine better value",
    "complexity": "medium",
    "subtasks": [
        {{
            "id": "step1",
            "description": "Get AAPL stock price",
            "tool": "finance",
            "query": "AAPL",
            "dependencies": [],
            "output_variable": "aapl_price"
        }},
        {{
            "id": "step2",
            "description": "Get TSLA stock price",
            "tool": "finance",
            "query": "TSLA",
            "dependencies": [],
            "output_variable": "tsla_price"
        }},
        {{
            "id": "step3",
            "description": "Search for PE ratios and fundamental data",
            "tool": "search",
            "query": "AAPL TSLA PE ratio earnings comparison 2025",
            "dependencies": [],
            "output_variable": "fundamental_data"
        }},
        {{
            "id": "step4",
            "description": "Analyze and compare stocks",
            "tool": "chat",
            "query": "Compare AAPL ({{{{aapl_price}}}}) and TSLA ({{{{tsla_price}}}}) using this data: {{{{fundamental_data}}}}. Which is better value?",
            "dependencies": ["step1", "step2", "step3"],
            "output_variable": "comparison"
        }}
    ]
}}

Now analyze the user's query and create a task plan:"""

        return prompt

    def _parse_plan(self, original_query: str, response: str) -> TaskPlan:
        """Parse LLM response into TaskPlan"""

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in LLM response")

        data = json.loads(json_match.group())

        # Parse subtasks
        subtasks = []
        for subtask_data in data.get("subtasks", []):
            subtask = SubTask(
                id=subtask_data["id"],
                description=subtask_data["description"],
                tool=subtask_data["tool"],
                query=subtask_data["query"],
                dependencies=subtask_data.get("dependencies", []),
                output_variable=subtask_data.get("output_variable", subtask_data["id"]),
            )
            subtasks.append(subtask)

        # Create plan
        plan = TaskPlan(
            original_query=original_query,
            goal=data.get("goal", "Complete user request"),
            subtasks=subtasks,
            estimated_steps=len(subtasks),
            complexity=data.get("complexity", "medium"),
        )

        return plan

    def _create_fallback_plan(self, query: str) -> TaskPlan:
        """Create a simple fallback plan when decomposition fails"""

        logger.warning("Using fallback plan")

        # Try to guess the best tool based on keywords
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["weather", "temperature", "天气"]):
            tool = "weather"
        elif any(kw in query_lower for kw in ["stock", "price", "股票"]):
            tool = "finance"
        elif any(kw in query_lower for kw in ["route", "direction", "路线"]):
            tool = "routing"
        elif any(kw in query_lower for kw in ["calculate", "compute", "计算"]):
            tool = "code"
        elif any(kw in query_lower for kw in ["document", "文档", "pdf"]):
            tool = "rag"
        else:
            tool = "search"

        subtask = SubTask(
            id="step1",
            description=f"Execute user query using {tool}",
            tool=tool,
            query=query,
            dependencies=[],
            output_variable="result",
        )

        return TaskPlan(
            original_query=query,
            goal="Execute user query",
            subtasks=[subtask],
            estimated_steps=1,
            complexity="low",
        )

    def optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        Optimize task plan (remove redundancies, parallelize where possible)

        Args:
            plan: Original task plan

        Returns:
            Optimized task plan

        Note:
            Currently returns plan as-is. Future optimizations could include:
            - Detecting and removing duplicate tasks
            - Identifying tasks that can run in parallel
            - Reordering tasks for efficiency
            - Merging similar tasks
        """
        # Return plan as-is (optimizations deferred to future versions)
        return plan

    def visualize_plan(self, plan: TaskPlan) -> str:
        """
        Create a text visualization of the task plan

        Args:
            plan: Task plan

        Returns:
            Text representation
        """
        lines = [
            f"Task Plan: {plan.goal}",
            f"Complexity: {plan.complexity}",
            f"Steps: {plan.estimated_steps}",
            "",
        ]

        for i, subtask in enumerate(plan.subtasks, 1):
            deps = f" (depends on: {', '.join(subtask.dependencies)})" if subtask.dependencies else ""
            lines.append(
                f"{i}. [{subtask.tool}] {subtask.description}{deps}\n"
                f"   Query: {subtask.query}\n"
                f"   Output: {subtask.output_variable}"
            )
            lines.append("")

        return "\n".join(lines)
