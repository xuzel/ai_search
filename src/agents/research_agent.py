"""Research Agent - Conducts web research and synthesizes information"""

import json
from typing import Any, Dict, List, Optional

from src.llm.manager import LLMManager
from src.tools.scraper import ScraperTool
from src.tools.search import SearchTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent:
    """Research Agent for conducting web research"""

    def __init__(
        self,
        llm_manager: LLMManager,
        search_tool: SearchTool,
        scraper_tool: ScraperTool,
        config: Any = None,
    ):
        """
        Initialize Research Agent

        Args:
            llm_manager: LLM Manager instance
            search_tool: Search Tool instance
            scraper_tool: Scraper Tool instance
            config: Configuration object
        """
        self.llm_manager = llm_manager
        self.search_tool = search_tool
        self.scraper_tool = scraper_tool
        self.config = config

        # Extract config parameters
        if config:
            self.max_queries = getattr(config.research, 'max_queries', 5)
            self.top_results_per_query = getattr(
                config.research, 'top_results_per_query', 3
            )
            self.summary_max_tokens = getattr(
                config.research, 'summary_max_tokens', 500
            )
        else:
            self.max_queries = 5
            self.top_results_per_query = 3
            self.summary_max_tokens = 500

    async def research(
        self,
        query: str,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        Conduct research on a query

        Args:
            query: Research query
            show_progress: Show progress information

        Returns:
            Dict with 'query', 'plan', 'sources', 'summary'
        """

        logger.info(f"Starting research on: {query}")

        # Step 1: Generate search plan
        if show_progress:
            print("\n🔍 Generating search plan...")

        search_plan = await self._generate_search_plan(query)
        search_queries = search_plan.get("queries", [query])[:self.max_queries]

        if show_progress:
            print(f"📋 Generated {len(search_queries)} search queries:")
            for i, q in enumerate(search_queries, 1):
                print(f"   {i}. {q}")

        # Step 2: Execute searches
        if show_progress:
            print(f"\n🔎 Executing searches...")

        search_results = await self.search_tool.batch_search(
            search_queries,
            num_results_per_query=self.top_results_per_query,
        )

        # Flatten results
        all_results = []
        for query_results in search_results.values():
            all_results.extend(query_results)

        if show_progress:
            print(f"✅ Found {len(all_results)} results")

        # Step 3: Scrape top results
        if show_progress:
            print(f"\n📄 Scraping content from top results...")

        top_urls = [r["link"] for r in all_results[:5]]
        scraped_content = await self.scraper_tool.batch_scrape(
            top_urls,
            extract_text=True,
            max_content_length=2000,
        )

        if show_progress:
            print(f"✅ Scraped {len(scraped_content)} pages")

        # Step 4: Summarize information
        if show_progress:
            print(f"\n📝 Synthesizing information...")

        summary = await self._synthesize_information(
            query,
            search_results,
            scraped_content,
        )

        result = {
            "query": query,
            "plan": search_plan,
            "sources": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in all_results[:5]
            ],
            "summary": summary,
        }

        if show_progress:
            print("✅ Research complete!")

        return result

    async def _generate_search_plan(self, query: str) -> Dict[str, Any]:
        """Generate search queries for the research"""

        prompt = f"""You are a research assistant. Given the following query, generate 3-5 specific and relevant search queries that would help answer it comprehensively.

Query: {query}

Return ONLY a JSON object with this structure:
{{
    "reasoning": "brief explanation of the search strategy",
    "queries": ["query1", "query2", "query3", ...]
}}"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm_manager.complete(messages)

            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"reasoning": "", "queries": [query]}

        except Exception as e:
            logger.error(f"Error generating search plan: {e}")
            return {"reasoning": "", "queries": [query]}

    async def _summarize_content(self, url: str, content: str) -> str:
        """Summarize extracted content"""

        if not content or len(content) < 100:
            return content

        prompt = f"""Summarize the following content in 2-3 sentences, focusing on key information relevant to research:

Content:
{content}

Provide a concise summary:"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            return await self.llm_manager.complete(
                messages,
                max_tokens=self.summary_max_tokens,
            )
        except Exception as e:
            logger.error(f"Error summarizing content: {e}")
            return content[:500]

    async def _synthesize_information(
        self,
        query: str,
        search_results: Dict[str, List[Dict[str, str]]],
        scraped_content: List[Dict[str, str]],
    ) -> str:
        """Synthesize all information into a comprehensive answer"""

        # Prepare context from scraped content
        sources_text = ""
        for item in scraped_content:
            if item.get("content"):
                sources_text += f"\n---\nSource: {item.get('title', 'Untitled')}\nURL: {item.get('url', '')}\nContent:\n{item.get('content', '')}\n"

        prompt = f"""Based on the following research materials, provide a comprehensive answer to the query. Include specific facts and cite the sources.

Query: {query}

Research Materials:
{sources_text}

Please provide:
1. A direct answer to the query
2. Key findings and facts
3. Source citations

Answer:"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            return await self.llm_manager.complete(messages, max_tokens=1000)
        except Exception as e:
            logger.error(f"Error synthesizing information: {e}")
            return "Unable to synthesize information"
