"""Code Agent - Generates and executes code for solving problems"""

import json
from typing import Any, Dict, Optional

from src.llm.manager import LLMManager
from src.tools.code_executor import CodeExecutor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeAgent:
    """Code Agent for generating and executing code"""

    def __init__(
        self,
        llm_manager: LLMManager,
        code_executor: CodeExecutor,
        config: Any = None,
    ):
        """
        Initialize Code Agent

        Args:
            llm_manager: LLM Manager instance
            code_executor: Code Executor instance
            config: Configuration object
        """
        self.llm_manager = llm_manager
        self.code_executor = code_executor
        self.config = config

    async def solve(
        self,
        problem: str,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        Solve a problem by generating and executing code

        Args:
            problem: Problem description or math question
            show_progress: Show progress information

        Returns:
            Dict with 'problem', 'code', 'output', 'explanation'
        """

        logger.info(f"Solving problem: {problem}")

        # Step 1: Generate code
        if show_progress:
            print("\n🤖 Analyzing problem and generating code...")

        code = await self._generate_code(problem)

        if show_progress:
            print("✅ Code generated")
            print("\n📝 Generated Code:")
            print("```python")
            print(code)
            print("```")

        # Step 2: Validate code
        if show_progress:
            print("\n🔍 Validating code...")

        is_valid, validation_error = self.code_executor.validate_code(code)
        if not is_valid:
            if show_progress:
                print(f"❌ Code validation failed: {validation_error}")
            return {
                "problem": problem,
                "code": code,
                "output": "",
                "error": validation_error,
                "explanation": "",
                "success": False,
            }

        # Step 3: Execute code
        if show_progress:
            print("\n⚙️ Executing code...")

        result = await self.code_executor.execute(code, show_code=False)

        if result["success"]:
            if show_progress:
                print("✅ Code executed successfully")
                print("\n📊 Output:")
                print(result["output"])
        else:
            if show_progress:
                print("❌ Code execution failed")
                print("\n❌ Error:")
                print(result["error"])

        # Step 4: Explain results
        if show_progress:
            print("\n💡 Analyzing results...")

        explanation = await self._explain_results(
            problem,
            code,
            result["output"],
            result["error"],
            result["success"],
        )

        return {
            "problem": problem,
            "code": code,
            "output": result["output"],
            "error": result["error"],
            "explanation": explanation,
            "success": result["success"],
        }

    async def _generate_code(self, problem: str) -> str:
        """Generate Python code to solve the problem"""

        prompt = f"""You are an expert Python programmer. Write clean, well-commented Python code to solve this problem:

Problem: {problem}

Requirements:
1. Use only standard libraries and common scientific packages (numpy, pandas, scipy, sympy, etc.)
2. Include comments explaining the logic
3. Print results clearly
4. Handle edge cases appropriately

Generate ONLY the Python code, no explanations:"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm_manager.complete(messages, max_tokens=2000)

            # Extract code from markdown code blocks if present
            import re
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            elif re.search(r'```\n(.*?)\n```', response, re.DOTALL):
                return re.search(r'```\n(.*?)\n```', response, re.DOTALL).group(1)
            else:
                return response

        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"# Error generating code: {e}"

    async def _explain_results(
        self,
        problem: str,
        code: str,
        output: str,
        error: str,
        success: bool,
    ) -> str:
        """Explain the results"""

        if success:
            prompt = f"""A Python program was executed to solve this problem:

Problem: {problem}

Code executed:
```python
{code}
```

Output produced:
{output}

Please explain:
1. What the code does
2. What the results mean
3. Any insights or conclusions

Explanation:"""
        else:
            prompt = f"""A Python program failed to solve this problem:

Problem: {problem}

Code executed:
```python
{code}
```

Error: {error}

Please explain:
1. What went wrong
2. Why the error occurred
3. Suggestions for fixing it

Analysis:"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            return await self.llm_manager.complete(messages, max_tokens=1000)
        except Exception as e:
            logger.error(f"Error explaining results: {e}")
            return "Unable to explain results"
