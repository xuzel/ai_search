"""Secret Sanitizer - Remove sensitive information from logs and error messages

This module provides utilities to automatically sanitize sensitive data like API keys,
passwords, tokens, etc. from logs, error messages, and other output.
"""

import re
from typing import Any, Dict, List


# Patterns for sensitive data
SENSITIVE_PATTERNS = [
    # API Keys (various formats)
    (re.compile(r'(api[_-]?key["\s:=]+)([a-zA-Z0-9_\-]{20,})', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(key["\s:=]+)([a-zA-Z0-9_\-]{20,})', re.IGNORECASE), r'\1***REDACTED***'),

    # Tokens
    (re.compile(r'(token["\s:=]+)([a-zA-Z0-9_\-\.]{20,})', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(bearer\s+)([a-zA-Z0-9_\-\.]{20,})', re.IGNORECASE), r'\1***REDACTED***'),

    # Passwords
    (re.compile(r'(password["\s:=]+)([^\s"\']+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(passwd["\s:=]+)([^\s"\']+)', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(pwd["\s:=]+)([^\s"\']+)', re.IGNORECASE), r'\1***REDACTED***'),

    # Secrets
    (re.compile(r'(secret["\s:=]+)([a-zA-Z0-9_\-]{20,})', re.IGNORECASE), r'\1***REDACTED***'),

    # Authorization headers
    (re.compile(r'(authorization["\s:]+)([^\s"\']+)', re.IGNORECASE), r'\1***REDACTED***'),

    # Common environment variable patterns
    (re.compile(r'([A-Z_]+_API_KEY["\s:=]+)([a-zA-Z0-9_\-]{10,})', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'([A-Z_]+_SECRET["\s:=]+)([a-zA-Z0-9_\-]{10,})', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'([A-Z_]+_TOKEN["\s:=]+)([a-zA-Z0-9_\-]{10,})', re.IGNORECASE), r'\1***REDACTED***'),

    # URLs with credentials
    (re.compile(r'(https?://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***REDACTED***\3'),

    # JWT tokens (basic pattern)
    (re.compile(r'\b(eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)\b'), r'***JWT_REDACTED***'),
]

# Known sensitive keys in dictionaries/objects
SENSITIVE_KEYS = {
    'api_key', 'apikey', 'api-key',
    'secret', 'secret_key', 'secret-key',
    'password', 'passwd', 'pwd',
    'token', 'access_token', 'refresh_token',
    'authorization', 'auth',
    'private_key', 'privatekey',
    'client_secret', 'client-secret',
    'serpapi_key', 'openai_key', 'dashscope_key',
    'alpha_vantage_key', 'openweathermap_key',
}


def sanitize_string(text: str) -> str:
    """Sanitize sensitive information from a string

    Args:
        text: Input string that may contain sensitive data

    Returns:
        Sanitized string with sensitive data redacted
    """
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def sanitize_dict(data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
    """Sanitize sensitive information from a dictionary

    Args:
        data: Dictionary that may contain sensitive data
        recursive: Whether to recursively sanitize nested dictionaries

    Returns:
        Sanitized dictionary with sensitive values redacted
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        # Check if key indicates sensitive data
        if key.lower().replace('-', '_') in SENSITIVE_KEYS:
            sanitized[key] = '***REDACTED***'
        elif recursive and isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, recursive=True)
        elif recursive and isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, recursive=True) if isinstance(item, dict)
                else sanitize_string(str(item)) if isinstance(item, str)
                else item
                for item in value
            ]
        elif isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        else:
            sanitized[key] = value

    return sanitized


def sanitize_list(data: List[Any], recursive: bool = True) -> List[Any]:
    """Sanitize sensitive information from a list

    Args:
        data: List that may contain sensitive data
        recursive: Whether to recursively sanitize nested structures

    Returns:
        Sanitized list with sensitive data redacted
    """
    if not isinstance(data, list):
        return data

    sanitized = []
    for item in data:
        if recursive and isinstance(item, dict):
            sanitized.append(sanitize_dict(item, recursive=True))
        elif recursive and isinstance(item, list):
            sanitized.append(sanitize_list(item, recursive=True))
        elif isinstance(item, str):
            sanitized.append(sanitize_string(item))
        else:
            sanitized.append(item)

    return sanitized


def sanitize(data: Any, recursive: bool = True) -> Any:
    """Sanitize sensitive information from any data type

    Args:
        data: Data that may contain sensitive information
        recursive: Whether to recursively sanitize nested structures

    Returns:
        Sanitized data with sensitive information redacted
    """
    if isinstance(data, dict):
        return sanitize_dict(data, recursive=recursive)
    elif isinstance(data, list):
        return sanitize_list(data, recursive=recursive)
    elif isinstance(data, str):
        return sanitize_string(data)
    else:
        return data


def mask_value(value: str, visible_chars: int = 4) -> str:
    """Mask a sensitive value, showing only the last few characters

    Args:
        value: Value to mask
        visible_chars: Number of characters to leave visible at the end

    Returns:
        Masked value (e.g., "***abc123")

    Example:
        >>> mask_value("my_secret_api_key_12345", 5)
        '***12345'
    """
    if not isinstance(value, str) or len(value) <= visible_chars:
        return '***'

    return '***' + value[-visible_chars:]


def is_sensitive_key(key: str) -> bool:
    """Check if a key name indicates sensitive data

    Args:
        key: Key name to check

    Returns:
        True if key likely contains sensitive data
    """
    normalized = key.lower().replace('-', '_')
    return normalized in SENSITIVE_KEYS or any(
        keyword in normalized
        for keyword in ['key', 'secret', 'password', 'token', 'auth']
    )
