"""Entity Extraction Utilities

Simple pattern-based entity extraction for domain-specific queries.
Extracts locations, stock symbols, and route information without heavy NLP dependencies.
"""

import re
from typing import Dict, Optional, Tuple, List


class EntityExtractor:
    """Extract entities from user queries using pattern matching"""

    # Common city names (English and Chinese)
    CITIES = {
        # Major Chinese cities
        "北京", "beijing", "上海", "shanghai", "广州", "guangzhou",
        "深圳", "shenzhen", "成都", "chengdu", "杭州", "hangzhou",
        "武汉", "wuhan", "西安", "xian", "南京", "nanjing",
        "天津", "tianjin", "重庆", "chongqing", "苏州", "suzhou",

        # Major international cities
        "tokyo", "london", "paris", "new york", "newyork", "los angeles",
        "singapore", "hong kong", "hongkong", "sydney", "melbourne",
        "dubai", "toronto", "vancouver", "san francisco", "seattle",
        "chicago", "boston", "washington", "miami", "las vegas",
    }

    # Weather-related keywords to remove
    WEATHER_KEYWORDS = {
        "天气", "weather", "forecast", "temperature", "temp",
        "今天", "明天", "后天", "today", "tomorrow", "how",
        "what", "what's", "whats", "how's", "hows", "的", "in"
    }

    # Stock symbol patterns (1-5 uppercase letters)
    STOCK_SYMBOL_PATTERN = re.compile(r'\b([A-Z]{1,5})\b')

    # Common stock-related keywords
    STOCK_KEYWORDS = {
        "stock", "price", "quote", "ticker", "shares", "equity",
        "股票", "价格", "股价", "行情"
    }

    # Routing keywords
    ROUTING_KEYWORDS = {
        "from", "to", "route", "navigate", "directions", "way",
        "从", "到", "去", "路线", "导航"
    }

    @staticmethod
    def extract_location(query: str) -> str:
        """Extract location from weather query

        Args:
            query: User query string

        Returns:
            Extracted location or default "Beijing"

        Examples:
            >>> extract_location("北京天气")
            'Beijing'
            >>> extract_location("What's the weather in London?")
            'London'
        """
        # Normalize query
        query_lower = query.lower()

        # Remove weather keywords
        cleaned = query_lower
        for keyword in EntityExtractor.WEATHER_KEYWORDS:
            cleaned = cleaned.replace(keyword, " ")

        # Remove punctuation and extra spaces
        cleaned = re.sub(r'[?!.,;:""'']', ' ', cleaned)
        cleaned = ' '.join(cleaned.split())

        # Check for known cities
        for city in EntityExtractor.CITIES:
            if city in cleaned or city in query_lower:
                # Return capitalized English name
                return EntityExtractor._normalize_city_name(city)

        # If no city found, try to extract first meaningful word
        words = cleaned.split()
        if words:
            # Filter out common words
            stop_words = {"the", "in", "of", "a", "an", "is", "for", "at"}
            meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
            if meaningful_words:
                return meaningful_words[0].capitalize()

        # Default to Beijing
        return "Beijing"

    @staticmethod
    def _normalize_city_name(city: str) -> str:
        """Normalize city name to English capitalized form"""
        city_map = {
            "北京": "Beijing",
            "beijing": "Beijing",
            "上海": "Shanghai",
            "shanghai": "Shanghai",
            "广州": "Guangzhou",
            "guangzhou": "Guangzhou",
            "深圳": "Shenzhen",
            "shenzhen": "Shenzhen",
            "成都": "Chengdu",
            "chengdu": "Chengdu",
            "杭州": "Hangzhou",
            "hangzhou": "Hangzhou",
            "武汉": "Wuhan",
            "wuhan": "Wuhan",
            "西安": "Xian",
            "xian": "Xian",
            "南京": "Nanjing",
            "nanjing": "Nanjing",
            "天津": "Tianjin",
            "tianjin": "Tianjin",
            "重庆": "Chongqing",
            "chongqing": "Chongqing",
            "苏州": "Suzhou",
            "suzhou": "Suzhou",
            "tokyo": "Tokyo",
            "london": "London",
            "paris": "Paris",
            "new york": "New York",
            "newyork": "New York",
            "los angeles": "Los Angeles",
            "singapore": "Singapore",
            "hong kong": "Hong Kong",
            "hongkong": "Hong Kong",
            "sydney": "Sydney",
            "melbourne": "Melbourne",
            "dubai": "Dubai",
            "toronto": "Toronto",
            "vancouver": "Vancouver",
            "san francisco": "San Francisco",
            "seattle": "Seattle",
            "chicago": "Chicago",
            "boston": "Boston",
            "washington": "Washington",
            "miami": "Miami",
            "las vegas": "Las Vegas",
        }
        return city_map.get(city.lower(), city.capitalize())

    @staticmethod
    def extract_stock_symbol(query: str) -> str:
        """Extract stock symbol from finance query

        Args:
            query: User query string

        Returns:
            Extracted stock symbol or default "AAPL"

        Examples:
            >>> extract_stock_symbol("What's the price of TSLA?")
            'TSLA'
            >>> extract_stock_symbol("Google stock price")
            'GOOGL'
        """
        # First try direct pattern match for symbols (1-5 uppercase letters)
        matches = EntityExtractor.STOCK_SYMBOL_PATTERN.findall(query)

        # Filter out common words that might match
        common_words = {"I", "A", "API", "USD", "US", "UK", "EU", "AI", "IT", "HR", "PR"}
        valid_matches = [m for m in matches if m not in common_words]

        if valid_matches:
            return valid_matches[0]

        # Try company name to symbol mapping
        company_symbols = {
            "apple": "AAPL",
            "google": "GOOGL",
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "nvidia": "NVDA",
            "amd": "AMD",
            "intel": "INTC",
            "alibaba": "BABA",
            "tencent": "TCEHY",
            "baidu": "BIDU",
            "阿里巴巴": "BABA",
            "腾讯": "TCEHY",
            "百度": "BIDU",
        }

        query_lower = query.lower()
        for company, symbol in company_symbols.items():
            if company in query_lower:
                return symbol

        # Default to AAPL
        return "AAPL"

    @staticmethod
    def extract_route(query: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract origin and destination from routing query

        Args:
            query: User query string

        Returns:
            Tuple of (origin, destination) or (None, None) if not found

        Examples:
            >>> extract_route("Route from Beijing to Shanghai")
            ('Beijing', 'Shanghai')
            >>> extract_route("从北京到上海")
            ('Beijing', 'Shanghai')
        """
        # Pattern 1: "from X to Y"
        from_to_pattern = re.compile(
            r'from\s+([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+)',
            re.IGNORECASE
        )
        match = from_to_pattern.search(query)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return (
                EntityExtractor._normalize_city_name(origin),
                EntityExtractor._normalize_city_name(destination)
            )

        # Pattern 2: "从 X 到/去 Y" (Chinese)
        # Supports both "到" and "去"
        chinese_pattern = re.compile(r'从\s*([^\s到去]+)\s*[到去]\s*([^\s的需要怎么吗？]+)')
        match = chinese_pattern.search(query)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            # Remove common suffixes
            destination = re.sub(r'(的路线|的导航|路线|导航)$', '', destination).strip()
            return (
                EntityExtractor._normalize_city_name(origin),
                EntityExtractor._normalize_city_name(destination)
            )

        # Pattern 3: "X to Y" (simple)
        simple_pattern = re.compile(
            r'([A-Za-z\s]+?)\s+to\s+([A-Za-z\s]+)',
            re.IGNORECASE
        )
        match = simple_pattern.search(query)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            # Filter out routing keywords
            if origin.lower() not in EntityExtractor.ROUTING_KEYWORDS:
                return (
                    EntityExtractor._normalize_city_name(origin),
                    EntityExtractor._normalize_city_name(destination)
                )

        return (None, None)

    @staticmethod
    def extract_entities(query: str, entity_type: str) -> Dict[str, any]:
        """Extract entities based on type

        Args:
            query: User query string
            entity_type: Type of entity ('location', 'stock', 'route')

        Returns:
            Dictionary with extracted entities

        Examples:
            >>> extract_entities("Beijing weather", "location")
            {'location': 'Beijing'}
        """
        if entity_type == "location":
            return {"location": EntityExtractor.extract_location(query)}
        elif entity_type == "stock":
            return {"symbol": EntityExtractor.extract_stock_symbol(query)}
        elif entity_type == "route":
            origin, destination = EntityExtractor.extract_route(query)
            return {"origin": origin, "destination": destination}
        else:
            return {}


# Convenience functions for direct use
def extract_location(query: str) -> str:
    """Extract location from query"""
    return EntityExtractor.extract_location(query)


def extract_stock_symbol(query: str) -> str:
    """Extract stock symbol from query"""
    return EntityExtractor.extract_stock_symbol(query)


def extract_route(query: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract route (origin, destination) from query"""
    return EntityExtractor.extract_route(query)
