"""Main CLI Application"""

import asyncio
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from src.agents import ChatAgent, CodeAgent, ResearchAgent
from src.llm import LLMManager
from src.router import Router, TaskType
from src.tools import CodeExecutor, ScraperTool, SearchTool
from src.utils import get_config, get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(help="AI Search Engine - Research and Code Execution")

# Global instances
config = get_config()
llm_manager = LLMManager(config=config)
search_tool = SearchTool(
    provider=config.search.provider,
    api_key=config.search.serpapi_key,
)
scraper_tool = ScraperTool(
    timeout=config.scraper.timeout,
    max_workers=config.scraper.max_workers,
    user_agent=config.scraper.user_agent,
)
code_executor = CodeExecutor(
    timeout=config.code_execution.timeout,
    max_output_lines=config.code_execution.max_output_lines,
)

research_agent = ResearchAgent(
    llm_manager=llm_manager,
    search_tool=search_tool,
    scraper_tool=scraper_tool,
    config=config,
)
code_agent = CodeAgent(
    llm_manager=llm_manager,
    code_executor=code_executor,
    config=config,
)
chat_agent = ChatAgent(llm_manager=llm_manager, config=config)


@app.command()
def search(
    query: str = typer.Argument(..., help="Research query"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output", is_flag=True),
):
    """Conduct web research on a topic"""

    if not config.search.serpapi_key:
        console.print(
            "[red]Error: SERPAPI_API_KEY not configured. "
            "Set it in config/config.yaml or environment variables.[/red]"
        )
        raise typer.Exit(1)

    console.print(Panel(f"[cyan]Researching: {query}[/cyan]", expand=False))

    try:
        result = asyncio.run(research_agent.research(query, show_progress=True))

        # Display results
        console.print(Panel("[green]Research Complete[/green]", expand=False))

        # Sources
        console.print("\n[bold cyan]Sources:[/bold cyan]")
        for i, source in enumerate(result["sources"], 1):
            console.print(f"[yellow]{i}.[/yellow] {source['title']}")
            console.print(f"   {source['url']}")

        # Summary
        console.print(f"\n[bold cyan]Summary:[/bold cyan]")
        console.print(result["summary"])

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def solve(
    problem: str = typer.Argument(..., help="Math problem or question"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output", is_flag=True),
):
    """Solve a math problem or execute code"""

    console.print(Panel(f"[cyan]Solving: {problem}[/cyan]", expand=False))

    try:
        result = asyncio.run(code_agent.solve(problem, show_progress=True))

        if result["success"]:
            console.print(Panel("[green]Solution Complete[/green]", expand=False))

            console.print(f"\n[bold cyan]Output:[/bold cyan]")
            console.print(result["output"])
        else:
            console.print(Panel("[red]Execution Failed[/red]", expand=False))
            console.print(f"\n[bold red]Error:[/bold red]")
            console.print(result["error"])

        # Explanation
        console.print(f"\n[bold cyan]Explanation:[/bold cyan]")
        console.print(result["explanation"])

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def ask(
    query: str = typer.Argument(..., help="Question to ask"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-detect task type"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    use_llm: bool = typer.Option(True, "--llm/--no-llm", help="Use LLM for classification (default: True)"),
):
    """Ask a question (auto-routes to appropriate agent)"""

    if auto:
        # Use hybrid classification: keyword-based for fast cases, LLM for uncertain ones
        if use_llm:
            task_type, confidence, method = asyncio.run(
                Router.classify_hybrid(query, llm_manager, use_llm_threshold=0.6)
            )
        else:
            # Keyword-based only
            task_type = Router.classify(query)
            confidence = Router.get_confidence(query, task_type)
            method = "keyword"

        if verbose:
            console.print(
                f"[yellow]Detected: {task_type.value} (confidence: {confidence:.1%}, method: {method})[/yellow]"
            )

        if task_type == TaskType.RESEARCH:
            console.print(Panel("[cyan]Research Mode[/cyan]", expand=False))
            if not config.search.serpapi_key:
                console.print(
                    "[yellow]Warning: Research mode requires SERPAPI_API_KEY[/yellow]"
                )
            try:
                result = asyncio.run(research_agent.research(query, show_progress=True))
                console.print("\n[bold cyan]Summary:[/bold cyan]")
                console.print(result["summary"])
            except Exception as e:
                console.print(f"[red]Research failed: {e}[/red]")

        elif task_type == TaskType.CODE:
            console.print(Panel("[cyan]Code Execution Mode[/cyan]", expand=False))
            try:
                result = asyncio.run(code_agent.solve(query, show_progress=True))
                if result["success"]:
                    console.print(f"\n[bold cyan]Explanation:[/bold cyan]")
                    console.print(result["explanation"])
                else:
                    console.print(f"\n[bold red]Error:[/bold red]")
                    console.print(result["error"])
            except Exception as e:
                console.print(f"[red]Code execution failed: {e}[/red]")

        else:
            console.print(Panel("[cyan]Chat Mode[/cyan]", expand=False))
            try:
                response = asyncio.run(chat_agent.chat(query))
                console.print(f"\n[cyan]{response}[/cyan]")
            except Exception as e:
                console.print(f"[red]Chat failed: {e}[/red]")

    else:
        # Default chat mode
        try:
            response = asyncio.run(chat_agent.chat(query))
            console.print(f"\n[cyan]{response}[/cyan]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                import traceback
                traceback.print_exc()
            raise typer.Exit(1)


@app.command()
def chat(verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output", is_flag=True)):
    """Enter interactive chat mode"""

    console.print(Panel("[cyan]AI Search Engine - Chat Mode[/cyan]", expand=False))
    console.print("[yellow]Type 'exit' or 'quit' to exit, 'clear' to clear history[/yellow]\n")

    chat_agent.clear_history()

    while True:
        try:
            user_input = console.input("[green]You:[/green] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if user_input.lower() == "clear":
                chat_agent.clear_history()
                console.print("[yellow]Chat history cleared[/yellow]\n")
                continue

            response = asyncio.run(chat_agent.chat(user_input))
            console.print(f"[cyan]Assistant:[/cyan] {response}\n")

        except KeyboardInterrupt:
            console.print("[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if verbose:
                import traceback
                traceback.print_exc()


@app.command()
def info():
    """Show system information"""

    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    # Check LLM providers
    for provider_name in llm_manager.list_providers():
        table.add_row(f"LLM: {provider_name}", "✓ Configured")

    # Check search API
    if config.search.serpapi_key:
        table.add_row("Search API", "✓ Configured")
    else:
        table.add_row("Search API", "✗ Not configured")

    console.print(table)

    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Config file: config/config.yaml")
    console.print(f"  LLM providers: {', '.join(llm_manager.list_providers())}")
    console.print(f"  Search provider: {config.search.provider}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to config file"
    ),
):
    """AI Search Engine - Research, code execution, and chat powered by LLMs"""
    if ctx.invoked_subcommand is None:
        console.print("[cyan]AI Search Engine[/cyan]")
        console.print("Use --help to see available commands")


if __name__ == "__main__":
    app()
