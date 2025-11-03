"""Workflow Engine - Orchestrates multi-step tasks

Features:
- Execute complex workflows with multiple steps
- Support parallel and sequential execution
- Handle task dependencies
- Error recovery and retry logic
- Progress tracking and callbacks
"""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(Enum):
    """Task execution mode"""
    SEQUENTIAL = "sequential"  # Execute tasks one by one
    PARALLEL = "parallel"  # Execute all tasks simultaneously
    DAG = "dag"  # Execute based on dependency graph


@dataclass
class Task:
    """
    Represents a single task in a workflow

    Attributes:
        id: Unique task identifier
        name: Human-readable task name
        func: Async function to execute
        args: Positional arguments
        kwargs: Keyword arguments
        dependencies: Set of task IDs this task depends on
        retry_count: Number of retries on failure
        timeout: Task timeout in seconds
        on_success: Optional callback on success
        on_failure: Optional callback on failure
    """
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    retry_count: int = 3
    timeout: Optional[float] = None
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None

    # Runtime fields
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attempts: int = 0


@dataclass
class WorkflowResult:
    """
    Workflow execution result

    Attributes:
        success: Whether workflow completed successfully
        results: Dict of task_id -> result
        errors: Dict of task_id -> error
        execution_time: Total execution time in seconds
        task_count: Total number of tasks
        completed_count: Number of completed tasks
        failed_count: Number of failed tasks
    """
    success: bool
    results: Dict[str, Any]
    errors: Dict[str, Exception]
    execution_time: float
    task_count: int
    completed_count: int
    failed_count: int


class WorkflowEngine:
    """
    Orchestrates complex multi-step workflows

    Example:
        engine = WorkflowEngine()
        workflow = engine.create_workflow("research_task")

        # Add tasks
        workflow.add_task("search", search_func, args=("query",))
        workflow.add_task("scrape", scrape_func, dependencies={"search"})
        workflow.add_task("summarize", summarize_func, dependencies={"scrape"})

        # Execute
        result = await engine.execute(workflow)
    """

    def __init__(
        self,
        max_parallel_tasks: int = 5,
        default_timeout: float = 300.0,
    ):
        """
        Initialize Workflow Engine

        Args:
            max_parallel_tasks: Maximum concurrent tasks in parallel mode
            default_timeout: Default task timeout in seconds
        """
        self.max_parallel_tasks = max_parallel_tasks
        self.default_timeout = default_timeout
        self.workflows: Dict[str, "Workflow"] = {}

        logger.info(f"WorkflowEngine initialized (max_parallel={max_parallel_tasks})")

    def create_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        mode: ExecutionMode = ExecutionMode.DAG,
    ) -> "Workflow":
        """
        Create a new workflow

        Args:
            workflow_id: Unique workflow identifier
            name: Human-readable name
            mode: Execution mode

        Returns:
            Workflow instance
        """
        if workflow_id in self.workflows:
            logger.warning(f"Workflow {workflow_id} already exists, returning existing")
            return self.workflows[workflow_id]

        workflow = Workflow(
            id=workflow_id,
            name=name or workflow_id,
            mode=mode,
            engine=self,
        )

        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow: {workflow_id} (mode={mode.value})")

        return workflow

    async def execute(
        self,
        workflow: "Workflow",
        on_progress: Optional[Callable] = None,
    ) -> WorkflowResult:
        """
        Execute a workflow

        Args:
            workflow: Workflow to execute
            on_progress: Optional progress callback (task_id, status, result)

        Returns:
            WorkflowResult
        """
        logger.info(f"Executing workflow: {workflow.id} ({len(workflow.tasks)} tasks)")
        start_time = datetime.now()

        try:
            if workflow.mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(workflow, on_progress)
            elif workflow.mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(workflow, on_progress)
            else:  # DAG
                await self._execute_dag(workflow, on_progress)

            # Collect results
            results = {}
            errors = {}
            completed = 0
            failed = 0

            for task in workflow.tasks.values():
                if task.status == TaskStatus.COMPLETED:
                    results[task.id] = task.result
                    completed += 1
                elif task.status == TaskStatus.FAILED:
                    errors[task.id] = task.error
                    failed += 1

            execution_time = (datetime.now() - start_time).total_seconds()
            success = failed == 0

            logger.info(
                f"Workflow {workflow.id} {'completed' if success else 'failed'}: "
                f"{completed}/{len(workflow.tasks)} tasks completed, "
                f"{failed} failed, {execution_time:.2f}s"
            )

            return WorkflowResult(
                success=success,
                results=results,
                errors=errors,
                execution_time=execution_time,
                task_count=len(workflow.tasks),
                completed_count=completed,
                failed_count=failed,
            )

        except Exception as e:
            logger.error(f"Workflow {workflow.id} execution failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()

            return WorkflowResult(
                success=False,
                results={},
                errors={"workflow": e},
                execution_time=execution_time,
                task_count=len(workflow.tasks),
                completed_count=0,
                failed_count=len(workflow.tasks),
            )

    async def _execute_sequential(
        self,
        workflow: "Workflow",
        on_progress: Optional[Callable] = None,
    ):
        """Execute tasks sequentially"""
        for task in workflow.tasks.values():
            await self._execute_task(task, workflow, on_progress)

            # Stop on first failure (strict mode)
            if task.status == TaskStatus.FAILED:
                logger.warning(f"Sequential execution stopped at failed task: {task.id}")
                break

    async def _execute_parallel(
        self,
        workflow: "Workflow",
        on_progress: Optional[Callable] = None,
    ):
        """Execute tasks in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(self.max_parallel_tasks)

        async def execute_with_semaphore(task: Task):
            async with semaphore:
                await self._execute_task(task, workflow, on_progress)

        tasks = [execute_with_semaphore(task) for task in workflow.tasks.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_dag(
        self,
        workflow: "Workflow",
        on_progress: Optional[Callable] = None,
    ):
        """Execute tasks based on dependency graph (topological order)"""
        # Build dependency graph
        in_degree = {task_id: len(task.dependencies) for task_id, task in workflow.tasks.items()}
        ready_queue = [task_id for task_id, degree in in_degree.items() if degree == 0]

        executing_tasks = set()
        semaphore = asyncio.Semaphore(self.max_parallel_tasks)

        async def execute_with_semaphore(task: Task):
            async with semaphore:
                await self._execute_task(task, workflow, on_progress)

        while ready_queue or executing_tasks:
            # Start ready tasks
            while ready_queue and len(executing_tasks) < self.max_parallel_tasks:
                task_id = ready_queue.pop(0)
                task = workflow.tasks[task_id]

                # Check if dependencies succeeded
                deps_failed = any(
                    workflow.tasks[dep_id].status == TaskStatus.FAILED
                    for dep_id in task.dependencies
                )

                if deps_failed:
                    task.status = TaskStatus.SKIPPED
                    logger.warning(f"Task {task_id} skipped due to failed dependencies")
                    continue

                # Execute task
                task_future = asyncio.create_task(execute_with_semaphore(task))
                executing_tasks.add((task_id, task_future))

            # Wait for at least one task to complete
            if executing_tasks:
                done_tasks = []
                for task_id, future in list(executing_tasks):
                    if future.done():
                        done_tasks.append((task_id, future))

                if not done_tasks:
                    # Wait for any task to complete
                    _, pending = await asyncio.wait(
                        [future for _, future in executing_tasks],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # Find which tasks completed
                    for task_id, future in list(executing_tasks):
                        if future.done():
                            done_tasks.append((task_id, future))

                # Process completed tasks
                for task_id, future in done_tasks:
                    executing_tasks.discard((task_id, future))

                    # Update dependent tasks
                    for dep_task_id, dep_task in workflow.tasks.items():
                        if task_id in dep_task.dependencies:
                            in_degree[dep_task_id] -= 1
                            if in_degree[dep_task_id] == 0:
                                ready_queue.append(dep_task_id)

    async def _execute_task(
        self,
        task: Task,
        workflow: "Workflow",
        on_progress: Optional[Callable] = None,
    ):
        """Execute a single task with retry logic"""
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()

        logger.debug(f"Executing task: {task.id} ({task.name})")

        # Notify progress
        if on_progress:
            try:
                await on_progress(task.id, TaskStatus.RUNNING, None)
            except:
                pass

        # Retry loop
        for attempt in range(1, task.retry_count + 1):
            task.attempts = attempt

            try:
                # Prepare kwargs with results from dependencies
                kwargs = dict(task.kwargs)

                # Inject dependency results
                for dep_id in task.dependencies:
                    dep_task = workflow.tasks.get(dep_id)
                    if dep_task and dep_task.status == TaskStatus.COMPLETED:
                        kwargs[f"{dep_id}_result"] = dep_task.result

                # Execute with timeout
                timeout = task.timeout or self.default_timeout

                result = await asyncio.wait_for(
                    task.func(*task.args, **kwargs),
                    timeout=timeout,
                )

                # Success
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.end_time = datetime.now()

                logger.debug(f"Task {task.id} completed successfully")

                # Notify progress
                if on_progress:
                    try:
                        await on_progress(task.id, TaskStatus.COMPLETED, result)
                    except:
                        pass

                # Success callback
                if task.on_success:
                    try:
                        await task.on_success(result)
                    except:
                        pass

                return

            except asyncio.TimeoutError as e:
                logger.warning(f"Task {task.id} timed out (attempt {attempt}/{task.retry_count})")
                task.error = e

                if attempt >= task.retry_count:
                    break

                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.warning(f"Task {task.id} failed: {e} (attempt {attempt}/{task.retry_count})")
                task.error = e

                if attempt >= task.retry_count:
                    break

                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

        # All retries exhausted - mark as failed
        task.status = TaskStatus.FAILED
        task.end_time = datetime.now()

        logger.error(f"Task {task.id} failed after {task.attempts} attempts")

        # Notify progress
        if on_progress:
            try:
                await on_progress(task.id, TaskStatus.FAILED, task.error)
            except:
                pass

        # Failure callback
        if task.on_failure:
            try:
                await task.on_failure(task.error)
            except:
                pass


class Workflow:
    """
    Represents a workflow (collection of tasks)

    Methods:
        add_task: Add a task to the workflow
        remove_task: Remove a task
        get_task: Get task by ID
        validate: Validate workflow (check for cycles, etc.)
    """

    def __init__(
        self,
        id: str,
        name: str,
        mode: ExecutionMode,
        engine: WorkflowEngine,
    ):
        """
        Initialize workflow

        Args:
            id: Workflow ID
            name: Workflow name
            mode: Execution mode
            engine: Parent workflow engine
        """
        self.id = id
        self.name = name
        self.mode = mode
        self.engine = engine
        self.tasks: Dict[str, Task] = {}

    def add_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        func: Optional[Callable] = None,
        args: tuple = (),
        kwargs: dict = None,
        dependencies: Set[str] = None,
        retry_count: int = 3,
        timeout: Optional[float] = None,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
    ) -> Task:
        """
        Add a task to the workflow

        Args:
            task_id: Unique task ID
            name: Task name
            func: Async function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            dependencies: Set of task IDs this depends on
            retry_count: Number of retries
            timeout: Task timeout
            on_success: Success callback
            on_failure: Failure callback

        Returns:
            Created Task
        """
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists in workflow {self.id}")

        task = Task(
            id=task_id,
            name=name or task_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            dependencies=dependencies or set(),
            retry_count=retry_count,
            timeout=timeout,
            on_success=on_success,
            on_failure=on_failure,
        )

        self.tasks[task_id] = task
        logger.debug(f"Added task {task_id} to workflow {self.id}")

        return task

    def remove_task(self, task_id: str):
        """Remove a task from workflow"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.debug(f"Removed task {task_id} from workflow {self.id}")

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def validate(self) -> bool:
        """
        Validate workflow

        Checks:
        - All dependencies exist
        - No circular dependencies (for DAG mode)

        Returns:
            True if valid, raises ValueError otherwise
        """
        # Check all dependencies exist
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    raise ValueError(
                        f"Task {task.id} depends on non-existent task {dep_id}"
                    )

        # Check for cycles (DAG mode only)
        if self.mode == ExecutionMode.DAG:
            if self._has_cycle():
                raise ValueError(f"Workflow {self.id} contains circular dependencies")

        return True

    def _has_cycle(self) -> bool:
        """Check for circular dependencies using DFS"""
        visited = set()
        rec_stack = set()

        def dfs(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            task = self.tasks[task_id]
            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False

    async def execute(
        self,
        on_progress: Optional[Callable] = None,
    ) -> WorkflowResult:
        """Execute this workflow"""
        return await self.engine.execute(self, on_progress)
