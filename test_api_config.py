"""Test API Configuration Loading"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import get_config

def test_config():
    """Test if API keys are loaded correctly"""
    print("=" * 60)
    print("API Configuration Test")
    print("=" * 60)

    config = get_config()

    # Test Domain Tools
    print("\n🛠️  Domain Tools Configuration:")
    print(f"  Weather:")
    print(f"    - Enabled: {config.domain_tools.weather.enabled}")
    print(f"    - API Key: {'✅ Configured' if config.domain_tools.weather.api_key else '❌ Not configured'}")
    print(f"    - Key preview: {config.domain_tools.weather.api_key[:20]}..." if config.domain_tools.weather.api_key else "")

    print(f"  Finance:")
    print(f"    - Enabled: {config.domain_tools.finance.enabled}")
    print(f"    - API Key: {'✅ Configured' if config.domain_tools.finance.alpha_vantage_key else '❌ Not configured'}")
    print(f"    - Key preview: {config.domain_tools.finance.alpha_vantage_key[:20]}..." if config.domain_tools.finance.alpha_vantage_key else "")

    print(f"  Routing:")
    print(f"    - Enabled: {config.domain_tools.routing.enabled}")
    print(f"    - API Key: {'✅ Configured' if config.domain_tools.routing.api_key else '❌ Not configured'}")
    print(f"    - Key preview: {config.domain_tools.routing.api_key[:20]}..." if config.domain_tools.routing.api_key else "")

    # Test Multimodal
    print("\n🖼️  Multimodal Configuration:")
    print(f"  OCR:")
    print(f"    - Enabled: {config.multimodal.ocr.enabled}")

    print(f"  Vision:")
    print(f"    - Enabled: {config.multimodal.vision.enabled}")
    print(f"    - Google API Key: {'✅ Configured' if config.multimodal.vision.api_key else '❌ Not configured'}")
    print(f"    - Key preview: {config.multimodal.vision.api_key[:20]}..." if config.multimodal.vision.api_key else "")

    # Test LLM
    print("\n🤖 LLM Configuration:")
    print(f"  DashScope:")
    print(f"    - Enabled: {config.llm.dashscope_enabled}")
    print(f"    - API Key: {'✅ Configured' if config.llm.dashscope_api_key else '❌ Not configured'}")

    print(f"  OpenAI:")
    print(f"    - Enabled: {config.llm.openai_enabled}")
    print(f"    - API Key: {'✅ Configured' if config.llm.openai_api_key else '❌ Not configured'}")

    # Test Search
    print("\n🔍 Search Configuration:")
    print(f"  SerpAPI:")
    print(f"    - API Key: {'✅ Configured' if config.search.serpapi_key else '❌ Not configured'}")
    print(f"    - Key preview: {config.search.serpapi_key[:20]}..." if config.search.serpapi_key else "")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_config()
