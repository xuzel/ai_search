"""Basic usage examples for AI Search Engine"""

import asyncio
import os

from src.agents import ChatAgent, CodeAgent, ResearchAgent
from src.llm import LLMManager
from src.tools import CodeExecutor, ScraperTool, SearchTool
from src.utils import get_config, get_logger

logger = get_logger(__name__)


async def example_code_execution():
    """Example: Code execution for math problems"""
    print("\n" + "="*50)
    print("Example 1: Code Execution - Math Problem")
    print("="*50)

    config = get_config()
    llm_manager = LLMManager(config=config)
    code_executor = CodeExecutor()
    code_agent = CodeAgent(llm_manager, code_executor, config)

    problem = "Calculate the sum of all prime numbers less than 100"
    print(f"Problem: {problem}\n")

    result = await code_agent.solve(problem, show_progress=True)

    print(f"\nResult: {result['success']}")
    print(f"Output:\n{result['output']}")
    print(f"\nExplanation:\n{result['explanation']}")


async def example_chat():
    """Example: Simple chat interaction"""
    print("\n" + "="*50)
    print("Example 2: Chat - Conversation")
    print("="*50)

    config = get_config()
    llm_manager = LLMManager(config=config)
    chat_agent = ChatAgent(llm_manager, config)

    message = "What is machine learning?"
    print(f"User: {message}\n")

    response = await chat_agent.chat(message)
    print(f"Assistant: {response}")


async def example_code_with_matplotlib():
    """Example: Code execution with data visualization"""
    print("\n" + "="*50)
    print("Example 3: Code with Plot")
    print("="*50)

    config = get_config()
    llm_manager = LLMManager(config=config)
    code_executor = CodeExecutor()
    code_agent = CodeAgent(llm_manager, code_executor, config)

    problem = """
    Generate data for a sine wave and print some statistics:
    - Generate 100 points for x from 0 to 2π
    - Calculate y = sin(x)
    - Print max, min, and average values
    """
    print(f"Problem: {problem}\n")

    result = await code_agent.solve(problem, show_progress=True)

    if result['success']:
        print(f"\nOutput:\n{result['output']}")
    else:
        print(f"\nError:\n{result['error']}")


async def example_symbolic_math():
    """Example: Symbolic math with SymPy"""
    print("\n" + "="*50)
    print("Example 4: Symbolic Math - Solve Equation")
    print("="*50)

    config = get_config()
    llm_manager = LLMManager(config=config)
    code_executor = CodeExecutor()
    code_agent = CodeAgent(llm_manager, code_executor, config)

    problem = "Solve the equation: x^3 - 3x^2 + 2x = 0"
    print(f"Problem: {problem}\n")

    result = await code_agent.solve(problem, show_progress=True)

    print(f"\nOutput:\n{result['output']}")
    print(f"\nExplanation:\n{result['explanation']}")


async def example_data_analysis():
    """Example: Data analysis with pandas"""
    print("\n" + "="*50)
    print("Example 5: Data Analysis with Pandas")
    print("="*50)

    config = get_config()
    llm_manager = LLMManager(config=config)
    code_executor = CodeExecutor()
    code_agent = CodeAgent(llm_manager, code_executor, config)

    problem = """
    Create a dataset with 100 random numbers and calculate:
    - Mean and standard deviation
    - Quartiles (Q1, Q2, Q3)
    - Identify outliers (values beyond 3 std deviations)
    """
    print(f"Problem: {problem}\n")

    result = await code_agent.solve(problem, show_progress=True)

    if result['success']:
        print(f"\nOutput:\n{result['output']}")


async def example_research(query: str = "Latest developments in artificial intelligence"):
    """Example: Web research"""
    print("\n" + "="*50)
    print(f"Example 6: Research - {query}")
    print("="*50)

    config = get_config()

    if not config.search.serpapi_key:
        print("\n⚠️  SERPAPI_API_KEY not configured. Skipping research example.")
        print("To use this example, set SERPAPI_API_KEY in config/config.yaml or .env")
        return

    llm_manager = LLMManager(config=config)
    search_tool = SearchTool(
        provider=config.search.provider,
        api_key=config.search.serpapi_key,
    )
    scraper_tool = ScraperTool()
    research_agent = ResearchAgent(
        llm_manager, search_tool, scraper_tool, config
    )

    print(f"Researching: {query}\n")

    result = await research_agent.research(query, show_progress=True)

    print(f"\n\nSources:")
    for source in result['sources']:
        print(f"  - {source['title']}")
        print(f"    {source['url']}")

    print(f"\n\nSummary:\n{result['summary']}")


async def main():
    """Run all examples"""
    print("="*50)
    print("AI Search Engine - Examples")
    print("="*50)

    # Run examples
    await example_chat()
    await example_code_execution()
    await example_code_with_matplotlib()
    await example_symbolic_math()
    await example_data_analysis()

    # Uncomment to run research example (requires SERPAPI_API_KEY)
    # await example_research()

    print("\n" + "="*50)
    print("Examples completed!")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
