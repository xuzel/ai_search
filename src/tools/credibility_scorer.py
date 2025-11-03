"""Credibility Scorer - Assess source credibility for search results"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.utils.logger import get_logger

logger = get_logger(__name__)


class CredibilityScorer:
    """Score the credibility of sources for search results"""

    # Domain reputation scores (0.0 to 1.0)
    DOMAIN_SCORES = {
        # Academic (highest credibility)
        ".edu": 0.95,
        "arxiv.org": 0.90,
        "scholar.google": 0.92,
        "researchgate.net": 0.85,
        "pubmed.ncbi.nlm.nih.gov": 0.95,
        "ieee.org": 0.90,
        "acm.org": 0.90,
        # Government (very high credibility)
        ".gov": 0.95,
        ".gov.cn": 0.90,  # Chinese government
        # International organizations
        "who.int": 0.92,
        "un.org": 0.92,
        "worldbank.org": 0.90,
        # News - Tier 1 (high credibility)
        "reuters.com": 0.85,
        "apnews.com": 0.85,
        "bbc.com": 0.83,
        "theguardian.com": 0.80,
        "nytimes.com": 0.80,
        "wsj.com": 0.82,
        "ft.com": 0.82,
        # News - Tier 2 (moderate credibility)
        "cnn.com": 0.75,
        "bloomberg.com": 0.78,
        "economist.com": 0.80,
        # Chinese news
        "xinhuanet.com": 0.75,
        "people.com.cn": 0.75,
        # Reference
        "wikipedia.org": 0.70,
        "britannica.com": 0.80,
        # Tech/Professional
        "stackoverflow.com": 0.75,
        "github.com": 0.70,
        "medium.com": 0.60,
        # General blogs/forums (lower credibility)
        "reddit.com": 0.50,
        "quora.com": 0.55,
        "zhihu.com": 0.55,  # Chinese Q&A
    }

    # Content quality indicators (boost score)
    QUALITY_INDICATORS = {
        "peer-reviewed": 0.15,
        "peer reviewed": 0.15,
        "published in": 0.10,
        "research": 0.08,
        "study": 0.08,
        "journal": 0.08,
        "university": 0.08,
        "professor": 0.06,
        "phd": 0.06,
        "doi:": 0.10,  # Digital Object Identifier
        "issn:": 0.08,  # International Standard Serial Number
        "citation": 0.06,
    }

    # Red flags (reduce score)
    RED_FLAGS = {
        "sponsored": -0.10,
        "advertisement": -0.15,
        "affiliate": -0.10,
        "clickbait": -0.20,
        "rumor": -0.25,
        "unverified": -0.20,
        "opinion": -0.05,
        "blog post": -0.05,
    }

    def __init__(self, base_score: float = 0.5):
        """
        Initialize Credibility Scorer

        Args:
            base_score: Base credibility score (default 0.5)
        """
        self.base_score = base_score

    def score_source(
        self,
        url: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Calculate credibility score for a source

        Args:
            url: Source URL
            content: Content text
            title: Title of the source
            metadata: Additional metadata

        Returns:
            Credibility score (0.0 to 1.0)
        """
        score = self.base_score
        details = []

        # 1. Domain reputation
        if url:
            domain_score = self._score_domain(url)
            if domain_score != self.base_score:
                boost = domain_score - self.base_score
                score = domain_score
                details.append(f"domain: {boost:+.2f}")

        # 2. Content quality indicators
        if content:
            content_boost = self._score_content_quality(content)
            score += content_boost
            if content_boost > 0:
                details.append(f"quality: +{content_boost:.2f}")

            # Red flags
            red_flag_penalty = self._check_red_flags(content)
            score += red_flag_penalty
            if red_flag_penalty < 0:
                details.append(f"red_flags: {red_flag_penalty:.2f}")

        # 3. Title signals
        if title:
            title_boost = self._score_title(title)
            score += title_boost
            if title_boost != 0:
                details.append(f"title: {title_boost:+.2f}")

        # 4. Freshness (if date available in metadata)
        if metadata and "date" in metadata:
            freshness_boost = self._score_freshness(metadata["date"])
            score += freshness_boost
            if freshness_boost != 0:
                details.append(f"freshness: {freshness_boost:+.2f}")

        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))

        if details:
            logger.debug(f"Credibility score: {score:.2f} ({', '.join(details)})")

        return score

    def _score_domain(self, url: str) -> float:
        """Score based on domain reputation"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check exact matches first
            for pattern, score in self.DOMAIN_SCORES.items():
                if pattern in domain:
                    return score

            # Check TLD
            if domain.endswith(".edu"):
                return 0.90
            elif domain.endswith(".gov"):
                return 0.92

            return self.base_score

        except Exception as e:
            logger.debug(f"Error parsing URL {url}: {e}")
            return self.base_score

    def _score_content_quality(self, content: str) -> float:
        """Score based on quality indicators in content"""
        content_lower = content.lower()
        boost = 0.0

        for indicator, value in self.QUALITY_INDICATORS.items():
            if indicator in content_lower:
                boost += value

        # Cap boost at 0.25
        return min(boost, 0.25)

    def _check_red_flags(self, content: str) -> float:
        """Check for red flags in content"""
        content_lower = content.lower()
        penalty = 0.0

        for flag, value in self.RED_FLAGS.items():
            if flag in content_lower:
                penalty += value

        # Cap penalty at -0.30
        return max(penalty, -0.30)

    def _score_title(self, title: str) -> float:
        """Score based on title"""
        title_lower = title.lower()

        # Clickbait patterns
        clickbait_patterns = [
            r"you won't believe",
            r"shocking",
            r"one weird trick",
            r"\d+ reasons why",
            r"this is why",
        ]

        for pattern in clickbait_patterns:
            if re.search(pattern, title_lower):
                return -0.10

        # Academic title patterns
        if ":" in title and len(title) > 40:  # Often academic format
            return 0.05

        return 0.0

    def _score_freshness(self, date_str: str) -> float:
        """Score based on content freshness"""
        try:
            # Try to parse date
            # Support formats: 2024, 2024-01, 2024-01-15, etc.
            year_match = re.search(r"202[3-5]", date_str)
            if year_match:
                year = int(year_match.group())
                current_year = datetime.now().year

                # Recent content gets a small boost
                age = current_year - year
                if age == 0:
                    return 0.05  # This year
                elif age == 1:
                    return 0.03  # Last year
                elif age <= 2:
                    return 0.01  # 2 years ago

            return 0.0

        except Exception as e:
            logger.debug(f"Error parsing date {date_str}: {e}")
            return 0.0

    def score_batch(
        self,
        sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Score multiple sources

        Args:
            sources: List of source dicts with url, content, title, metadata

        Returns:
            Sources with added credibility_score field
        """
        for source in sources:
            score = self.score_source(
                url=source.get("url"),
                content=source.get("content") or source.get("text"),
                title=source.get("title"),
                metadata=source.get("metadata"),
            )
            source["credibility_score"] = score

        return sources

    def filter_by_credibility(
        self,
        sources: List[Dict[str, Any]],
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Filter sources by minimum credibility score

        Args:
            sources: List of sources (must have credibility_score)
            min_score: Minimum credibility threshold

        Returns:
            Filtered sources
        """
        return [
            source
            for source in sources
            if source.get("credibility_score", 0.0) >= min_score
        ]

    def rank_by_credibility(
        self,
        sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Sort sources by credibility score (descending)

        Args:
            sources: List of sources (must have credibility_score)

        Returns:
            Sorted sources
        """
        return sorted(
            sources,
            key=lambda x: x.get("credibility_score", 0.0),
            reverse=True,
        )
