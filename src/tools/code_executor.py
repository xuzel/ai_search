"""Code Execution Tool - Multi-layer secure Python code execution

This module provides secure code execution with three layers of protection:

Layer 1: AST-based Code Validation
    - Analyzes code structure before execution
    - Detects dangerous patterns (eval, exec, file operations)
    - Prevents import of blacklisted modules
    - Cannot be bypassed with obfuscation

Layer 2: Docker Sandbox (if available)
    - Isolated container execution
    - Resource limits (CPU, memory)
    - Network isolation
    - Read-only filesystem
    - Runs as unprivileged user

Layer 3: Subprocess with Timeout
    - Fallback if Docker unavailable
    - Timeout enforcement
    - Output size limits
    - Process isolation

Architecture:
    User Code → AST Validation → Docker/Subprocess → Result
                    ↓                    ↓
              Block if unsafe      Resource limits
                                   & Isolation
"""

import asyncio
from typing import Dict, Optional
from enum import Enum

from src.utils.logger import get_logger
from src.tools.code_validator import CodeValidator, SecurityLevel, validate_code
from src.tools.sandbox_executor import (
    SandboxExecutor,
    SandboxConfig,
    SandboxMode,
    ExecutionResult
)

logger = get_logger(__name__)


class ExecutionMode(Enum):
    """Code execution modes"""
    SECURE = "secure"      # Full security: AST + Docker + Timeout
    MODERATE = "moderate"  # AST + Subprocess + Timeout
    UNSAFE = "unsafe"      # No validation (DEVELOPMENT ONLY)


class CodeExecutor:
    """Multi-layer secure code execution

    This executor provides defense-in-depth security through multiple layers:
    1. Static analysis (AST validation)
    2. Runtime isolation (Docker containers)
    3. Resource limits (timeout, memory, CPU)

    Usage:
        executor = CodeExecutor(
            timeout=30,
            security_level=SecurityLevel.MODERATE,
            enable_docker=True
        )

        result = await executor.execute("print(2**100)")

        if result['success']:
            print(result['output'])
        else:
            print(result['error'])

    Security Levels:
        STRICT: Only basic Python, no imports
        MODERATE: + safe libs (math, datetime, json) [DEFAULT]
        PERMISSIVE: + data science (numpy, pandas, scipy)
    """

    def __init__(
        self,
        timeout: int = 30,
        max_output_lines: int = 1000,
        security_level: SecurityLevel = SecurityLevel.MODERATE,
        enable_docker: bool = True,
        enable_validation: bool = True,
        memory_limit: str = "256m"
    ):
        """Initialize Code Executor with security settings

        Args:
            timeout: Execution timeout in seconds
            max_output_lines: Maximum output lines (legacy, now handled by sandbox)
            security_level: AST validation security level
            enable_docker: Use Docker sandbox if available
            enable_validation: Enable AST validation (disable only for testing)
            memory_limit: Docker memory limit (e.g., "256m", "512m")
        """
        self.timeout = timeout
        self.max_output_lines = max_output_lines
        self.security_level = security_level
        self.enable_validation = enable_validation
        self.enable_docker = enable_docker

        # Initialize validators and executors
        self.validator = CodeValidator(security_level)

        # Initialize sandbox executor
        sandbox_config = SandboxConfig(
            mode=SandboxMode.DOCKER if enable_docker else SandboxMode.SUBPROCESS,
            timeout=timeout,
            memory_limit=memory_limit,
            enable_network=False,  # Always disable network for security
        )
        self.sandbox_executor = SandboxExecutor(sandbox_config)

        # Track initialization
        self._initialized = False

    async def initialize(self):
        """Initialize sandbox executor (pull Docker image if needed)"""
        if not self._initialized:
            await self.sandbox_executor.initialize()
            self._initialized = True
            logger.info(f"CodeExecutor initialized with security level: {self.security_level.value}")

    async def execute(
        self,
        code: str,
        show_code: bool = True,
    ) -> Dict[str, any]:
        """Execute Python code with multi-layer security

        Args:
            code: Python code to execute
            show_code: Whether to include code in result

        Returns:
            Dict with keys:
                - code: Source code (if show_code=True)
                - output: Standard output
                - error: Error message if any
                - success: Boolean indicating success
                - validation_errors: AST validation errors (if any)
                - execution_time: Time taken (seconds)
                - security_level: Security level used

        Example:
            result = await executor.execute("print(2**100)")
            # result = {
            #     'code': 'print(2**100)',
            #     'output': '1267650600228229401496703205376',
            #     'error': '',
            #     'success': True,
            #     'validation_errors': [],
            #     'execution_time': 0.023,
            #     'security_level': 'moderate'
            # }
        """
        # Ensure initialized
        await self.initialize()

        # Layer 1: AST Validation
        if self.enable_validation:
            validation_result = self.validator.validate(code)

            if not validation_result.is_safe:
                logger.warning(f"Code validation failed: {validation_result.error_message}")
                return {
                    "code": code if show_code else "",
                    "output": "",
                    "error": f"Security validation failed:\n{validation_result.error_message}",
                    "success": False,
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                    "execution_time": 0.0,
                    "security_level": self.security_level.value,
                }

            # Log warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Code validation warning: {warning}")

        # Layer 2 & 3: Execute in sandbox (Docker or subprocess)
        try:
            execution_result: ExecutionResult = await self.sandbox_executor.execute(code)

            # Limit output lines (for backward compatibility)
            output_lines = execution_result.stdout.split('\n')
            if len(output_lines) > self.max_output_lines:
                output_lines = output_lines[:self.max_output_lines]
                output_lines.append(f"... (output truncated to {self.max_output_lines} lines)")

            output_str = '\n'.join(output_lines)

            return {
                "code": code if show_code else "",
                "output": output_str,
                "error": execution_result.stderr,
                "success": execution_result.success,
                "validation_errors": [],
                "validation_warnings": [],
                "execution_time": execution_result.execution_time,
                "timed_out": execution_result.timed_out,
                "security_level": self.security_level.value,
            }

        except Exception as e:
            logger.error(f"Code execution error: {e}", exc_info=True)
            return {
                "code": code if show_code else "",
                "output": "",
                "error": f"Execution error: {str(e)}",
                "success": False,
                "validation_errors": [],
                "validation_warnings": [],
                "execution_time": 0.0,
                "security_level": self.security_level.value,
            }

    def validate_code(
        self,
        code: str,
        allowed_imports: Optional[list] = None
    ) -> tuple[bool, str]:
        """Validate code for safety (backward compatibility method)

        This method is kept for backward compatibility but now uses
        the AST-based validator instead of string matching.

        Args:
            code: Code to validate
            allowed_imports: List of allowed import names (ignored, use security_level instead)

        Returns:
            Tuple of (is_valid, error_message)

        Note:
            The allowed_imports parameter is deprecated. Use security_level instead.
        """
        if allowed_imports is not None:
            logger.warning(
                "allowed_imports parameter is deprecated. "
                "Use security_level parameter in constructor instead."
            )

        validation_result = self.validator.validate(code)

        if validation_result.is_safe:
            return True, ""
        else:
            return False, validation_result.error_message

    async def execute_with_retry(
        self,
        code: str,
        max_retries: int = 2,
        show_code: bool = True
    ) -> Dict[str, any]:
        """Execute code with automatic retry on transient failures

        Args:
            code: Python code to execute
            max_retries: Maximum number of retries
            show_code: Whether to include code in result

        Returns:
            Execution result dict
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = await self.execute(code, show_code)

                # If successful or validation error (non-retryable), return
                if result['success'] or result['validation_errors']:
                    return result

                # If timeout or execution error, might be transient
                if attempt < max_retries:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after failure")
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue

                return result

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(f"Execution attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue

        # All retries exhausted
        return {
            "code": code if show_code else "",
            "output": "",
            "error": f"Execution failed after {max_retries + 1} attempts: {last_error}",
            "success": False,
            "validation_errors": [],
            "execution_time": 0.0,
            "security_level": self.security_level.value,
        }

    def get_security_info(self) -> Dict[str, any]:
        """Get information about security configuration

        Returns:
            Dict with security configuration details
        """
        return {
            "security_level": self.security_level.value,
            "validation_enabled": self.enable_validation,
            "docker_enabled": self.enable_docker,
            "docker_available": self.sandbox_executor.docker_executor.is_available() if self.enable_docker else False,
            "timeout": self.timeout,
            "memory_limit": self.sandbox_executor.config.memory_limit,
            "network_enabled": self.sandbox_executor.config.enable_network,
        }


# Backward compatibility: Keep old class name as alias
class SafeCodeExecutor(CodeExecutor):
    """Alias for CodeExecutor (backward compatibility)"""
    pass


# Convenience function for quick execution
async def execute_code(
    code: str,
    timeout: int = 30,
    security_level: SecurityLevel = SecurityLevel.MODERATE,
    use_docker: bool = True
) -> Dict[str, any]:
    """Execute code with secure defaults (convenience function)

    Args:
        code: Python code to execute
        timeout: Timeout in seconds
        security_level: Security level for validation
        use_docker: Use Docker if available

    Returns:
        Execution result dict

    Example:
        result = await execute_code("print(2**100)")
        if result['success']:
            print(result['output'])
    """
    executor = CodeExecutor(
        timeout=timeout,
        security_level=security_level,
        enable_docker=use_docker
    )
    return await executor.execute(code)
