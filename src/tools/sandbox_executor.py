"""Docker Sandbox Executor - Isolated code execution in Docker containers

This module provides secure code execution by running untrusted Python code inside
Docker containers with strict resource limits and network isolation.

Architecture:
    User Code → AST Validation → Docker Container → Result
                                  ↓
                    - CPU limit (1 core)
                    - Memory limit (256MB)
                    - Network disabled
                    - No host filesystem access
                    - Timeout enforcement

Security Layers:
    Layer 1: AST-based code validation (code_validator.py)
    Layer 2: Docker containerization (this module)
    Layer 3: Subprocess timeout (fallback if Docker unavailable)
"""

import asyncio
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SandboxMode(Enum):
    """Sandbox execution modes"""
    DOCKER = "docker"          # Full Docker isolation (preferred)
    SUBPROCESS = "subprocess"  # Fallback without Docker
    DISABLED = "disabled"      # No sandboxing (development only)


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution"""
    mode: SandboxMode = SandboxMode.DOCKER
    timeout: int = 30  # seconds
    memory_limit: str = "256m"  # Docker memory limit
    cpu_limit: float = 1.0  # CPU cores
    enable_network: bool = False  # Disable network by default
    python_version: str = "3.11"  # Python version in container
    max_output_size: int = 100000  # Max output bytes


@dataclass
class ExecutionResult:
    """Result of sandbox execution"""
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    execution_time: float  # seconds

    @property
    def success(self) -> bool:
        """Check if execution was successful"""
        return self.exit_code == 0 and not self.timed_out


class DockerSandboxExecutor:
    """Execute Python code in isolated Docker containers

    This executor provides maximum security by running untrusted code in
    Docker containers with resource limits and no access to host system.

    Features:
    - CPU and memory limits
    - Network isolation
    - Temporary filesystem (no persistence)
    - Timeout enforcement
    - Automatic cleanup

    Requirements:
    - Docker installed and running
    - Python base image available (python:3.11-slim)

    Usage:
        config = SandboxConfig(timeout=10, memory_limit="128m")
        executor = DockerSandboxExecutor(config)

        if executor.is_available():
            result = await executor.execute("print(2**100)")
            print(result.stdout)
        else:
            # Fallback to subprocess execution
            ...
    """

    def __init__(self, config: SandboxConfig):
        """Initialize Docker sandbox executor

        Args:
            config: Sandbox configuration
        """
        self.config = config
        self._docker_available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if Docker is available

        Returns:
            True if Docker daemon is running and accessible
        """
        if self._docker_available is not None:
            return self._docker_available

        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                timeout=5
            )
            self._docker_available = result.returncode == 0

            if self._docker_available:
                logger.info("Docker is available for sandbox execution")
            else:
                logger.warning("Docker is not available, will use fallback mode")

            return self._docker_available

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Docker check failed: {e}")
            self._docker_available = False
            return False

    async def execute(self, code: str) -> ExecutionResult:
        """Execute Python code in Docker container

        Args:
            code: Python code to execute

        Returns:
            ExecutionResult with stdout, stderr, and metadata
        """
        import time
        start_time = time.time()

        # Create temporary file for code
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=None
        )

        try:
            # Write code to temp file
            temp_file.write(code)
            temp_file.close()

            # Generate unique container name
            container_name = f"sandbox_{uuid.uuid4().hex[:12]}"

            # Build Docker run command
            docker_cmd = self._build_docker_command(
                temp_file.name,
                container_name
            )

            # Execute in Docker
            try:
                process = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.config.timeout
                    )
                    timed_out = False

                except asyncio.TimeoutError:
                    # Kill container on timeout
                    await self._kill_container(container_name)
                    process.kill()
                    stdout = b""
                    stderr = f"Execution timeout ({self.config.timeout}s)".encode()
                    timed_out = True

                # Decode output
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')

                # Limit output size
                if len(stdout_str) > self.config.max_output_size:
                    stdout_str = stdout_str[:self.config.max_output_size] + "\n... (output truncated)"
                if len(stderr_str) > self.config.max_output_size:
                    stderr_str = stderr_str[:self.config.max_output_size] + "\n... (output truncated)"

                execution_time = time.time() - start_time

                return ExecutionResult(
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=process.returncode or (124 if timed_out else 0),
                    timed_out=timed_out,
                    execution_time=execution_time
                )

            finally:
                # Cleanup container (best effort)
                await self._cleanup_container(container_name)

        finally:
            # Cleanup temp file
            try:
                Path(temp_file.name).unlink()
            except Exception as e:
                logger.debug(f"Failed to delete temp file: {e}")

    def _build_docker_command(self, script_path: str, container_name: str) -> list:
        """Build Docker run command with security restrictions

        Args:
            script_path: Path to Python script on host
            container_name: Name for the container

        Returns:
            List of command arguments
        """
        cmd = [
            'docker', 'run',
            '--rm',  # Auto-remove container after execution
            '--name', container_name,

            # Resource limits
            f'--memory={self.config.memory_limit}',
            f'--cpus={self.config.cpu_limit}',
            '--memory-swap', self.config.memory_limit,  # No swap

            # Security restrictions
            '--read-only',  # Read-only root filesystem
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=10m',  # Small writable tmp
            '--security-opt=no-new-privileges',  # Prevent privilege escalation
            '--cap-drop=ALL',  # Drop all Linux capabilities

            # User
            '--user', '65534:65534',  # nobody:nogroup

            # Working directory
            '-w', '/tmp',
        ]

        # Network isolation
        if not self.config.enable_network:
            cmd.extend(['--network', 'none'])

        # Mount script (read-only)
        cmd.extend([
            '-v', f'{script_path}:/tmp/script.py:ro',
        ])

        # Image and command
        cmd.extend([
            f'python:{self.config.python_version}-slim',
            'python', '/tmp/script.py'
        ])

        return cmd

    async def _kill_container(self, container_name: str):
        """Kill a running container

        Args:
            container_name: Name of container to kill
        """
        try:
            process = await asyncio.create_subprocess_exec(
                'docker', 'kill', container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            logger.debug(f"Failed to kill container {container_name}: {e}")

    async def _cleanup_container(self, container_name: str):
        """Clean up container (best effort)

        Args:
            container_name: Name of container to cleanup
        """
        try:
            # Try to remove container (may already be gone due to --rm)
            process = await asyncio.create_subprocess_exec(
                'docker', 'rm', '-f', container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            logger.debug(f"Container cleanup failed (may already be removed): {e}")

    async def pull_image_if_needed(self) -> bool:
        """Pull Python Docker image if not available

        Returns:
            True if image is available or successfully pulled
        """
        image = f'python:{self.config.python_version}-slim'

        try:
            # Check if image exists
            process = await asyncio.create_subprocess_exec(
                'docker', 'image', 'inspect', image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            if process.returncode == 0:
                logger.debug(f"Docker image {image} already available")
                return True

            # Pull image
            logger.info(f"Pulling Docker image {image}...")
            process = await asyncio.create_subprocess_exec(
                'docker', 'pull', image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minutes for image pull
            )

            if process.returncode == 0:
                logger.info(f"Successfully pulled {image}")
                return True
            else:
                logger.error(f"Failed to pull {image}: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error pulling Docker image: {e}")
            return False


class SandboxExecutor:
    """Unified sandbox executor with automatic fallback

    This class provides a unified interface for sandbox execution with
    automatic fallback from Docker to subprocess if Docker is unavailable.

    Execution priority:
    1. Docker sandbox (if available and configured)
    2. Subprocess execution (fallback)

    Usage:
        executor = SandboxExecutor(config)
        result = await executor.execute(code)

        if result.success:
            print(result.stdout)
        else:
            print(f"Error: {result.stderr}")
    """

    def __init__(self, config: SandboxConfig):
        """Initialize sandbox executor

        Args:
            config: Sandbox configuration
        """
        self.config = config
        self.docker_executor = DockerSandboxExecutor(config)
        self._mode: Optional[SandboxMode] = None

    async def initialize(self) -> SandboxMode:
        """Initialize executor and determine execution mode

        Returns:
            Active sandbox mode
        """
        if self._mode is not None:
            return self._mode

        if self.config.mode == SandboxMode.DISABLED:
            self._mode = SandboxMode.DISABLED
            logger.warning("Sandbox execution is DISABLED - this is unsafe for production!")
            return self._mode

        if self.config.mode == SandboxMode.DOCKER:
            if self.docker_executor.is_available():
                # Try to pull image
                if await self.docker_executor.pull_image_if_needed():
                    self._mode = SandboxMode.DOCKER
                    logger.info("Using Docker sandbox mode")
                    return self._mode

            # Fallback to subprocess
            logger.warning("Docker not available, falling back to subprocess mode")
            self._mode = SandboxMode.SUBPROCESS
            return self._mode

        # Subprocess mode explicitly requested
        self._mode = SandboxMode.SUBPROCESS
        logger.info("Using subprocess sandbox mode")
        return self._mode

    async def execute(self, code: str) -> ExecutionResult:
        """Execute code in sandbox

        Args:
            code: Python code to execute

        Returns:
            ExecutionResult
        """
        # Ensure initialized
        mode = await self.initialize()

        if mode == SandboxMode.DOCKER:
            return await self.docker_executor.execute(code)
        elif mode == SandboxMode.SUBPROCESS:
            return await self._execute_subprocess(code)
        else:  # DISABLED
            return await self._execute_subprocess(code)

    async def _execute_subprocess(self, code: str) -> ExecutionResult:
        """Execute code in subprocess (fallback mode)

        Args:
            code: Python code to execute

        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()

        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        )

        try:
            temp_file.write(code)
            temp_file.close()

            process = await asyncio.create_subprocess_exec(
                'python3',
                temp_file.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout
                )
                timed_out = False
            except asyncio.TimeoutError:
                process.kill()
                stdout = b""
                stderr = f"Execution timeout ({self.config.timeout}s)".encode()
                timed_out = True

            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            # Limit output
            if len(stdout_str) > self.config.max_output_size:
                stdout_str = stdout_str[:self.config.max_output_size] + "\n... (output truncated)"
            if len(stderr_str) > self.config.max_output_size:
                stderr_str = stderr_str[:self.config.max_output_size] + "\n... (output truncated)"

            execution_time = time.time() - start_time

            return ExecutionResult(
                stdout=stdout_str,
                stderr=stderr_str,
                exit_code=process.returncode or (124 if timed_out else 0),
                timed_out=timed_out,
                execution_time=execution_time
            )

        finally:
            try:
                Path(temp_file.name).unlink()
            except Exception as e:
                logger.debug(f"Failed to delete temp file: {e}")


# Convenience function
async def execute_in_sandbox(
    code: str,
    timeout: int = 30,
    memory_limit: str = "256m",
    use_docker: bool = True
) -> ExecutionResult:
    """Execute code in sandbox (convenience function)

    Args:
        code: Python code to execute
        timeout: Timeout in seconds
        memory_limit: Docker memory limit (e.g., "256m")
        use_docker: Use Docker if available

    Returns:
        ExecutionResult

    Example:
        result = await execute_in_sandbox("print(2**100)")
        if result.success:
            print(result.stdout)
    """
    config = SandboxConfig(
        mode=SandboxMode.DOCKER if use_docker else SandboxMode.SUBPROCESS,
        timeout=timeout,
        memory_limit=memory_limit
    )
    executor = SandboxExecutor(config)
    return await executor.execute(code)
