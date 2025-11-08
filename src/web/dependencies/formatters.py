"""Formatter Dependencies

Provides singleton formatter instances (markdown processor, etc.).
"""

from typing import Optional
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Singleton markdown processor
_markdown_processor: Optional[markdown.Markdown] = None


def get_markdown_processor() -> markdown.Markdown:
    """Get singleton markdown processor instance

    Returns:
        Configured markdown.Markdown instance
    """
    global _markdown_processor

    if _markdown_processor is None:
        _markdown_processor = markdown.Markdown(
            extensions=[
                FencedCodeExtension(),
                CodeHiliteExtension(),
                TableExtension(),
                'nl2br',
            ]
        )
        logger.info("Markdown processor instance created")

    return _markdown_processor


def convert_markdown_to_html(text: str, processor: Optional[markdown.Markdown] = None) -> str:
    """Convert markdown text to HTML using singleton processor

    Args:
        text: Markdown text to convert
        processor: Optional markdown processor instance (uses singleton if not provided)

    Returns:
        HTML string
    """
    if processor is None:
        processor = get_markdown_processor()

    # Reset processor state for fresh conversion
    processor.reset()
    return processor.convert(text)


# Cleanup function
def cleanup_formatter_dependencies():
    """Cleanup formatter singleton instances"""
    global _markdown_processor

    logger.info("Cleaning up formatter dependency instances")
    _markdown_processor = None
