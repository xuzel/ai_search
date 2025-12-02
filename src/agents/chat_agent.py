"""Chat Agent - General conversation agent with history compression"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from src.llm.manager import LLMManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChatAgent:
    """Chat Agent for general conversation with history compression"""

    def __init__(
        self,
        llm_manager: LLMManager,
        config: Any = None,
        max_history: int = 20,
        compression_threshold: int = 15,
        enable_compression: bool = True
    ):
        """
        Initialize Chat Agent

        Args:
            llm_manager: LLM Manager instance
            config: Configuration object
            max_history: Maximum messages to keep in history
            compression_threshold: Number of messages to trigger compression
            enable_compression: Whether to enable history compression
        """
        self.llm_manager = llm_manager
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = max_history
        self.compression_threshold = compression_threshold
        self.enable_compression = enable_compression
        self._compressed_summary: Optional[str] = None

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

        # Check if compression is needed
        if self.enable_compression and len(self.conversation_history) >= self.compression_threshold:
            await self._compress_history()

        # Build messages with optional compressed summary
        messages = self._build_messages()

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

    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        """
        Send a message and get a streaming response

        Args:
            message: User message

        Yields:
            Response chunks as they arrive
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})

        # Check if compression is needed
        if self.enable_compression and len(self.conversation_history) >= self.compression_threshold:
            await self._compress_history()

        # Build messages with optional compressed summary
        messages = self._build_messages()

        try:
            full_response = ""
            async for chunk in self.llm_manager.stream_complete(messages):
                full_response += chunk
                yield chunk

            # Store complete response in history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })

        except Exception as e:
            logger.error(f"Streaming chat error: {e}")
            raise

    def clear_history(self):
        """Clear conversation history and compressed summary"""
        self.conversation_history = []
        self._compressed_summary = None

    def set_system_prompt(self, system_prompt: str):
        """Set a system prompt"""
        self.conversation_history = [
            {"role": "system", "content": system_prompt}
        ]
        self._compressed_summary = None

    def _build_messages(self) -> List[Dict[str, str]]:
        """
        Build messages list with optional compressed summary

        Returns:
            List of messages for LLM
        """
        messages = []

        # Add compressed summary as system context if available
        if self._compressed_summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary:\n{self._compressed_summary}"
            })

        # Add recent history (respect max_history limit)
        recent_history = self.conversation_history[-self.max_history:]

        # Check for existing system prompt
        has_system = any(m.get("role") == "system" for m in recent_history)

        if has_system:
            messages.extend(recent_history)
        else:
            messages.extend(recent_history)

        return messages

    async def _compress_history(self) -> None:
        """
        Compress older conversation history into a summary

        This reduces token usage while preserving context.
        """
        # Keep the most recent messages, compress the rest
        keep_recent = 6  # Keep last 3 exchanges (6 messages)

        if len(self.conversation_history) <= keep_recent:
            return

        # Messages to compress
        to_compress = self.conversation_history[:-keep_recent]

        # Skip if nothing to compress
        if len(to_compress) < 4:
            return

        # Build compression prompt
        conversation_text = ""
        for msg in to_compress:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "system":
                continue  # Don't include system prompts in summary
            conversation_text += f"{role.upper()}: {content}\n\n"

        if not conversation_text.strip():
            return

        compress_prompt = f"""Summarize the following conversation concisely, preserving key topics, decisions, and important context. Keep it brief (2-4 sentences):

{conversation_text}

Summary:"""

        try:
            summary = await self.llm_manager.complete(
                [{"role": "user", "content": compress_prompt}],
                max_tokens=200
            )

            # Merge with existing summary if present
            if self._compressed_summary:
                self._compressed_summary = f"{self._compressed_summary}\n\nLater: {summary}"
            else:
                self._compressed_summary = summary

            # Keep only recent messages plus any system prompt
            system_prompts = [m for m in self.conversation_history if m.get("role") == "system"]
            recent = self.conversation_history[-keep_recent:]
            self.conversation_history = system_prompts + recent

            logger.info(f"Compressed {len(to_compress)} messages into summary")

        except Exception as e:
            logger.warning(f"History compression failed: {e}")
            # Fallback: just truncate without summary
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_history_stats(self) -> Dict[str, Any]:
        """Get conversation history statistics"""
        return {
            "message_count": len(self.conversation_history),
            "has_summary": self._compressed_summary is not None,
            "summary_length": len(self._compressed_summary) if self._compressed_summary else 0,
            "compression_enabled": self.enable_compression,
        }

    def set_compression_enabled(self, enabled: bool) -> None:
        """Enable or disable history compression"""
        self.enable_compression = enabled
        logger.info(f"History compression {'enabled' if enabled else 'disabled'}")
