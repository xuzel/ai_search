"""Result Aggregator - Combines and synthesizes results from multiple sources

Features:
- Merge search results from different sources
- Deduplicate content
- Synthesize information using LLM
- Create unified summaries
- Rank and prioritize results
"""

from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass
import hashlib
from difflib import SequenceMatcher

from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.llm import LLMManager

logger = get_logger(__name__)


@dataclass
class AggregatedResult:
    """
    Aggregated result from multiple sources

    Attributes:
        summary: Synthesized summary
        sources: List of source results
        key_points: Extracted key points
        confidence: Confidence score (0.0-1.0)
        metadata: Additional metadata
    """
    summary: str
    sources: List[Dict[str, Any]]
    key_points: List[str]
    confidence: float
    metadata: Dict[str, Any]


class ResultAggregator:
    """
    Aggregates and synthesizes results from multiple sources

    Example:
        aggregator = ResultAggregator(llm_manager)

        # Combine search results from multiple sources
        results = [
            {"source": "google", "title": "...", "content": "..."},
            {"source": "bing", "title": "...", "content": "..."},
        ]

        aggregated = await aggregator.aggregate(
            results,
            query="original query",
            strategy="synthesis"
        )
    """

    def __init__(
        self,
        llm_manager: Optional["LLMManager"] = None,
        similarity_threshold: float = 0.85,
    ):
        """
        Initialize Result Aggregator

        Args:
            llm_manager: Optional LLM manager for synthesis
            similarity_threshold: Threshold for deduplication (0.0-1.0)
        """
        self.llm_manager = llm_manager
        self.similarity_threshold = similarity_threshold

        logger.info("ResultAggregator initialized")

    async def aggregate(
        self,
        results: List[Dict[str, Any]],
        query: Optional[str] = None,
        strategy: str = "synthesis",
    ) -> AggregatedResult:
        """
        Aggregate results from multiple sources

        Args:
            results: List of result dicts (must have 'content' or 'text' field)
            query: Optional original query for context
            strategy: Aggregation strategy:
                     - "synthesis": LLM-based synthesis (default)
                     - "concatenate": Simple concatenation
                     - "ranking": Rank and take top results

        Returns:
            AggregatedResult
        """
        if not results:
            return AggregatedResult(
                summary="No results to aggregate",
                sources=[],
                key_points=[],
                confidence=0.0,
                metadata={},
            )

        logger.info(f"Aggregating {len(results)} results using {strategy} strategy")

        # Step 1: Deduplicate
        deduplicated = self.deduplicate(results)
        logger.debug(f"Deduplicated: {len(results)} -> {len(deduplicated)} results")

        # Step 2: Extract content
        contents = self._extract_contents(deduplicated)

        # Step 3: Aggregate based on strategy
        if strategy == "synthesis" and self.llm_manager:
            return await self._synthesize_results(deduplicated, contents, query)
        elif strategy == "ranking":
            return self._rank_and_aggregate(deduplicated, contents, query)
        else:  # concatenate
            return self._concatenate_results(deduplicated, contents)

    def deduplicate(
        self,
        results: List[Dict[str, Any]],
        key: str = "content",
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate or highly similar results

        Args:
            results: List of results
            key: Field to use for comparison (default: "content")

        Returns:
            Deduplicated results
        """
        if not results:
            return []

        unique_results = []
        seen_hashes: Set[str] = set()
        seen_contents: List[str] = []

        for result in results:
            # Extract content
            content = self._get_content(result, key)

            if not content:
                continue

            # Check exact duplicates (hash-based)
            content_hash = hashlib.md5(content.encode()).hexdigest()

            if content_hash in seen_hashes:
                continue

            # Check similar content (similarity-based)
            is_similar = False
            for seen_content in seen_contents:
                similarity = self._compute_similarity(content, seen_content)
                if similarity >= self.similarity_threshold:
                    is_similar = True
                    break

            if is_similar:
                continue

            # Add to unique results
            seen_hashes.add(content_hash)
            seen_contents.append(content)
            unique_results.append(result)

        return unique_results

    def merge_search_results(
        self,
        search_results: List[List[Dict[str, Any]]],
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Merge search results from multiple sources

        Args:
            search_results: List of search result lists
            max_results: Maximum results to return

        Returns:
            Merged and deduplicated results
        """
        # Flatten results
        all_results = []
        for results in search_results:
            all_results.extend(results)

        # Deduplicate
        unique_results = self.deduplicate(all_results)

        # Sort by relevance/score if available
        unique_results.sort(
            key=lambda x: x.get("score", 0.0) + x.get("credibility", 0.0),
            reverse=True,
        )

        # Return top results
        return unique_results[:max_results]

    async def synthesize_from_multiple_agents(
        self,
        agent_results: Dict[str, Any],
        query: str,
    ) -> AggregatedResult:
        """
        Synthesize results from multiple agents (research, code, RAG, etc.)

        Args:
            agent_results: Dict of agent_name -> result
            query: Original query

        Returns:
            AggregatedResult
        """
        if not agent_results:
            return AggregatedResult(
                summary="No agent results to synthesize",
                sources=[],
                key_points=[],
                confidence=0.0,
                metadata={},
            )

        # Convert agent results to list format
        results = []
        for agent_name, result in agent_results.items():
            results.append({
                "source": agent_name,
                "content": str(result),
                "agent": agent_name,
            })

        # Aggregate
        return await self.aggregate(results, query, strategy="synthesis")

    def _extract_contents(
        self,
        results: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract content strings from results"""
        contents = []
        for result in results:
            content = self._get_content(result)
            if content:
                contents.append(content)
        return contents

    def _get_content(
        self,
        result: Dict[str, Any],
        key: str = "content",
    ) -> str:
        """Get content from result dict (tries multiple keys)"""
        # Try specified key first
        if key in result:
            return str(result[key])

        # Try common keys
        for k in ["content", "text", "summary", "answer", "description"]:
            if k in result:
                return str(result[k])

        # Try title if nothing else
        if "title" in result:
            return str(result["title"])

        return ""

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts (0.0-1.0)"""
        return SequenceMatcher(None, text1, text2).ratio()

    async def _synthesize_results(
        self,
        results: List[Dict[str, Any]],
        contents: List[str],
        query: Optional[str] = None,
    ) -> AggregatedResult:
        """Synthesize results using LLM"""

        # Build synthesis prompt
        sources_text = ""
        for i, (result, content) in enumerate(zip(results, contents), 1):
            source_name = result.get("source", result.get("title", f"Source {i}"))
            sources_text += f"\n[Source {i}: {source_name}]\n{content}\n"

        query_context = f'Original query: "{query}"\n\n' if query else ""

        prompt = f"""{query_context}You are an information synthesis assistant.
Analyze the following sources and create a comprehensive, unified summary.

Sources:
{sources_text}

Instructions:
1. Synthesize information from all sources
2. Identify key points and main themes
3. Resolve any contradictions or inconsistencies
4. Create a coherent, well-structured summary
5. Extract 3-5 key points as bullet points

Respond in JSON format:
{{
    "summary": "Comprehensive synthesis of all sources",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = await self.llm_manager.complete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )

            # Parse JSON
            import json
            import re

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON in LLM response")

            data = json.loads(json_match.group())

            return AggregatedResult(
                summary=data.get("summary", ""),
                sources=results,
                key_points=data.get("key_points", []),
                confidence=float(data.get("confidence", 0.7)),
                metadata={"strategy": "synthesis", "source_count": len(results)},
            )

        except Exception as e:
            logger.error(f"Synthesis failed: {e}, falling back to concatenation")
            return self._concatenate_results(results, contents)

    def _rank_and_aggregate(
        self,
        results: List[Dict[str, Any]],
        contents: List[str],
        query: Optional[str] = None,
    ) -> AggregatedResult:
        """Rank results and aggregate top ones"""

        # Sort by score/credibility
        ranked = sorted(
            zip(results, contents),
            key=lambda x: x[0].get("score", 0.0) + x[0].get("credibility", 0.0),
            reverse=True,
        )

        # Take top 3
        top_results = ranked[:3]

        # Extract key points from top results
        key_points = []
        for result, _ in top_results:
            if "title" in result:
                key_points.append(result["title"])

        # Create summary from top results
        summary_parts = []
        for i, (result, content) in enumerate(top_results, 1):
            source = result.get("source", result.get("title", f"Source {i}"))
            snippet = content[:300] + "..." if len(content) > 300 else content
            summary_parts.append(f"[{source}] {snippet}")

        summary = "\n\n".join(summary_parts)

        return AggregatedResult(
            summary=summary,
            sources=[r for r, _ in top_results],
            key_points=key_points,
            confidence=0.7,
            metadata={"strategy": "ranking", "source_count": len(results)},
        )

    def _concatenate_results(
        self,
        results: List[Dict[str, Any]],
        contents: List[str],
    ) -> AggregatedResult:
        """Simple concatenation of results"""

        # Concatenate contents
        summary = "\n\n---\n\n".join(contents)

        # Extract titles as key points
        key_points = []
        for result in results:
            if "title" in result:
                key_points.append(result["title"])

        return AggregatedResult(
            summary=summary,
            sources=results,
            key_points=key_points[:5],  # Max 5
            confidence=0.5,
            metadata={"strategy": "concatenate", "source_count": len(results)},
        )

    def extract_key_points(
        self,
        text: str,
        max_points: int = 5,
    ) -> List[str]:
        """
        Extract key points from text (simple heuristic)

        Args:
            text: Input text
            max_points: Maximum number of points

        Returns:
            List of key points
        """
        # Split by sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        # Score sentences (simple heuristic: length + keyword presence)
        scored_sentences = []
        keywords = ["important", "key", "main", "significant", "critical", "primarily"]

        for sentence in sentences:
            score = len(sentence)  # Longer sentences = more information

            # Boost score for keyword presence
            for keyword in keywords:
                if keyword in sentence.lower():
                    score += 50

            scored_sentences.append((score, sentence))

        # Sort by score and take top
        scored_sentences.sort(reverse=True)
        key_points = [s for _, s in scored_sentences[:max_points]]

        return key_points

    def compute_aggregate_confidence(
        self,
        results: List[Dict[str, Any]],
    ) -> float:
        """
        Compute confidence score for aggregated results

        Factors:
        - Number of sources (more = higher)
        - Source credibility scores
        - Content consistency

        Returns:
            Confidence score (0.0-1.0)
        """
        if not results:
            return 0.0

        # Base confidence from source count
        source_count_score = min(len(results) / 5.0, 1.0)  # Max at 5 sources

        # Average credibility
        credibility_scores = [r.get("credibility", 0.5) for r in results]
        avg_credibility = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 0.5

        # Combine scores
        confidence = (source_count_score * 0.4 + avg_credibility * 0.6)

        return min(confidence, 1.0)
