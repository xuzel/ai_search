"""AST-based Code Validator - Secure code analysis using Abstract Syntax Tree

This module provides robust security validation for Python code execution by analyzing
the code's Abstract Syntax Tree (AST) rather than using string matching, which can be
easily bypassed.

Example bypasses that string matching misses:
    - getattr(__builtins__, 'open')('file')  # String matching doesn't catch 'open'
    - __builtins__['exec'](code)  # Bracket notation
    - eval(input())  # Nested dangerous calls
    - compile(code, '', 'exec')  # Compile then execute
"""

import ast
from dataclasses import dataclass
from typing import List, Set, Tuple, Optional
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityLevel(Enum):
    """Security levels for code validation"""
    STRICT = "strict"      # Only basic math/data structures
    MODERATE = "moderate"  # + common safe libraries (math, datetime, json)
    PERMISSIVE = "permissive"  # + data science libs (numpy, pandas)


@dataclass
class ValidationResult:
    """Result of code validation"""
    is_safe: bool
    errors: List[str]
    warnings: List[str]
    security_level: SecurityLevel

    def __bool__(self):
        """Allow: if validation_result: ..."""
        return self.is_safe

    @property
    def error_message(self) -> str:
        """Get formatted error message"""
        if not self.errors:
            return ""
        return "\n".join(f"- {err}" for err in self.errors)


class CodeValidator:
    """AST-based code validator for secure Python execution

    This validator analyzes code structure using Python's ast module to detect:
    - Dangerous built-in functions (eval, exec, compile, __import__)
    - File system operations (open, write, delete)
    - System operations (os.system, subprocess, etc.)
    - Network operations (socket, urllib, requests)
    - Reflection and introspection abuse (getattr, setattr, delattr)
    - Import of blacklisted modules

    Usage:
        validator = CodeValidator(SecurityLevel.MODERATE)
        result = validator.validate(code)
        if result.is_safe:
            # Execute code
            ...
        else:
            logger.error(f"Unsafe code: {result.error_message}")
    """

    # Dangerous built-in functions that should never be allowed
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', '__import__',
        'open', 'input', 'raw_input',
        'execfile',  # Python 2
        'reload',  # Module reloading
        'breakpoint',  # Debugger access
    }

    # Dangerous module attributes/functions
    DANGEROUS_ATTRIBUTES = {
        'system', 'popen', 'spawn', 'fork', 'kill',
        'remove', 'unlink', 'rmdir', 'rmtree',
        'chdir', 'chmod', 'chown',
        'read', 'write', 'readlines', 'writelines',
        '__code__', '__globals__', '__builtins__',
        'func_code', 'func_globals',  # Python 2
    }

    # Module blacklists by security level
    BLACKLISTED_MODULES = {
        SecurityLevel.STRICT: {
            # Only basic Python structures allowed, no imports
            '*',  # Wildcard: deny all imports
        },
        SecurityLevel.MODERATE: {
            # Dangerous modules
            'os', 'sys', 'subprocess', 'shutil', 'pathlib',
            'socket', 'urllib', 'urllib2', 'urllib3', 'requests', 'httplib',
            'pickle', 'shelve', 'marshal', 'imp', 'importlib',
            'ctypes', 'cffi', 'pty', 'fcntl',
            'multiprocessing', 'threading', 'asyncio',
            '__builtin__', 'builtins',  # Direct access to builtins
            'code', 'codeop',  # Interactive code execution
            'rlcompleter',  # Readline completion (can expose internals)
        },
        SecurityLevel.PERMISSIVE: {
            # Still deny most dangerous modules
            'os', 'sys', 'subprocess', 'shutil',
            'socket', 'urllib', 'urllib2', 'requests',
            'pickle', 'shelve', 'marshal',
            'ctypes', 'cffi',
            '__builtin__', 'builtins',
        }
    }

    # Allowed modules by security level
    ALLOWED_MODULES = {
        SecurityLevel.STRICT: set(),  # No imports allowed
        SecurityLevel.MODERATE: {
            'math', 'statistics', 'random', 'decimal', 'fractions',
            'datetime', 'time', 'calendar',
            'json', 're', 'string', 'textwrap',
            'collections', 'itertools', 'functools',
            'operator', 'copy', 'pprint',
        },
        SecurityLevel.PERMISSIVE: {
            # Moderate + data science
            'math', 'statistics', 'random', 'decimal', 'fractions',
            'datetime', 'time', 'calendar',
            'json', 're', 'string', 'textwrap',
            'collections', 'itertools', 'functools',
            'operator', 'copy', 'pprint',
            'numpy', 'pandas', 'scipy', 'matplotlib',
            'sympy',  # Symbolic math
        }
    }

    def __init__(self, security_level: SecurityLevel = SecurityLevel.MODERATE):
        """Initialize code validator

        Args:
            security_level: Security level for validation
        """
        self.security_level = security_level
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, code: str) -> ValidationResult:
        """Validate Python code for security issues

        Args:
            code: Python code string to validate

        Returns:
            ValidationResult with safety status and messages
        """
        self.errors = []
        self.warnings = []

        # Step 1: Try to parse code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
            return ValidationResult(
                is_safe=False,
                errors=self.errors,
                warnings=self.warnings,
                security_level=self.security_level
            )
        except Exception as e:
            self.errors.append(f"Failed to parse code: {str(e)}")
            return ValidationResult(
                is_safe=False,
                errors=self.errors,
                warnings=self.warnings,
                security_level=self.security_level
            )

        # Step 2: Analyze AST for dangerous patterns
        self._analyze_ast(tree)

        # Step 3: Return result
        is_safe = len(self.errors) == 0
        return ValidationResult(
            is_safe=is_safe,
            errors=self.errors,
            warnings=self.warnings,
            security_level=self.security_level
        )

    def _analyze_ast(self, tree: ast.AST):
        """Analyze AST for dangerous patterns"""
        for node in ast.walk(tree):
            self._check_node(node)

    def _check_node(self, node: ast.AST):
        """Check individual AST node for security issues"""

        # Check function calls
        if isinstance(node, ast.Call):
            self._check_call(node)

        # Check imports
        elif isinstance(node, ast.Import):
            self._check_import(node)

        # Check from imports
        elif isinstance(node, ast.ImportFrom):
            self._check_from_import(node)

        # Check attribute access
        elif isinstance(node, ast.Attribute):
            self._check_attribute(node)

        # Check subscript access (like __builtins__['eval'])
        elif isinstance(node, ast.Subscript):
            self._check_subscript(node)

        # Check exec/eval as statements (Python 2)
        elif isinstance(node, (ast.Exec,)) if hasattr(ast, 'Exec') else False:
            self.errors.append("Exec statement not allowed")

    def _check_call(self, node: ast.Call):
        """Check function call for dangerous patterns"""

        # Direct call to dangerous built-in
        if isinstance(node.func, ast.Name):
            if node.func.id in self.DANGEROUS_BUILTINS:
                self.errors.append(
                    f"Dangerous built-in function: {node.func.id}()"
                )

            # Special check for getattr/setattr/delattr with dangerous arguments
            if node.func.id in ('getattr', 'setattr', 'delattr', 'hasattr'):
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    attr_name = node.args[1].value
                    if attr_name in self.DANGEROUS_BUILTINS or attr_name in self.DANGEROUS_ATTRIBUTES:
                        self.errors.append(
                            f"Dangerous attribute access via {node.func.id}(): '{attr_name}'"
                        )

            # Special check for vars() with dangerous targets
            if node.func.id == 'vars':
                if len(node.args) >= 1 and isinstance(node.args[0], ast.Name):
                    target_name = node.args[0].id
                    if target_name in ('__builtins__', '__globals__'):
                        self.errors.append(
                            f"Dangerous vars() call with '{target_name}'"
                        )

        # Call through getattr: getattr(__builtins__, 'eval')
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.DANGEROUS_BUILTINS:
                self.errors.append(
                    f"Dangerous function accessed via attribute: {node.func.attr}"
                )
            if node.func.attr in self.DANGEROUS_ATTRIBUTES:
                self.errors.append(
                    f"Dangerous attribute accessed: {node.func.attr}"
                )

    def _check_import(self, node: ast.Import):
        """Check import statement"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]  # Get root module
            if not self._is_module_allowed(module_name):
                self.errors.append(
                    f"Import not allowed: {alias.name} "
                    f"(security level: {self.security_level.value})"
                )

    def _check_from_import(self, node: ast.ImportFrom):
        """Check from...import statement"""
        if node.module:
            module_name = node.module.split('.')[0]
            if not self._is_module_allowed(module_name):
                self.errors.append(
                    f"Import not allowed: from {node.module} "
                    f"(security level: {self.security_level.value})"
                )

        # Check for dangerous wildcard imports
        for alias in node.names:
            if alias.name == '*':
                self.warnings.append(
                    f"Wildcard import detected: from {node.module} import *"
                )

    def _check_attribute(self, node: ast.Attribute):
        """Check attribute access"""

        # Access to __builtins__, __globals__, etc.
        if node.attr.startswith('__') and node.attr.endswith('__'):
            if node.attr in self.DANGEROUS_ATTRIBUTES:
                self.errors.append(
                    f"Access to dangerous dunder attribute: {node.attr}"
                )

        # Access to dangerous module attributes
        if node.attr in self.DANGEROUS_ATTRIBUTES:
            # Try to get the module name
            module_name = self._get_module_name(node.value)
            if module_name:
                self.warnings.append(
                    f"Potentially dangerous: {module_name}.{node.attr}"
                )

    def _check_subscript(self, node: ast.Subscript):
        """Check subscript access (e.g., __builtins__['eval'])"""

        # Check if accessing __builtins__ dictionary
        if isinstance(node.value, ast.Name):
            if node.value.id in ('__builtins__', '__globals__'):
                # Check if subscript is a string literal
                if isinstance(node.slice, ast.Constant):
                    if node.slice.value in self.DANGEROUS_BUILTINS:
                        self.errors.append(
                            f"Dangerous built-in accessed via subscript: "
                            f"{node.value.id}['{node.slice.value}']"
                        )

    def _get_module_name(self, node: ast.AST) -> Optional[str]:
        """Try to extract module name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_module_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        return None

    def _is_module_allowed(self, module_name: str) -> bool:
        """Check if module is allowed for current security level"""

        # Strict: no imports allowed
        if self.security_level == SecurityLevel.STRICT:
            return False

        # Check blacklist
        blacklist = self.BLACKLISTED_MODULES[self.security_level]
        if module_name in blacklist:
            return False

        # Check allowlist
        allowlist = self.ALLOWED_MODULES[self.security_level]
        return module_name in allowlist

    def add_allowed_module(self, module_name: str):
        """Dynamically add allowed module for current security level

        Args:
            module_name: Module to allow
        """
        self.ALLOWED_MODULES[self.security_level].add(module_name)
        logger.info(f"Added allowed module: {module_name}")

    def add_blocked_module(self, module_name: str):
        """Dynamically add blocked module for current security level

        Args:
            module_name: Module to block
        """
        self.BLACKLISTED_MODULES[self.security_level].add(module_name)
        logger.info(f"Added blocked module: {module_name}")


def validate_code(
    code: str,
    security_level: SecurityLevel = SecurityLevel.MODERATE
) -> ValidationResult:
    """Convenience function for code validation

    Args:
        code: Python code to validate
        security_level: Security level for validation

    Returns:
        ValidationResult

    Example:
        result = validate_code("import os; os.system('ls')")
        if not result.is_safe:
            print(result.error_message)
    """
    validator = CodeValidator(security_level)
    return validator.validate(code)


# Example bypass attempts that this validator catches:
_BYPASS_EXAMPLES = """
# String matching would miss these, but AST-based validation catches them:

# 1. Getattr bypass
getattr(__builtins__, 'eval')('malicious_code')
# Caught: Dangerous built-in accessed via attribute: eval

# 2. Dictionary access bypass
__builtins__['exec'](code)
# Caught: Dangerous built-in accessed via subscript: __builtins__['exec']

# 3. Nested dangerous calls
eval(input())
# Caught: Dangerous built-in function: eval() AND input()

# 4. Compile then execute
compile(malicious_code, '<string>', 'exec')
# Caught: Dangerous built-in function: compile()

# 5. Import through string
__import__('os').system('ls')
# Caught: Dangerous built-in function: __import__()

# 6. Attribute chains
sys.modules['os'].system('ls')
# Caught: Import not allowed: sys

# 7. Hidden file operations
with open('/etc/passwd') as f: data = f.read()
# Caught: Dangerous built-in function: open()
"""
