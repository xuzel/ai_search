"""Workflow Router - Multi-step task orchestration and execution"""

import asyncio
import json
from typing import Dict, Optional
from fastapi import APIRouter, Request, Form, WebSocket
from fastapi.responses import HTMLResponse
import uuid

from src.workflow import WorkflowEngine, TaskDecomposer, ResultAggregator
from src.llm import LLMManager
from src.agents import ResearchAgent, CodeAgent, ChatAgent
from src.tools import SearchTool, CodeExecutor, ScraperTool
from src.utils import get_config, get_logger
from src.web import database

logger = get_logger(__name__)

router = APIRouter()

# Global instances (initialized once)
workflow_engine = None
task_decomposer = None
result_aggregator = None
research_agent = None
code_agent = None
chat_agent = None

# Active workflows tracking
active_workflows: Dict[str, Dict] = {}


async def initialize_workflow_engine():
    """Initialize workflow engine and related components"""
    global config, llm_manager, workflow_engine, task_decomposer, result_aggregator
    global research_agent, code_agent, chat_agent

    if workflow_engine is None:
        config = get_config()
        llm_manager = LLMManager(config=config)

        # Initialize workflow components
        workflow_engine = WorkflowEngine(
            max_parallel_tasks=5,
            default_timeout=300.0
        )
        task_decomposer = TaskDecomposer(llm_manager=llm_manager)
        result_aggregator = ResultAggregator(llm_manager=llm_manager)

        # Initialize agents for use in workflow tasks
        search_tool = SearchTool(api_key=config.search.serpapi_key)
        scraper_tool = ScraperTool()
        code_executor = CodeExecutor(timeout=config.code_execution.timeout)

        research_agent = ResearchAgent(
            llm_manager=llm_manager,
            search_tool=search_tool,
            scraper_tool=scraper_tool,
            config=config
        )
        code_agent = CodeAgent(
            llm_manager=llm_manager,
            code_executor=code_executor,
            config=config
        )
        chat_agent = ChatAgent(llm_manager=llm_manager)

        logger.info("Workflow engine initialized successfully")


@router.post("/workflow/plan", response_class=HTMLResponse)
async def plan_workflow(request: Request, query: str = Form(...)):
    """
    Decompose a query into a workflow plan without executing it
    Shows the user the planned tasks before execution
    """
    await initialize_workflow_engine()

    request.app.state.templates

    try:
        logger.info(f"Planning workflow for query: {query}")

        # Decompose query into subtasks
        plan = await task_decomposer.decompose(query)

        logger.info(f"Generated plan with {len(plan.subtasks)} subtasks")

        # Convert to JSON-serializable format
        subtasks_data = [
            {
                "id": task.id,
                "description": task.description,
                "tool": task.tool,
                "query": task.query,
                "dependencies": task.dependencies,
                "output_variable": task.output_variable,
            }
            for task in plan.subtasks
        ]

        return f"""
        <div class="workflow-plan" id="workflowPlan">
            <div class="plan-header">
                <h3>Task Plan</h3>
                <p class="plan-goal">{plan.goal}</p>
            </div>

            <div class="plan-info">
                <div class="info-item">
                    <span class="label">Complexity:</span>
                    <span class="value">{plan.complexity}</span>
                </div>
                <div class="info-item">
                    <span class="label">Estimated Steps:</span>
                    <span class="value">{plan.estimated_steps}</span>
                </div>
                <div class="info-item">
                    <span class="label">Subtasks:</span>
                    <span class="value">{len(plan.subtasks)}</span>
                </div>
            </div>

            <div class="subtasks-list">
                <h4>Tasks:</h4>
                {''.join([
                    f'''
                    <div class="subtask-item" data-task-id="{task['id']}">
                        <div class="task-header">
                            <span class="task-id">Task {subtasks_data.index(task) + 1}</span>
                            <span class="tool-badge">{task['tool']}</span>
                        </div>
                        <p class="task-description">{task['description']}</p>
                        <details class="task-details">
                            <summary>Details</summary>
                            <div class="details-content">
                                <p><strong>Query:</strong> {task['query']}</p>
                                {f'<p><strong>Dependencies:</strong> {", ".join(task["dependencies"])}</p>' if task['dependencies'] else ''}
                                <p><strong>Output Variable:</strong> {task['output_variable']}</p>
                            </div>
                        </details>
                    </div>
                    '''
                    for task in subtasks_data
                ])}
            </div>

            <div class="plan-actions">
                <button class="btn btn-primary" hx-post="/workflow/execute"
                        hx-vals='{{"query": "{query}", "plan": "{json.dumps(subtasks_data).replace('"', '&quot;')}"}}'
                        hx-target="#result" hx-swap="innerHTML">
                    Execute Workflow
                </button>
            </div>
        </div>
        """

    except Exception as e:
        logger.error(f"Error planning workflow: {e}", exc_info=True)
        return f"""
        <div class="alert alert-danger">
            <h4>Error Planning Workflow</h4>
            <p>{str(e)}</p>
        </div>
        """


@router.post("/workflow/execute", response_class=HTMLResponse)
async def execute_workflow(request: Request, query: str = Form(...), plan: Optional[str] = Form(None)):
    """
    Execute a workflow with real-time progress tracking
    """
    await initialize_workflow_engine()

    request.app.state.templates
    workflow_id = str(uuid.uuid4())[:8]

    try:
        logger.info(f"Executing workflow {workflow_id} for query: {query}")

        # Track workflow
        active_workflows[workflow_id] = {
            "query": query,
            "status": "running",
            "progress": 0,
            "tasks": {},
            "results": {},
        }

        # Parse plan if provided, otherwise decompose
        if plan:
            subtasks_data = json.loads(plan)
        else:
            task_plan = await task_decomposer.decompose(query)
            subtasks_data = [
                {
                    "id": task.id,
                    "description": task.description,
                    "tool": task.tool,
                    "query": task.query,
                    "dependencies": task.dependencies,
                    "output_variable": task.output_variable,
                }
                for task in task_plan.subtasks
            ]

        # Create workflow
        workflow = workflow_engine.create_workflow(
            workflow_id=workflow_id,
            name=f"Query: {query[:50]}..."
        )

        # Progress callback
        async def on_progress(task_id: str, status: str, result: any = None):
            """Track task progress"""
            if workflow_id in active_workflows:
                active_workflows[workflow_id]["tasks"][task_id] = {
                    "status": status,
                    "result": result
                }

        # Add tasks to workflow
        for subtask in subtasks_data:
            # Create task executor based on tool type
            if subtask["tool"] == "search":
                task_func = research_agent.research
            elif subtask["tool"] == "code":
                task_func = code_agent.solve
            elif subtask["tool"] == "chat":
                task_func = chat_agent.chat
            else:
                # Fallback to chat for unknown tools
                task_func = chat_agent.chat

            # Add task with dependencies
            workflow.add_task(
                task_id=subtask["id"],
                func=task_func,
                args=(subtask["query"],),
                dependencies=set(subtask.get("dependencies", [])),
                name=subtask["description"]
            )

        # Execute workflow
        result = await workflow_engine.execute(workflow, on_progress=on_progress)

        # Aggregate results
        aggregated = await result_aggregator.aggregate(
            results=result.results,
            original_query=query
        )

        active_workflows[workflow_id]["status"] = "completed"
        active_workflows[workflow_id]["results"] = aggregated

        # Save to history
        await database.save_conversation(
            mode="workflow",
            query=query,
            response=aggregated.get("summary", ""),
            metadata=json.dumps({
                "workflow_id": workflow_id,
                "task_count": result.task_count,
                "completed_count": result.completed_count,
                "failed_count": result.failed_count,
                "execution_time": result.execution_time,
            })
        )

        # Render results
        return f"""
        <div class="workflow-result">
            <div class="result-header">
                <h3>Workflow Results</h3>
                <div class="result-stats">
                    <span class="stat">Tasks: {result.task_count}</span>
                    <span class="stat">Completed: {result.completed_count}</span>
                    <span class="stat">Failed: {result.failed_count}</span>
                    <span class="stat">Time: {result.execution_time:.2f}s</span>
                </div>
            </div>

            <div class="result-content">
                <h4>Summary</h4>
                <div class="summary-text">
                    {aggregated.get('summary', 'No summary available')}
                </div>

                {f'''
                <h4>Key Insights</h4>
                <div class="insights">
                    {chr(10).join([f'<p>• {insight}</p>' for insight in aggregated.get('key_insights', [])])}
                </div>
                ''' if aggregated.get('key_insights') else ''}

                {f'''
                <h4>Sources</h4>
                <div class="sources-list">
                    {chr(10).join([
                        f'<div class="source-item"><a href="{s.get("url", "#")}" target="_blank">{s.get("title", "Source")}</a></div>'
                        for s in aggregated.get('sources', [])[:5]
                    ])}
                </div>
                ''' if aggregated.get('sources') else ''}
            </div>

            <div class="result-actions">
                <button class="btn btn-secondary" onclick="location.reload()">
                    New Query
                </button>
            </div>
        </div>
        """

    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}", exc_info=True)
        active_workflows[workflow_id]["status"] = "failed"
        return f"""
        <div class="alert alert-danger">
            <h4>Workflow Execution Error</h4>
            <p>{str(e)}</p>
        </div>
        """


@router.websocket("/ws/workflow/{workflow_id}")
async def websocket_workflow_progress(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time workflow progress updates
    """
    await websocket.accept()

    try:
        while workflow_id in active_workflows:
            workflow_data = active_workflows[workflow_id]

            # Send progress update
            await websocket.send_json({
                "workflow_id": workflow_id,
                "status": workflow_data.get("status"),
                "tasks": workflow_data.get("tasks", {}),
                "progress": len([t for t in workflow_data.get("tasks", {}).values()
                               if t.get("status") == "completed"]) / max(1, len(workflow_data.get("tasks", {}))),
            })

            # Check if workflow is complete
            if workflow_data.get("status") in ["completed", "failed"]:
                break

            # Wait before next update
            await asyncio.sleep(1)

        # Send final update
        final_data = active_workflows.get(workflow_id, {})
        await websocket.send_json({
            "workflow_id": workflow_id,
            "status": final_data.get("status"),
            "completed": True,
            "results": final_data.get("results", {}),
        })

    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        # Cleanup after 1 hour
        if workflow_id in active_workflows:
            # Could implement TTL here
            pass
