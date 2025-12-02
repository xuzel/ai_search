"""Code Agent - Generates and executes code for solving problems"""

import re
from typing import Any, AsyncGenerator, Dict, Union

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
        self.max_fix_attempts = 3  # Maximum auto-fix retry attempts

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

    async def stream_solve(
        self,
        problem: str,
        auto_fix: bool = True,
    ) -> AsyncGenerator[Union[Dict[str, Any], str], None]:
        """
        Solve a problem with streaming output and optional auto-fix

        Args:
            problem: Problem description
            auto_fix: Whether to automatically fix errors

        Yields:
            - Dict with 'type': 'progress' for stage updates
            - Dict with 'type': 'code' for generated code
            - Dict with 'type': 'output' for execution output
            - Dict with 'type': 'error' for execution errors
            - Dict with 'type': 'fix_attempt' for auto-fix attempts
            - String chunks for streaming explanation
        """
        logger.info(f"Stream solving problem: {problem}")

        # Step 1: Generate code
        yield {"type": "progress", "stage": "generate", "message": "Generating code..."}

        code = await self._generate_code(problem)
        yield {"type": "code", "code": code}

        # Execute with auto-fix loop
        attempt = 0
        current_code = code
        last_error = ""

        while attempt <= self.max_fix_attempts:
            # Validate code
            yield {"type": "progress", "stage": "validate", "message": f"Validating code (attempt {attempt + 1})..."}

            is_valid, validation_error = self.code_executor.validate_code(current_code)

            if not is_valid:
                if auto_fix and attempt < self.max_fix_attempts:
                    yield {
                        "type": "fix_attempt",
                        "attempt": attempt + 1,
                        "error": validation_error,
                        "message": f"Validation failed, attempting fix..."
                    }
                    current_code = await self._fix_code(problem, current_code, validation_error)
                    yield {"type": "code", "code": current_code}
                    attempt += 1
                    continue
                else:
                    yield {"type": "error", "error": validation_error, "stage": "validation"}
                    break

            # Execute code
            yield {"type": "progress", "stage": "execute", "message": "Executing code..."}

            result = await self.code_executor.execute(current_code, show_code=False)

            if result["success"]:
                yield {"type": "output", "output": result["output"]}
                break
            else:
                last_error = result["error"]
                if auto_fix and attempt < self.max_fix_attempts:
                    yield {
                        "type": "fix_attempt",
                        "attempt": attempt + 1,
                        "error": last_error,
                        "message": f"Execution failed, attempting fix..."
                    }
                    current_code = await self._fix_code(problem, current_code, last_error)
                    yield {"type": "code", "code": current_code}
                    attempt += 1
                else:
                    yield {"type": "error", "error": last_error, "stage": "execution"}
                    break

        # Stream explanation
        yield {"type": "progress", "stage": "explain", "message": "Generating explanation..."}

        async for chunk in self._stream_explain_results(
            problem,
            current_code,
            result.get("output", ""),
            result.get("error", last_error),
            result.get("success", False),
        ):
            yield chunk

        yield {"type": "progress", "stage": "complete", "message": "Complete!"}

    async def _fix_code(self, problem: str, code: str, error: str) -> str:
        """
        Use LLM to fix code based on error

        Args:
            problem: Original problem
            code: Code that failed
            error: Error message

        Returns:
            Fixed code
        """
        prompt = f"""You are an expert Python programmer. The following code has an error that needs to be fixed.

Original Problem: {problem}

Code that failed:
```python
{code}
```

Error message:
{error}

Please analyze the error and provide the FIXED Python code only. No explanations, just the corrected code:"""

        messages = [{"role": "user", "content": prompt}]

        try:
            response = await self.llm_manager.complete(messages, max_tokens=2000)

            # Extract code from markdown code blocks if present
            code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                return code_match.group(1)
            elif re.search(r'```\n(.*?)\n```', response, re.DOTALL):
                return re.search(r'```\n(.*?)\n```', response, re.DOTALL).group(1)
            else:
                return response

        except Exception as e:
            logger.error(f"Error fixing code: {e}")
            return code  # Return original code if fix fails

    async def _stream_explain_results(
        self,
        problem: str,
        code: str,
        output: str,
        error: str,
        success: bool,
    ) -> AsyncGenerator[str, None]:
        """Stream explanation of results"""

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

        messages = [{"role": "user", "content": prompt}]

        try:
            async for chunk in self.llm_manager.stream_complete(messages, max_tokens=1000):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming explanation: {e}")
            yield "Unable to explain results"

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
