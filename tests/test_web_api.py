"""Web API endpoint tests - consolidated from test_basic_functions.py and test_web_ui.py"""

import pytest
import aiohttp


@pytest.mark.api
@pytest.mark.asyncio
class TestWebAPI:
    """Test Web UI API endpoints"""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    async def session(self):
        """Create aiohttp session for tests"""
        async with aiohttp.ClientSession() as session:
            yield session

    async def test_health_check(self, session):
        """Test health check endpoint"""
        async with session.get(f"{self.BASE_URL}/health") as response:
            assert response.status == 200
            data = await response.json()
            assert "status" in data or isinstance(data, dict)

    async def test_homepage_loads(self, session):
        """Test homepage loads successfully"""
        async with session.get(f"{self.BASE_URL}/") as response:
            assert response.status == 200
            html = await response.text()
            assert "AI Search Engine" in html
            assert len(html) > 0

    async def test_css_loads(self, session):
        """Test CSS stylesheet loads"""
        async with session.get(f"{self.BASE_URL}/static/css/new-style.css") as response:
            assert response.status == 200
            css = await response.text()
            assert len(css) > 0

    async def test_javascript_loads(self, session):
        """Test JavaScript loads"""
        async with session.get(f"{self.BASE_URL}/static/js/main.js") as response:
            assert response.status == 200
            js = await response.text()
            assert len(js) > 0

    @pytest.mark.parametrize("query,expected_type", [
        ("What is machine learning?", "RESEARCH"),
        ("Calculate 25% of 480", "CODE"),
        ("Tell me a joke", "CHAT"),
        ("今天北京天气怎么样", "WEATHER"),
    ])
    async def test_query_classification(self, session, query, expected_type):
        """Test query classification endpoint"""
        async with session.post(
            f"{self.BASE_URL}/classify",
            data={"query": query}
        ) as response:
            assert response.status == 200
            result = await response.text()
            assert expected_type.lower() in result.lower()

    async def test_rag_page_loads(self, session):
        """Test RAG page loads"""
        async with session.get(f"{self.BASE_URL}/rag") as response:
            assert response.status == 200
            html = await response.text()
            assert "Document Q&A" in html or "RAG" in html

    async def test_history_page_loads(self, session):
        """Test history page loads"""
        async with session.get(f"{self.BASE_URL}/history/") as response:
            assert response.status == 200
            html = await response.text()
            assert "History" in html or "历史" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
