"""Configuration management for AI Search Engine"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class LLMConfig(BaseModel):
    """LLM Configuration"""
    # OpenAI Configuration
    openai_enabled: bool = False  # ✅ 添加 enabled 标志
    openai_api_key: str = Field(default_factory=lambda: os.getenv('OPENAI_API_KEY', '') or os.getenv('DASHSCOPE_API_KEY', ''))
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    openai_base_url: str = "https://api.openai.com/v1"
    openai_provider_name: str = "OpenAI"

    # Aliyun DashScope Configuration (compatible with OpenAI format)
    dashscope_enabled: bool = True  # ✅ 添加 enabled 标志
    dashscope_api_key: str = Field(default_factory=lambda: os.getenv('DASHSCOPE_API_KEY', ''))
    dashscope_model: str = "qwen3-max"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Ollama Configuration
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # OpenAI-compatible providers (DeepSeek, local servers, etc.)
    deepseek_enabled: bool = False
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv('DEEPSEEK_API_KEY', ''))
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    local_compatible_enabled: bool = False
    local_compatible_api_key: str = "local-key"
    local_compatible_base_url: str = "http://localhost:8000/v1"
    local_compatible_model: str = "llama-2"

    # Other providers
    google_api_key: str = Field(default_factory=lambda: os.getenv('GOOGLE_API_KEY', ''))

class SearchConfig(BaseModel):
    """Search Configuration"""
    provider: str = "serpapi"
    serpapi_key: str = Field(default_factory=lambda: os.getenv('SERPAPI_API_KEY', ''))
    results_per_query: int = 5
    timeout: int = 10

class ScraperConfig(BaseModel):
    """Web Scraper Configuration"""
    timeout: int = 10
    max_workers: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class CodeExecutionConfig(BaseModel):
    """Code Execution Configuration"""
    timeout: int = 30
    max_output_lines: int = 1000

    # Security configuration (new in 2025-11-04)
    security_level: str = "moderate"  # Options: strict, moderate, permissive
    enable_docker: bool = True  # Use Docker sandbox if available
    enable_validation: bool = True  # Enable AST-based code validation
    memory_limit: str = "256m"  # Docker memory limit
    cpu_limit: float = 1.0  # Docker CPU limit (cores)
    enable_network: bool = False  # Enable network access in sandbox
    python_version: str = "3.11"  # Python version for Docker
    max_output_size: int = 100000  # Maximum output size in bytes

    # Legacy: Allowed imports (deprecated, now controlled by security_level)
    allowed_imports: list = Field(
        default_factory=lambda: [
            "numpy", "pandas", "scipy", "matplotlib",
            "sympy", "math", "statistics"
        ]
    )

class ResearchConfig(BaseModel):
    """Research Agent Configuration"""
    max_queries: int = 5
    top_results_per_query: int = 3
    summary_max_tokens: int = 500

class CacheConfig(BaseModel):
    """Cache Configuration"""
    enabled: bool = True
    ttl_seconds: int = 3600
    backend: str = "sqlite"
    db_path: str = "./cache/search_cache.db"

class CLIConfig(BaseModel):
    """CLI Configuration"""
    theme: str = "monokai"
    verbose: bool = False
    show_sources: bool = True

class RAGChunkingConfig(BaseModel):
    """RAG Chunking Configuration"""
    strategy: str = "semantic"
    chunk_size: int = 512
    chunk_overlap: int = 77
    min_chunk_size: int = 100

class RAGRetrievalConfig(BaseModel):
    """RAG Retrieval Configuration"""
    top_k: int = 10
    similarity_threshold: float = 0.7

class RAGRerankingConfig(BaseModel):
    """RAG Reranking Configuration"""
    enabled: bool = False
    model: str = "BAAI/bge-reranker-large"
    top_k: int = 3

class RAGConfig(BaseModel):
    """RAG Configuration"""
    enabled: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    device: str = "cpu"
    persist_directory: str = "./data/vector_store"
    collection_name: str = "documents"
    chunking: RAGChunkingConfig = Field(default_factory=RAGChunkingConfig)
    retrieval: RAGRetrievalConfig = Field(default_factory=RAGRetrievalConfig)
    reranking: RAGRerankingConfig = Field(default_factory=RAGRerankingConfig)

class WeatherToolConfig(BaseModel):
    """Weather Tool Configuration"""
    enabled: bool = False
    provider: str = "openweathermap"
    api_key: str = Field(default_factory=lambda: os.getenv('OPENWEATHERMAP_API_KEY', ''))
    units: str = "metric"
    language: str = "zh_cn"

class FinanceToolConfig(BaseModel):
    """Finance Tool Configuration"""
    enabled: bool = False
    primary_provider: str = "alpha_vantage"
    alpha_vantage_key: str = Field(default_factory=lambda: os.getenv('ALPHA_VANTAGE_API_KEY', ''))
    fallback_provider: str = "yfinance"
    cache_ttl: int = 300

class RoutingToolConfig(BaseModel):
    """Routing Tool Configuration"""
    enabled: bool = False
    provider: str = "openrouteservice"
    api_key: str = Field(default_factory=lambda: os.getenv('OPENROUTESERVICE_API_KEY', ''))
    default_profile: str = "driving-car"

class DomainToolsConfig(BaseModel):
    """Domain Tools Configuration"""
    weather: WeatherToolConfig = Field(default_factory=WeatherToolConfig)
    finance: FinanceToolConfig = Field(default_factory=FinanceToolConfig)
    routing: RoutingToolConfig = Field(default_factory=RoutingToolConfig)

class OCRConfig(BaseModel):
    """OCR Configuration"""
    enabled: bool = False
    provider: str = "paddleocr"
    languages: list = Field(default_factory=lambda: ["ch", "en"])
    use_gpu: bool = False

class VisionConfig(BaseModel):
    """Vision API Configuration"""
    enabled: bool = False
    provider: str = "gemini"
    model: str = "gemini-2.5-pro"
    api_key: str = Field(default_factory=lambda: os.getenv('GOOGLE_API_KEY', ''))

class MultimodalConfig(BaseModel):
    """Multimodal Configuration"""
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)

class Config(BaseModel):
    """Main Configuration Class"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    code_execution: CodeExecutionConfig = Field(default_factory=CodeExecutionConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    domain_tools: DomainToolsConfig = Field(default_factory=DomainToolsConfig)
    multimodal: MultimodalConfig = Field(default_factory=MultimodalConfig)

def _substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitute environment variable placeholders in config values.
    Supports ${VAR_NAME} syntax.

    Args:
        value: Config value to process (str, dict, list, or other)

    Returns:
        Processed value with env vars substituted
    """
    import re

    if isinstance(value, str):
        # Replace ${VAR_NAME} with environment variable values
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))

        return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)

    elif isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]

    else:
        return value


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file or environment variables"""

    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__),
            '../../config/config.yaml'
        )

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f) or {}
    else:
        config_dict = {}

    # Substitute environment variable placeholders (${VAR_NAME}) in config
    config_dict = _substitute_env_vars(config_dict)

    # Override with environment variables if present (highest priority)
    if os.getenv('OPENAI_API_KEY'):
        config_dict.setdefault('llm', {})['openai_api_key'] = os.getenv('OPENAI_API_KEY')

    if os.getenv('SERPAPI_API_KEY'):
        config_dict.setdefault('search', {})['serpapi_key'] = os.getenv('SERPAPI_API_KEY')

    # 从 YAML 中提取 enabled 标志
    # YAML 结构: llm -> openai -> enabled: false
    llm_config = config_dict.get('llm', {})

    if isinstance(llm_config, dict):
        # 提取 openai enabled 标志
        openai_config = llm_config.get('openai', {})
        if isinstance(openai_config, dict):
            config_dict.setdefault('llm', {})['openai_enabled'] = openai_config.get('enabled', False)

        # 提取 dashscope enabled 标志
        dashscope_config = llm_config.get('dashscope', {})
        if isinstance(dashscope_config, dict):
            config_dict.setdefault('llm', {})['dashscope_enabled'] = dashscope_config.get('enabled', True)

    return Config(**config_dict)

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global config instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
