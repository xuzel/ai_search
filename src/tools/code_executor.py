"""Code Execution Tool - Safe Python code execution"""

import asyncio
import subprocess
import tempfile
import uuid
from typing import Dict, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CodeExecutor:
    """Safe code execution with timeout and resource limits"""

    def __init__(self, timeout: int = 30, max_output_lines: int = 1000):
        """
        Initialize Code Executor

        Args:
            timeout: Execution timeout in seconds
            max_output_lines: Maximum output lines to capture
        """
        self.timeout = timeout
        self.max_output_lines = max_output_lines

    async def execute(
        self,
        code: str,
        show_code: bool = True,
    ) -> Dict[str, str]:
        """
        Execute Python code safely

        Args:
            code: Python code to execute
            show_code: Whether to include code in result

        Returns:
            Dict with 'code', 'output', 'error', 'success'
        """

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=None,
        )

        try:
            temp_file.write(code)
            temp_file.close()

            # Execute in subprocess
            result = await self._run_subprocess(temp_file.name)

            return {
                "code": code if show_code else "",
                "output": result[0],
                "error": result[1],
                "success": result[2],
            }

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "code": code if show_code else "",
                "output": "",
                "error": str(e),
                "success": False,
            }

        finally:
            import os
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.debug(f"Failed to delete temp file: {e}")

    async def _run_subprocess(self, script_path: str) -> Tuple[str, str, bool]:
        """
        Run Python script in subprocess with timeout

        Args:
            script_path: Path to Python script

        Returns:
            Tuple of (stdout, stderr, success)
        """

        try:
            process = await asyncio.create_subprocess_exec(
                'python3',
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return "", f"Execution timeout (>{self.timeout}s)", False

            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            # Limit output
            stdout_lines = stdout_str.split('\n')[:self.max_output_lines]
            stdout_str = '\n'.join(stdout_lines)

            success = process.returncode == 0
            return stdout_str, stderr_str, success

        except Exception as e:
            return "", str(e), False

    def validate_code(self, code: str, allowed_imports: Optional[list] = None) -> Tuple[bool, str]:
        """
        Validate code for safety (basic checks)

        Args:
            code: Code to validate
            allowed_imports: List of allowed import names

        Returns:
            Tuple of (is_valid, error_message)
        """

        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "open(",
            "input(",
            "system(",
            "os.remove",
            "os.rmdir",
            "rmtree",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"

        # Check imports if allowed_imports is specified
        if allowed_imports is not None:
            import re
            imports = re.findall(r'^\s*(?:import|from)\s+(\w+)', code, re.MULTILINE)
            for imp in imports:
                if imp not in allowed_imports and imp != "__main__":
                    return False, f"Import not allowed: {imp}"

        return True, ""
