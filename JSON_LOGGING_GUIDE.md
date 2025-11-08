# JSON Logging Guide

**Date**: 2025-11-05
**Status**: ✅ IMPLEMENTED

## Overview

Structured JSON logging has been implemented for production environments with log aggregation systems (ELK Stack, Splunk, CloudWatch, Datadog, etc.).

## Features

✅ **Structured Output**: All logs in machine-readable JSON format
✅ **Context Support**: Attach persistent context to log messages
✅ **Secret Sanitization**: Automatic redaction of sensitive data
✅ **Exception Handling**: Full stack traces in structured format
✅ **Metadata**: Process, thread, file, line number information
✅ **ELK Compatible**: Works with Elasticsearch, Logstash, Kibana
✅ **Environment-Based**: Enable/disable via environment variable

## Quick Start

### Enable JSON Logging

Set environment variable:
```bash
export LOG_FORMAT=json
export LOG_LEVEL=INFO
python -m src.web.app
```

Or in `.env` file:
```bash
LOG_FORMAT=json
LOG_LEVEL=INFO
LOG_FILE=logs/app.json  # Optional: log to file
```

### Basic Usage

```python
from src.utils import get_logger

logger = get_logger(__name__)
logger.info("Application started", extra={"version": "1.0.0"})
```

**Output**:
```json
{
  "timestamp": "2025-11-05T11:23:46.678Z",
  "level": "INFO",
  "logger": "src.main",
  "message": "Application started",
  "context": {
    "file": "/path/to/main.py",
    "line": 42,
    "function": "main",
    "module": "main"
  },
  "process": {
    "id": 12345,
    "name": "MainProcess"
  },
  "thread": {
    "id": 67890,
    "name": "MainThread"
  },
  "extra": {
    "version": "1.0.0"
  }
}
```

## Advanced Usage

### Structured Logger with Context

Use `StructuredLogger` to attach persistent context fields:

```python
from src.utils import get_structured_logger

logger = get_structured_logger(__name__)

# Set context once (persists for all log calls)
logger.set_context(
    request_id="req-abc-123",
    user_id="user-456",
    session_id="sess-789"
)

# All subsequent logs will include the context
logger.info("User logged in")
logger.info("User performed action", extra={"action": "purchase"})

# Clear context when done
logger.clear_context()
```

**Output**:
```json
{
  "timestamp": "2025-11-05T11:23:46.678Z",
  "level": "INFO",
  "logger": "src.auth",
  "message": "User logged in",
  "context": {...},
  "process": {...},
  "thread": {...},
  "extra": {
    "request_id": "req-abc-123",
    "user_id": "user-456",
    "session_id": "sess-789"
  }
}
```

### Exception Logging

Exceptions are automatically formatted with full stack traces:

```python
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Operation failed", extra={"operation": "risky_op"})
```

**Output**:
```json
{
  "timestamp": "2025-11-05T11:23:46.678Z",
  "level": "ERROR",
  "logger": "src.operations",
  "message": "Operation failed",
  "exception": {
    "type": "ValueError",
    "message": "Invalid input",
    "traceback": [
      "Traceback (most recent call last):",
      "  File \"operations.py\", line 42, in risky_operation",
      "    raise ValueError(\"Invalid input\")",
      "ValueError: Invalid input"
    ]
  },
  "extra": {
    "operation": "risky_op"
  }
}
```

### Configure Specific Logger

Configure a specific logger for JSON output:

```python
from src.utils import configure_json_logging
import logging

# Configure specific logger
logger = configure_json_logging(
    logging.getLogger('my.module'),
    level='DEBUG',
    include_context=True,
    sanitize_secrets=True
)

logger.debug("Debug message")
```

## Use Cases

### 1. Production Monitoring with ELK Stack

**Setup**:
```bash
# docker-compose.yml
services:
  app:
    environment:
      - LOG_FORMAT=json
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
```

**Logstash Config**:
```conf
input {
  file {
    path => "/app/logs/app.json"
    codec => "json"
  }
}

filter {
  # Logs are already structured JSON
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ai-search-engine-%{+YYYY.MM.dd}"
  }
}
```

**Kibana Queries**:
```
# Find all errors from specific module
level: ERROR AND logger: "src.agents.research_agent"

# Find logs with specific user
extra.user_id: "user-123"

# Find logs in time range with specific action
timestamp: [now-1h TO now] AND extra.action: "login"
```

### 2. AWS CloudWatch Logs

**Lambda Function**:
```python
import os
os.environ['LOG_FORMAT'] = 'json'

from src.utils import get_structured_logger

logger = get_structured_logger(__name__)

def lambda_handler(event, context):
    logger.set_context(
        request_id=context.request_id,
        function_name=context.function_name
    )

    logger.info("Lambda invoked", extra={"event_type": event.get("type")})

    # ... process event ...

    return {"statusCode": 200, "body": "Success"}
```

**CloudWatch Insights Query**:
```
fields @timestamp, message, extra.event_type, extra.request_id
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

### 3. Request Tracing in Web App

**FastAPI Middleware**:
```python
from fastapi import FastAPI, Request
from src.utils import get_structured_logger
import uuid

app = FastAPI()
logger = get_structured_logger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    logger.set_context(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )

    logger.info("Request started")

    response = await call_next(request)

    logger.info("Request completed", extra={"status_code": response.status_code})
    logger.clear_context()

    return response
```

### 4. Performance Monitoring

```python
import time
from src.utils import get_structured_logger

logger = get_structured_logger(__name__)

def slow_operation():
    start_time = time.time()

    try:
        # ... operation ...
        result = perform_operation()

        duration = time.time() - start_time
        logger.info(
            "Operation completed",
            extra={
                "duration_ms": int(duration * 1000),
                "operation": "perform_operation",
                "status": "success"
            }
        )
        return result

    except Exception as e:
        duration = time.time() - start_time
        logger.exception(
            "Operation failed",
            extra={
                "duration_ms": int(duration * 1000),
                "operation": "perform_operation",
                "status": "failed"
            }
        )
        raise
```

## Secret Sanitization

Sensitive data is automatically redacted from logs:

```python
logger.info("User authenticated", extra={
    "username": "john_doe",
    "api_key": "sk-abc123",  # Will be redacted
    "password": "secret123"  # Will be redacted
})
```

**Output**:
```json
{
  "message": "User authenticated",
  "extra": {
    "username": "john_doe",
    "api_key": "***REDACTED***",
    "password": "***REDACTED***"
  }
}
```

## Format Comparison

### Standard Format (Text)
```
2025-11-05 11:23:46 - src.main - INFO - Application started
```

### Detailed Format (Text)
```
2025-11-05 11:23:46 - src.main - INFO - [main.py:42] - Application started
```

### JSON Format (Structured)
```json
{
  "timestamp": "2025-11-05T11:23:46.678Z",
  "level": "INFO",
  "logger": "src.main",
  "message": "Application started",
  "context": {"file": "main.py", "line": 42, "function": "main", "module": "main"},
  "process": {"id": 12345, "name": "MainProcess"},
  "thread": {"id": 67890, "name": "MainThread"}
}
```

## Configuration Options

| Environment Variable | Values | Description |
|---------------------|--------|-------------|
| `LOG_FORMAT` | `standard`, `detailed`, `json` | Output format |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | Minimum log level |
| `LOG_FILE` | File path | Optional file output |

## Best Practices

### DO:
✅ Use structured logger for request handling
✅ Include relevant context in `extra` fields
✅ Use consistent key names across services
✅ Log structured data, not formatted strings
✅ Include timing/performance metrics

```python
# Good
logger.info("Order processed", extra={
    "order_id": "ord-123",
    "user_id": "user-456",
    "amount": 99.99,
    "duration_ms": 245
})
```

### DON'T:
❌ Don't log formatted strings in JSON mode
❌ Don't include secrets/PII without sanitization
❌ Don't log binary data
❌ Don't use inconsistent key names

```python
# Bad
logger.info(f"Order ord-123 for user user-456 amount $99.99 took 245ms")
```

## Migration from Text Logging

**Before (Text)**:
```python
logger.info(f"User {user_id} logged in from {ip_address}")
```

**After (JSON)**:
```python
logger.info("User logged in", extra={
    "user_id": user_id,
    "ip_address": ip_address,
    "event": "login"
})
```

## Troubleshooting

### Issue: JSON logs not appearing

**Check**:
1. Verify `LOG_FORMAT=json` is set before importing logger
2. Check if application is using `get_logger()` from `src.utils`
3. Verify no custom logging configuration overrides

### Issue: Logs missing context fields

**Solution**: Use `StructuredLogger` instead of base logger:
```python
from src.utils import get_structured_logger
logger = get_structured_logger(__name__)
logger.set_context(request_id="...")
```

### Issue: Secrets appearing in logs

**Check**: Ensure `sanitize_secrets=True` in JSONFormatter (enabled by default)

## Performance Impact

- **Text Logging**: ~0.1ms per log call
- **JSON Logging**: ~0.2ms per log call
- **Overhead**: Approximately 2x, negligible for most applications

## References

- **ELK Stack**: https://www.elastic.co/what-is/elk-stack
- **Splunk**: https://www.splunk.com/
- **CloudWatch Logs**: https://aws.amazon.com/cloudwatch/
- **JSON Log Format**: https://jsonlines.org/
- **Structured Logging**: https://www.structlog.org/

## Related Files

- Implementation: `src/utils/json_logger.py`
- Configuration: `src/utils/logger.py`
- Examples: This file
- Environment: `.env.example`
