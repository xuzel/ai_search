"""Structured JSON Logging

Provides JSON-formatted logging for production environments with log aggregation.
Compatible with ELK Stack, Splunk, CloudWatch Logs, and other log management systems.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging"""

    def __init__(
        self,
        include_extra: bool = True,
        include_context: bool = True,
        sanitize_secrets: bool = True
    ):
        """
        Initialize JSON formatter

        Args:
            include_extra: Include extra fields from LogRecord
            include_context: Include execution context (file, line, function)
            sanitize_secrets: Sanitize sensitive data from log messages
        """
        super().__init__()
        self.include_extra = include_extra
        self.include_context = include_context
        self.sanitize_secrets = sanitize_secrets

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON string representation of the log record
        """
        # Base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add execution context if enabled
        if self.include_context:
            log_entry["context"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
                "module": record.module,
            }

        # Add process/thread info
        log_entry["process"] = {
            "id": record.process,
            "name": record.processName,
        }

        log_entry["thread"] = {
            "id": record.thread,
            "name": record.threadName,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields if enabled
        if self.include_extra:
            # Filter out standard LogRecord attributes
            standard_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
                'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
                'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'getMessage', 'taskName'
            }

            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith('_'):
                    extra_fields[key] = value

            if extra_fields:
                log_entry["extra"] = extra_fields

        # Sanitize secrets if enabled
        if self.sanitize_secrets:
            log_entry = self._sanitize_log_entry(log_entry)

        # Return JSON string
        return json.dumps(log_entry, default=str, ensure_ascii=False)

    def _sanitize_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive information from log entry

        Args:
            log_entry: Log entry dictionary

        Returns:
            Sanitized log entry
        """
        # Import sanitizer
        try:
            from src.utils.secret_sanitizer import sanitize_dict
            return sanitize_dict(log_entry, recursive=True)
        except ImportError:
            # If sanitizer not available, return as-is
            return log_entry


class StructuredLogger:
    """Wrapper for adding structured context to logs"""

    def __init__(self, logger: logging.Logger):
        """
        Initialize structured logger wrapper

        Args:
            logger: Base logger instance
        """
        self.logger = logger
        self.context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """Set persistent context fields

        Example:
            >>> logger = StructuredLogger(get_logger(__name__))
            >>> logger.set_context(user_id="123", request_id="abc")
            >>> logger.info("User action")  # Will include user_id and request_id
        """
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context fields"""
        self.context.clear()

    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Internal method to log with context"""
        # Merge context into extra
        extra = kwargs.get('extra', {})
        extra.update(self.context)
        kwargs['extra'] = extra

        self.logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with context"""
        self._log_with_context(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with context"""
        self._log_with_context(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with context"""
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with context"""
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with context"""
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log exception with context"""
        kwargs['exc_info'] = True
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)


def configure_json_logging(
    logger: Optional[logging.Logger] = None,
    level: str = "INFO",
    include_context: bool = True,
    sanitize_secrets: bool = True
) -> logging.Logger:
    """Configure a logger for JSON output

    Args:
        logger: Logger to configure (defaults to root logger)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_context: Include file/line/function context
        sanitize_secrets: Sanitize sensitive data

    Returns:
        Configured logger

    Example:
        >>> logger = configure_json_logging(level='DEBUG')
        >>> logger.info('Application started', extra={'version': '1.0.0'})
    """
    if logger is None:
        logger = logging.getLogger()

    # Create JSON formatter
    json_formatter = JSONFormatter(
        include_extra=True,
        include_context=include_context,
        sanitize_secrets=sanitize_secrets
    )

    # Remove existing handlers
    logger.handlers.clear()

    # Add console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    # Set level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    return logger


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance

    Example:
        >>> logger = get_structured_logger(__name__)
        >>> logger.set_context(user_id="123", session_id="abc")
        >>> logger.info("User logged in")
    """
    base_logger = logging.getLogger(name)
    return StructuredLogger(base_logger)
