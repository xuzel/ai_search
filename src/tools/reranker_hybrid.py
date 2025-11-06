"""Hybrid Reranker - Combining multiple ranking signals

This module provides a hybrid reranking approach that combines:
- Semantic relevance (from cross-encoder)
- Source credibility
- Content freshness

Use this for more nuanced ranking in RAG systems.
"""

from typing import Any, Dict, List, Optional

from src.tools.reranker_base import Reranker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HybridReranker:
    """Hybrid reranking combining multiple signals

    Combines semantic relevance with other signals like credibility
    and freshness for more comprehensive ranking.
    """

    def __init__(
        self,
        cross_encoder_model: str = "BAAI/bge-reranker-large",
        device: Optional[str] = None,
    ):
        """
        Initialize Hybrid Reranker

        Args:
            cross_encoder_model: Cross-encoder model name
            device: Device to use (cpu/cuda)
        """
        self.reranker = Reranker(
            model_name=cross_encoder_model,
            device=device,
        )

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid reranking with multiple signals

        Args:
            query: Search query
            documents: Documents with text and optional scores
            weights: Weights for different signals
                    {"semantic": 0.6, "credibility": 0.3, "freshness": 0.1}
            top_k: Number of top results

        Returns:
            Reranked documents with combined scores
        """
        if not documents:
            return []

        # Default weights
        if weights is None:
            weights = {
                "semantic": 0.7,  # Semantic relevance (most important)
                "credibility": 0.2,  # Source credibility
                "freshness": 0.1,  # Content freshness
            }

        # Extract texts for reranking
        texts = [doc.get("text", "") for doc in documents]

        # Get semantic scores
        reranked = self.reranker.rerank(query, texts, top_k=None)

        # Combine scores
        results = []
        for ranked_item in reranked:
            original_idx = ranked_item["original_index"]
            original_doc = documents[original_idx].copy()

            # Semantic score (from reranker)
            semantic_score = ranked_item["score"]

            # Credibility score (if available)
            credibility_score = original_doc.get("credibility_score", 0.5)

            # Freshness score (if available)
            freshness_score = original_doc.get("freshness_score", 0.5)

            # Combined score
            combined_score = (
                weights["semantic"] * semantic_score
                + weights["credibility"] * credibility_score
                + weights["freshness"] * freshness_score
            )

            # Update document
            original_doc["semantic_score"] = semantic_score
            original_doc["combined_score"] = combined_score

            results.append(original_doc)

        # Sort by combined score
        results.sort(key=lambda x: x["combined_score"], reverse=True)

        # Return top k
        if top_k is not None:
            results = results[:top_k]

        logger.info(
            f"Hybrid reranking complete. Top combined score: {results[0]['combined_score']:.4f}"
        )

        return results
