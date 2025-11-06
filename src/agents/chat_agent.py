"""Chat Agent - General conversation agent"""

from typing import Any, Dict, List

from src.llm.manager import LLMManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChatAgent:
    """Chat Agent for general conversation"""

    def __init__(self, llm_manager: LLMManager, config: Any = None):
        """
        Initialize Chat Agent

        Args:
            llm_manager: LLM Manager instance
            config: Configuration object
        """
        self.llm_manager = llm_manager
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []

    async def chat(self, message: str) -> str:
        """
        Send a message and get a response

        Args:
            message: User message

        Returns:
            Agent response
        """

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})

        # Keep conversation history manageable (last 10 exchanges)
        messages = self.conversation_history[-20:]

        try:
            response = await self.llm_manager.complete(messages)
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def set_system_prompt(self, system_prompt: str):
        """Set a system prompt"""
        self.conversation_history = [
            {"role": "system", "content": system_prompt}
        ]
