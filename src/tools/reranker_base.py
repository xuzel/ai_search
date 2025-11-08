"""Base Reranker - Improve retrieval quality with cross-encoder models"""

from typing import Any, Dict, List, Optional

from sentence_transformers import CrossEncoder

from src.utils.logger import get_logger

logger = get_logger(__name__)


class Reranker:
    """Rerank search results using cross-encoder models

    This is the base reranker that uses cross-encoder models to score
    query-document pairs for semantic relevance.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-large",
        max_length: int = 512,
        device: Optional[str] = None,
    ):
        """
        Initialize Reranker

        Args:
            model_name: Cross-encoder model name
            max_length: Maximum sequence length
            device: Device to use (cpu/cuda), auto-detect if None
        """
        self.model_name = model_name
        self.max_length = max_length

        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(
            model_name,
            max_length=max_length,
            device=device,
        )
        # Safely get device info
        device_info = getattr(self.model, 'device', 'unknown')
        logger.info(f"Reranker model loaded on device: {device_info}")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents by relevance to query

        Args:
            query: Search query
            documents: List of document texts
            top_k: Number of top results to return (None = all)

        Returns:
            List of dicts with text, score, and original index
        """
        if not documents:
            return []

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Predict relevance scores
        logger.debug(f"Reranking {len(documents)} documents")
        scores = self.model.predict(pairs)

        # Create results with scores
        results = []
        for idx, (doc, score) in enumerate(zip(documents, scores)):
            results.append(
                {
                    "text": doc,
                    "score": float(score),
                    "original_index": idx,
                }
            )

        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Return top k
        if top_k is not None:
            results = results[:top_k]

        logger.debug(
            f"Reranked results, top score: {results[0]['score']:.4f}, "
            f"bottom score: {results[-1]['score']:.4f}"
        )

        return results

    def rerank_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents with metadata preservation

        Args:
            query: Search query
            documents: List of document dicts with text and metadata
            text_field: Field name containing text
            top_k: Number of top results to return

        Returns:
            Reranked documents with updated scores
        """
        if not documents:
            return []

        # Extract texts
        texts = [doc[text_field] for doc in documents]

        # Rerank
        reranked = self.rerank(query, texts, top_k=None)

        # Merge with original metadata
        results = []
        for ranked_item in reranked:
            original_idx = ranked_item["original_index"]
            original_doc = documents[original_idx].copy()

            # Update score
            original_doc["rerank_score"] = ranked_item["score"]

            results.append(original_doc)

        # Return top k
        if top_k is not None:
            results = results[:top_k]

        return results

    def batch_rerank(
        self,
        queries: List[str],
        documents_list: List[List[str]],
        top_k: Optional[int] = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        Rerank multiple query-document sets in batch

        Args:
            queries: List of queries
            documents_list: List of document lists (one per query)
            top_k: Number of top results per query

        Returns:
            List of reranked results (one list per query)
        """
        results = []

        for query, documents in zip(queries, documents_list):
            reranked = self.rerank(query, documents, top_k=top_k)
            results.append(reranked)

        return results
