"""Main CLI Application - Refactored with New Routing System

This version uses the unified routing system instead of the old Router class.
"""

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from src.agents import ChatAgent, CodeAgent, ResearchAgent
from src.llm import LLMManager
from src.routing import create_router, TaskType  # ✅ New routing system
from src.tools import CodeExecutor, ScraperTool, SearchTool
from src.tools.code_validator import SecurityLevel
from src.utils import get_config, get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(help="AI Search Engine - Research and Code Execution")

# Initialize once (still global for CLI, but using new components)
config = get_config()
llm_manager = LLMManager(config=config)

# ✅ Use new unified router
router = create_router(
    config=config,
    llm_manager=llm_manager,
    router_type='hybrid'  # Uses keyword + LLM fallback
)

# Initialize tools
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
    security_level=SecurityLevel(config.code_execution.security_level),
    enable_docker=config.code_execution.enable_docker,
    enable_validation=config.code_execution.enable_validation,
    memory_limit=config.code_execution.memory_limit,
)

# Initialize agents
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
    problem: str = typer.Argument(..., help="Problem to solve with code"),
    show_code: bool = typer.Option(True, "--show-code/--no-code", help="Show generated code"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output", is_flag=True),
):
    """Solve a problem using code execution"""

    console.print(Panel(f"[cyan]Solving: {problem}[/cyan]", expand=False))

    try:
        result = asyncio.run(code_agent.solve(problem))

        if result["success"]:
            console.print(Panel("[green]Solution Found[/green]", expand=False))

            if show_code and result.get("code"):
                console.print("\n[bold cyan]Generated Code:[/bold cyan]")
                syntax = Syntax(result["code"], "python", theme="monokai", line_numbers=True)
                console.print(syntax)

            if result.get("output"):
                console.print("\n[bold cyan]Output:[/bold cyan]")
                console.print(result["output"])

            if result.get("explanation"):
                console.print("\n[bold cyan]Explanation:[/bold cyan]")
                console.print(result["explanation"])
        else:
            console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def ask(
    query: str = typer.Argument(..., help="Question or query"),
    auto: bool = typer.Option(True, "--auto/--manual", help="Auto-route to appropriate agent"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output", is_flag=True),
):
    """Ask a question and auto-route to the appropriate agent

    ✨ This command uses the new unified routing system!
    """

    console.print(Panel(f"[cyan]Query: {query}[/cyan]", expand=False))

    try:
        if auto:
            # ✅ Use new routing system
            console.print("[dim]Routing query...[/dim]")
            decision = asyncio.run(router.route(query))

            task_type = decision.primary_task_type
            confidence = decision.task_confidence

            console.print(
                f"[dim]Routed to: {task_type.value} "
                f"(confidence: {confidence:.2f})[/dim]"
            )
            console.print(f"[dim]Reasoning: {decision.reasoning}[/dim]\n")

            # Execute based on task type
            if task_type == TaskType.RESEARCH:
                asyncio.run(_execute_research(query))
            elif task_type == TaskType.CODE:
                asyncio.run(_execute_code(query))
            elif task_type == TaskType.CHAT:
                asyncio.run(_execute_chat(query))
            else:
                # Default to chat
                asyncio.run(_execute_chat(query))
        else:
            # Manual mode: just chat
            asyncio.run(_execute_chat(query))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)


async def _execute_research(query: str):
    """Execute research task"""
    result = await research_agent.research(query, show_progress=True)
    console.print("\n[bold cyan]Summary:[/bold cyan]")
    console.print(result["summary"])


async def _execute_code(query: str):
    """Execute code task"""
    result = await code_agent.solve(query)
    if result["success"]:
        if result.get("output"):
            console.print("\n[bold cyan]Output:[/bold cyan]")
            console.print(result["output"])
    else:
        console.print(f"[red]Error: {result.get('error')}[/red]")


async def _execute_chat(query: str):
    """Execute chat task"""
    result = await chat_agent.chat(query)
    console.print(f"\n{result.get('message', result.get('answer', 'No response'))}")


@app.command()
def chat():
    """Start interactive chat session"""

    console.print(Panel("[cyan]Interactive Chat Mode[/cyan]", expand=False))
    console.print("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")

    while True:
        try:
            query = console.input("[bold green]You:[/bold green] ")

            if query.lower() in ["exit", "quit", "q"]:
                console.print("\n[cyan]Goodbye![/cyan]")
                break

            if not query.strip():
                continue

            result = asyncio.run(chat_agent.chat(query))
            console.print(
                f"[bold blue]AI:[/bold blue] {result.get('message', result.get('answer', 'No response'))}\n"
            )

        except KeyboardInterrupt:
            console.print("\n[cyan]Goodbye![/cyan]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue


@app.command()
def info():
    """Show system information"""

    table = Table(title="AI Search Engine - System Info")

    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    # LLM providers
    providers = llm_manager.list_providers()
    table.add_row(
        "LLM Providers",
        "✓ Available",
        f"{len(providers)} provider(s): {', '.join(providers)}"
    )

    # ✅ Router info
    table.add_row(
        "Router",
        "✓ Unified",
        f"{router.name} (keyword + LLM hybrid)"
    )

    # Search tool
    search_status = "✓ Ready" if config.search.serpapi_key else "✗ Not configured"
    table.add_row(
        "Search Tool",
        search_status,
        f"Provider: {config.search.provider}"
    )

    # Code executor
    security_info = code_executor.get_security_info()
    docker_status = "✓ Enabled" if security_info['docker_available'] else "✗ Disabled"
    table.add_row(
        "Code Executor",
        docker_status,
        f"Security: {security_info['security_level']}"
    )

    console.print(table)


if __name__ == "__main__":
    app()
