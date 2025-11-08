"""Logging configuration for AI Search Engine

Standardized logging setup with support for:
- Environment-based configuration
- File and console output
- Structured format
- Log rotation
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

# Configuration from environment
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', None)  # Optional file logging
LOG_FORMAT = os.getenv('LOG_FORMAT', 'standard')  # 'standard', 'detailed', or 'json'

# Standard format: timestamp - module - level - message
STANDARD_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Detailed format: includes file, line number, and thread
DETAILED_FORMAT = (
    '%(asctime)s - %(name)s - %(levelname)s - '
    '[%(filename)s:%(lineno)d] - %(message)s'
)

# Date format
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Determine format and create handlers
if LOG_FORMAT == 'json':
    # Use JSON formatter for structured logging
    from src.utils.json_logger import JSONFormatter

    json_formatter = JSONFormatter(
        include_extra=True,
        include_context=True,
        sanitize_secrets=True
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    handlers = [console_handler]

    # Add file handler with JSON format if specified
    if LOG_FILE:
        log_dir = Path(LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(json_formatter)
        handlers.append(file_handler)

    # Configure root logger for JSON
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        handlers=handlers
    )
else:
    # Use text format (standard or detailed)
    log_format = DETAILED_FORMAT if LOG_FORMAT == 'detailed' else STANDARD_FORMAT

    # Create handlers list
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler if LOG_FILE is specified
    if LOG_FILE:
        log_dir = Path(LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Rotating file handler: 10MB max, keep 5 backups
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=DATE_FORMAT))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=log_format,
        datefmt=DATE_FORMAT,
        handlers=handlers
    )

# Suppress noisy third-party loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a standardized logger instance

    Args:
        name: Logger name (typically __name__)
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)

    if level:
        # Allow per-logger level override
        logger.setLevel(getattr(logging, level.upper()))

    return logger


def set_log_level(level: str) -> None:
    """Change global log level at runtime

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> set_log_level('DEBUG')
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)


def get_log_config() -> dict:
    """Get current logging configuration

    Returns:
        Dictionary with current log settings
    """
    return {
        'level': logging.getLevelName(logging.getLogger().level),
        'format': LOG_FORMAT,
        'file': LOG_FILE,
        'handlers': len(logging.getLogger().handlers)
    }
