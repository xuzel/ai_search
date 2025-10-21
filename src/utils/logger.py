"""Logging configuration for AI Search Engine"""

import logging
import sys
import os
from typing import Optional

# Get log level from environment or default to INFO
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a logger instance"""
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    return logger
