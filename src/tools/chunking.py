"""Smart Chunking - Intelligent text chunking strategies for RAG"""

import re
from typing import Dict, List

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SmartChunker:
    """Smart text chunking with multiple strategies"""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 77,
        min_chunk_size: int = 100,
        strategy: str = "semantic",
    ):
        """
        Initialize Smart Chunker

        Args:
            chunk_size: Target size of each chunk (in tokens/characters)
            chunk_overlap: Overlap between chunks (15% recommended)
            min_chunk_size: Minimum chunk size
            strategy: Chunking strategy ('fixed', 'semantic', 'recursive')
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.strategy = strategy

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text using the configured strategy

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunks with content and metadata
        """
        if not text or len(text) < self.min_chunk_size:
            return [{"content": text, "metadata": metadata or {}}]

        if self.strategy == "fixed":
            chunks = self._chunk_fixed(text)
        elif self.strategy == "semantic":
            chunks = self._chunk_semantic(text)
        elif self.strategy == "recursive":
            chunks = self._chunk_recursive(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")

        # Add metadata to each chunk
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update(
                {
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunking_strategy": self.strategy,
                }
            )
            result.append({"content": chunk_text, "metadata": chunk_metadata})

        logger.debug(
            f"Created {len(result)} chunks using {self.strategy} strategy "
            f"(size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return result

    def _chunk_fixed(self, text: str) -> List[str]:
        """
        Fixed-size chunking with overlap

        Args:
            text: Text to chunk

        Returns:
            List of chunk strings
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]

            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)

            start += self.chunk_size - self.chunk_overlap

        return chunks

    def _chunk_semantic(self, text: str) -> List[str]:
        """
        Semantic chunking - split on paragraph and sentence boundaries

        Args:
            text: Text to chunk

        Returns:
            List of chunk strings
        """
        # Split by paragraphs first
        paragraphs = re.split(r'\n\n+', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk size, finalize current chunk
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + " " + para
                else:
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_recursive(self, text: str) -> List[str]:
        """
        Recursive chunking - try multiple separators in order

        Args:
            text: Text to chunk

        Returns:
            List of chunk strings
        """
        # Separators in order of preference
        separators = [
            "\n\n",  # Paragraph breaks
            "\n",  # Line breaks
            ". ",  # Sentence breaks
            "! ",
            "? ",
            "; ",
            ", ",  # Clause breaks
            " ",  # Word breaks
        ]

        return self._split_with_separators(text, separators)

    def _split_with_separators(
        self, text: str, separators: List[str]
    ) -> List[str]:
        """
        Recursively split text using a list of separators

        Args:
            text: Text to split
            separators: List of separators to try

        Returns:
            List of chunks
        """
        if not separators:
            # No more separators, return as single chunk
            return [text] if text else []

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split by current separator
        splits = text.split(separator)

        chunks = []
        current_chunk = ""

        for split in splits:
            if not split:
                continue

            # Check if adding this split would exceed chunk size
            if len(current_chunk) + len(separator) + len(split) > self.chunk_size:
                if current_chunk:
                    # Try to further split if needed
                    if len(current_chunk) > self.chunk_size and remaining_separators:
                        sub_chunks = self._split_with_separators(
                            current_chunk, remaining_separators
                        )
                        chunks.extend(sub_chunks)
                    else:
                        chunks.append(current_chunk)

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + separator + split
                else:
                    current_chunk = split
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split

        # Add final chunk
        if current_chunk:
            if len(current_chunk) > self.chunk_size and remaining_separators:
                sub_chunks = self._split_with_separators(
                    current_chunk, remaining_separators
                )
                chunks.extend(sub_chunks)
            else:
                chunks.append(current_chunk)

        # Filter out chunks that are too small
        return [c for c in chunks if len(c) >= self.min_chunk_size]

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Chunk multiple documents

        Args:
            documents: List of documents with 'content' and 'metadata' keys

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            chunks = self.chunk_text(content, metadata)
            all_chunks.extend(chunks)

        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks
