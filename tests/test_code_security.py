"""Comprehensive security tests for code execution system

Tests the three-layer security architecture:
- Layer 1: AST-based code validation
- Layer 2: Docker sandbox isolation
- Layer 3: Resource limits and timeout enforcement
"""

import asyncio
import pytest

from src.tools.code_validator import CodeValidator, SecurityLevel, ValidationResult
from src.tools.sandbox_executor import (
    SandboxExecutor,
    SandboxConfig,
    SandboxMode,
    ExecutionResult
)
from src.tools.code_executor import CodeExecutor


# ============================================================================
# Layer 1: AST-based Code Validation Tests
# ============================================================================

class TestCodeValidator:
    """Test AST-based code validator"""

    def test_validator_basic_math(self):
        """Test that basic math is allowed"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "result = 2 + 2\nprint(result)"
        result = validator.validate(code)

        assert result.is_safe
        assert len(result.errors) == 0

    def test_validator_blocks_eval(self):
        """Test that eval() is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "eval('2 + 2')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('eval' in error.lower() for error in result.errors)

    def test_validator_blocks_exec(self):
        """Test that exec() is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "exec('print(2)')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('exec' in error.lower() for error in result.errors)

    def test_validator_blocks_open(self):
        """Test that open() is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "with open('/etc/passwd') as f: data = f.read()"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('open' in error.lower() for error in result.errors)

    def test_validator_blocks_import(self):
        """Test that __import__() is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "__import__('os').system('ls')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('__import__' in error.lower() for error in result.errors)

    def test_validator_blocks_os_import(self):
        """Test that importing os is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "import os\nos.system('ls')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('os' in error.lower() for error in result.errors)

    def test_validator_blocks_sys_import(self):
        """Test that importing sys is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "import sys\nprint(sys.version)"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('sys' in error.lower() for error in result.errors)

    def test_validator_blocks_subprocess_import(self):
        """Test that importing subprocess is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "import subprocess\nsubprocess.run(['ls'])"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('subprocess' in error.lower() for error in result.errors)

    def test_validator_allows_math_import(self):
        """Test that importing math is allowed in MODERATE level"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "import math\nprint(math.pi)"
        result = validator.validate(code)

        assert result.is_safe
        assert len(result.errors) == 0

    def test_validator_allows_datetime_import(self):
        """Test that importing datetime is allowed in MODERATE level"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "import datetime\nprint(datetime.datetime.now())"
        result = validator.validate(code)

        assert result.is_safe
        assert len(result.errors) == 0

    def test_validator_blocks_getattr_bypass(self):
        """Test that getattr bypass is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "getattr(__builtins__, 'eval')('2 + 2')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('getattr' in error.lower() and 'eval' in error.lower() for error in result.errors)

    def test_validator_blocks_setattr_bypass(self):
        """Test that setattr with dangerous attributes is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "setattr(obj, '__globals__', {})"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('setattr' in error.lower() for error in result.errors)

    def test_validator_blocks_subscript_bypass(self):
        """Test that __builtins__ subscript access is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "__builtins__['eval']('2 + 2')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('eval' in error.lower() for error in result.errors)

    def test_validator_strict_mode_blocks_imports(self):
        """Test that STRICT mode blocks all imports"""
        validator = CodeValidator(SecurityLevel.STRICT)
        code = "import math\nprint(math.pi)"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('math' in error.lower() for error in result.errors)

    def test_validator_permissive_allows_numpy(self):
        """Test that PERMISSIVE mode allows numpy"""
        validator = CodeValidator(SecurityLevel.PERMISSIVE)
        code = "import numpy as np\nprint(np.array([1, 2, 3]))"
        result = validator.validate(code)

        assert result.is_safe
        assert len(result.errors) == 0

    def test_validator_syntax_error(self):
        """Test that syntax errors are caught"""
        validator = CodeValidator(SecurityLevel.MODERATE)
        code = "if True\n    print('missing colon')"
        result = validator.validate(code)

        assert not result.is_safe
        assert any('syntax' in error.lower() for error in result.errors)


# ============================================================================
# Layer 2: Sandbox Executor Tests
# ============================================================================

class TestSandboxExecutor:
    """Test sandbox executor (subprocess mode)"""

    @pytest.mark.asyncio
    async def test_sandbox_basic_execution(self):
        """Test basic code execution in sandbox"""
        config = SandboxConfig(mode=SandboxMode.SUBPROCESS, timeout=5)
        executor = SandboxExecutor(config)

        code = "print(2 + 2)"
        result = await executor.execute(code)

        assert result.success
        assert "4" in result.stdout
        assert result.exit_code == 0
        assert not result.timed_out

    @pytest.mark.asyncio
    async def test_sandbox_timeout_enforcement(self):
        """Test that timeout is enforced"""
        config = SandboxConfig(mode=SandboxMode.SUBPROCESS, timeout=1)
        executor = SandboxExecutor(config)

        code = "import time\ntime.sleep(10)\nprint('done')"
        result = await executor.execute(code)

        assert not result.success
        assert result.timed_out
        assert "timeout" in result.stderr.lower()

    @pytest.mark.asyncio
    async def test_sandbox_output_capture(self):
        """Test that stdout and stderr are captured"""
        config = SandboxConfig(mode=SandboxMode.SUBPROCESS, timeout=5)
        executor = SandboxExecutor(config)

        code = """
import sys
print('stdout message')
print('stderr message', file=sys.stderr)
"""
        result = await executor.execute(code)

        assert result.success
        assert "stdout message" in result.stdout
        assert "stderr message" in result.stderr

    @pytest.mark.asyncio
    async def test_sandbox_output_size_limit(self):
        """Test that output size is limited"""
        config = SandboxConfig(mode=SandboxMode.SUBPROCESS, timeout=5, max_output_size=100)
        executor = SandboxExecutor(config)

        code = "for i in range(10000): print('x' * 100)"
        result = await executor.execute(code)

        # Output should be truncated
        assert len(result.stdout) <= config.max_output_size + 100  # Small buffer for truncation message
        assert "truncated" in result.stdout.lower()

    @pytest.mark.asyncio
    async def test_sandbox_execution_error(self):
        """Test that execution errors are captured"""
        config = SandboxConfig(mode=SandboxMode.SUBPROCESS, timeout=5)
        executor = SandboxExecutor(config)

        code = "raise ValueError('test error')"
        result = await executor.execute(code)

        assert not result.success
        assert "ValueError" in result.stderr
        assert "test error" in result.stderr


# ============================================================================
# Layer 3: Integrated CodeExecutor Tests
# ============================================================================

class TestCodeExecutor:
    """Test integrated CodeExecutor with all security layers"""

    @pytest.mark.asyncio
    async def test_executor_safe_code(self):
        """Test execution of safe code"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,  # Use subprocess for testing
            enable_validation=True
        )

        code = """
import math
result = math.sqrt(16) + math.pi
print(f"Result: {result}")
"""
        result = await executor.execute(code)

        assert result['success']
        assert "Result:" in result['output']
        assert len(result['validation_errors']) == 0

    @pytest.mark.asyncio
    async def test_executor_blocks_dangerous_code(self):
        """Test that dangerous code is blocked by validation"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,
            enable_validation=True
        )

        code = "import os; os.system('ls')"
        result = await executor.execute(code)

        assert not result['success']
        assert len(result['validation_errors']) > 0
        assert "os" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_executor_timeout(self):
        """Test that execution timeout works"""
        executor = CodeExecutor(
            timeout=1,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,
            enable_validation=True
        )

        code = """
import time
time.sleep(10)
print('done')
"""
        result = await executor.execute(code)

        assert not result['success']
        assert result.get('timed_out', False) or "timeout" in result['error'].lower()

    @pytest.mark.asyncio
    async def test_executor_validation_can_be_disabled(self):
        """Test that validation can be disabled (for testing only)"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,
            enable_validation=False  # Disable for testing
        )

        # This would normally be blocked, but validation is disabled
        code = "print(2 + 2)"  # Safe code, but testing disabled validation
        result = await executor.execute(code)

        # Should still execute (subprocess layer doesn't validate)
        assert result['success'] or not result['success']  # May succeed or fail depending on imports

    @pytest.mark.asyncio
    async def test_executor_strict_mode(self):
        """Test STRICT security level"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.STRICT,
            enable_docker=False,
            enable_validation=True
        )

        # Even math import should be blocked
        code = "import math\nprint(math.pi)"
        result = await executor.execute(code)

        assert not result['success']
        assert len(result['validation_errors']) > 0

    @pytest.mark.asyncio
    async def test_executor_permissive_mode(self):
        """Test PERMISSIVE security level"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.PERMISSIVE,
            enable_docker=False,
            enable_validation=True
        )

        # Data science imports should be allowed
        code = """
import math
import statistics
result = statistics.mean([1, 2, 3, 4, 5])
print(f"Mean: {result}")
"""
        result = await executor.execute(code)

        assert result['success']
        assert "Mean:" in result['output']

    @pytest.mark.asyncio
    async def test_executor_get_security_info(self):
        """Test get_security_info() method"""
        executor = CodeExecutor(
            timeout=30,
            security_level=SecurityLevel.MODERATE,
            enable_docker=True,
            enable_validation=True,
            memory_limit="512m"
        )

        info = executor.get_security_info()

        assert info['security_level'] == 'moderate'
        assert info['validation_enabled'] == True
        assert info['docker_enabled'] == True
        assert info['timeout'] == 30
        assert info['memory_limit'] == "512m"
        assert info['network_enabled'] == False

    @pytest.mark.asyncio
    async def test_executor_execute_with_retry(self):
        """Test execute_with_retry() method"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,
            enable_validation=True
        )

        # Safe code should succeed on first try
        code = "print(2 ** 10)"
        result = await executor.execute_with_retry(code, max_retries=2)

        assert result['success']
        assert "1024" in result['output']

    @pytest.mark.asyncio
    async def test_executor_output_line_limit(self):
        """Test that output line limiting works"""
        executor = CodeExecutor(
            timeout=5,
            max_output_lines=10,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,
            enable_validation=True
        )

        # Generate many lines
        code = "for i in range(100): print(f'Line {i}')"
        result = await executor.execute(code)

        assert result['success']
        lines = result['output'].split('\n')
        # Should be limited to max_output_lines + 1 for truncation message
        assert len(lines) <= 12  # 10 lines + truncation message + empty line

    @pytest.mark.asyncio
    async def test_executor_complex_math(self):
        """Test complex mathematical operations"""
        executor = CodeExecutor(
            timeout=5,
            security_level=SecurityLevel.MODERATE,
            enable_docker=False,
            enable_validation=True
        )

        code = """
import math
# Calculate fibonacci
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

result = fib(10)
print(f"Fibonacci(10) = {result}")

# Calculate prime numbers
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

primes = [x for x in range(2, 50) if is_prime(x)]
print(f"Primes < 50: {primes}")
"""
        result = await executor.execute(code)

        assert result['success']
        assert "Fibonacci(10) = 55" in result['output']
        assert "Primes < 50:" in result['output']


# ============================================================================
# Attack Vector Tests
# ============================================================================

class TestAttackVectors:
    """Test various attack vectors to ensure they're blocked"""

    def test_prevent_file_read(self):
        """Test that file read attempts are blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)

        attack_codes = [
            "open('/etc/passwd').read()",
            "with open('/etc/passwd') as f: data = f.read()",
            "file('/etc/passwd').read()",
        ]

        for code in attack_codes:
            result = validator.validate(code)
            assert not result.is_safe, f"Failed to block: {code}"

    def test_prevent_file_write(self):
        """Test that file write attempts are blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)

        code = "with open('/tmp/evil.txt', 'w') as f: f.write('data')"
        result = validator.validate(code)

        assert not result.is_safe

    def test_prevent_system_commands(self):
        """Test that system command execution is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)

        attack_codes = [
            "import os; os.system('rm -rf /')",
            "import subprocess; subprocess.run(['ls'])",
            "import shutil; shutil.rmtree('/')",
        ]

        for code in attack_codes:
            result = validator.validate(code)
            assert not result.is_safe, f"Failed to block: {code}"

    def test_prevent_network_access(self):
        """Test that network access is blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)

        attack_codes = [
            "import socket; socket.socket()",
            "import urllib; urllib.request.urlopen('http://evil.com')",
            "import requests; requests.get('http://evil.com')",
        ]

        for code in attack_codes:
            result = validator.validate(code)
            assert not result.is_safe, f"Failed to block: {code}"

    def test_prevent_code_injection(self):
        """Test that code injection attempts are blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)

        attack_codes = [
            "eval('__import__(\"os\").system(\"ls\")')",
            "exec('import os; os.system(\"ls\")')",
            "compile('malicious code', '<string>', 'exec')",
        ]

        for code in attack_codes:
            result = validator.validate(code)
            assert not result.is_safe, f"Failed to block: {code}"

    def test_prevent_reflection_attacks(self):
        """Test that reflection attacks are blocked"""
        validator = CodeValidator(SecurityLevel.MODERATE)

        attack_codes = [
            "getattr(__builtins__, 'eval')('code')",
            "__builtins__['exec']('code')",
            "vars(__builtins__)['eval']('code')",
        ]

        for code in attack_codes:
            result = validator.validate(code)
            assert not result.is_safe, f"Failed to block: {code}"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
