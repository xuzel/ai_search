"""Task Type Definitions

Centralized task type enumeration used across the routing system.
"""

from enum import Enum


class TaskType(Enum):
    """Task type enumeration for routing decisions"""

    # Core task types
    RESEARCH = "research"
    CODE = "code"
    CHAT = "chat"

    # Document processing
    RAG = "rag"  # Document Q&A

    # Domain-specific tasks
    DOMAIN_WEATHER = "domain_weather"
    DOMAIN_FINANCE = "domain_finance"
    DOMAIN_ROUTING = "domain_routing"

    # Multimodal tasks
    MULTIMODAL_OCR = "multimodal_ocr"
    MULTIMODAL_VISION = "multimodal_vision"

    # Workflow tasks
    WORKFLOW = "workflow"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> 'TaskType':
        """Create TaskType from string value

        Args:
            value: String representation of task type

        Returns:
            TaskType enum

        Raises:
            ValueError: If value is not a valid task type
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid task type: {value}")
