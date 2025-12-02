"""Task Tracker - Tracks execution progress and provides status updates

Provides real-time visibility into workflow execution including:
- Progress tracking for multi-step tasks
- Status updates and notifications
- Execution history and statistics
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskProgress:
    """Progress information for a task"""
    task_id: str
    task_name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at is None:
            return None
        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowProgress:
    """Progress information for an entire workflow"""
    workflow_id: str
    workflow_name: str
    tasks: List[TaskProgress] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_progress(self) -> float:
        """Calculate overall workflow progress"""
        if not self.tasks:
            return 0.0
        return sum(t.progress for t in self.tasks) / len(self.tasks)

    @property
    def completed_tasks(self) -> int:
        """Count completed tasks"""
        return sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)

    @property
    def failed_tasks(self) -> int:
        """Count failed tasks"""
        return sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

    @property
    def duration(self) -> Optional[float]:
        """Get workflow duration in seconds"""
        if self.started_at is None:
            return None
        end_time = self.completed_at or time.time()
        return end_time - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "overall_progress": self.overall_progress,
            "tasks": [t.to_dict() for t in self.tasks],
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_tasks": len(self.tasks),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "metadata": self.metadata,
        }


class TaskTracker:
    """
    Tracks task and workflow execution progress

    Features:
    - Create and track workflows with multiple tasks
    - Update task status and progress
    - Subscribe to progress updates via callbacks
    - Get execution statistics and history
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize TaskTracker

        Args:
            max_history: Maximum number of completed workflows to keep
        """
        self.max_history = max_history
        self._active_workflows: Dict[str, WorkflowProgress] = {}
        self._completed_workflows: List[WorkflowProgress] = []
        self._progress_callbacks: List[Callable[[WorkflowProgress], None]] = []
        self._task_callbacks: List[Callable[[TaskProgress], None]] = []
        self._stats: Dict[str, int] = defaultdict(int)

    def create_workflow(
        self,
        workflow_id: str,
        workflow_name: str,
        task_names: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowProgress:
        """
        Create a new workflow to track

        Args:
            workflow_id: Unique workflow identifier
            workflow_name: Human-readable workflow name
            task_names: List of task names in the workflow
            metadata: Optional workflow metadata

        Returns:
            WorkflowProgress object
        """
        tasks = [
            TaskProgress(
                task_id=f"{workflow_id}_{i}",
                task_name=name,
            )
            for i, name in enumerate(task_names)
        ]

        workflow = WorkflowProgress(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            tasks=tasks,
            metadata=metadata or {},
        )

        self._active_workflows[workflow_id] = workflow
        self._stats["workflows_created"] += 1
        logger.debug(f"Created workflow: {workflow_id} with {len(tasks)} tasks")

        return workflow

    def start_workflow(self, workflow_id: str) -> None:
        """Mark workflow as started"""
        if workflow_id not in self._active_workflows:
            logger.warning(f"Workflow not found: {workflow_id}")
            return

        workflow = self._active_workflows[workflow_id]
        workflow.status = TaskStatus.RUNNING
        workflow.started_at = time.time()

        self._notify_workflow_update(workflow)
        logger.info(f"Started workflow: {workflow_id}")

    def start_task(
        self,
        workflow_id: str,
        task_index: int,
        message: str = ""
    ) -> None:
        """
        Mark a task as started

        Args:
            workflow_id: Workflow identifier
            task_index: Index of the task in the workflow
            message: Optional status message
        """
        workflow = self._active_workflows.get(workflow_id)
        if not workflow or task_index >= len(workflow.tasks):
            return

        task = workflow.tasks[task_index]
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.message = message

        self._notify_task_update(task)
        self._notify_workflow_update(workflow)

    def update_task_progress(
        self,
        workflow_id: str,
        task_index: int,
        progress: float,
        message: str = ""
    ) -> None:
        """
        Update task progress

        Args:
            workflow_id: Workflow identifier
            task_index: Index of the task
            progress: Progress value (0.0 to 1.0)
            message: Optional status message
        """
        workflow = self._active_workflows.get(workflow_id)
        if not workflow or task_index >= len(workflow.tasks):
            return

        task = workflow.tasks[task_index]
        task.progress = min(1.0, max(0.0, progress))
        if message:
            task.message = message

        self._notify_task_update(task)
        self._notify_workflow_update(workflow)

    def complete_task(
        self,
        workflow_id: str,
        task_index: int,
        result: Any = None,
        message: str = ""
    ) -> None:
        """
        Mark a task as completed

        Args:
            workflow_id: Workflow identifier
            task_index: Index of the task
            result: Task result
            message: Optional completion message
        """
        workflow = self._active_workflows.get(workflow_id)
        if not workflow or task_index >= len(workflow.tasks):
            return

        task = workflow.tasks[task_index]
        task.status = TaskStatus.COMPLETED
        task.progress = 1.0
        task.completed_at = time.time()
        task.result = result
        if message:
            task.message = message

        self._stats["tasks_completed"] += 1
        self._notify_task_update(task)
        self._notify_workflow_update(workflow)
        logger.debug(f"Completed task: {task.task_name}")

    def fail_task(
        self,
        workflow_id: str,
        task_index: int,
        error: str,
        message: str = ""
    ) -> None:
        """
        Mark a task as failed

        Args:
            workflow_id: Workflow identifier
            task_index: Index of the task
            error: Error message
            message: Optional status message
        """
        workflow = self._active_workflows.get(workflow_id)
        if not workflow or task_index >= len(workflow.tasks):
            return

        task = workflow.tasks[task_index]
        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        task.error = error
        if message:
            task.message = message

        self._stats["tasks_failed"] += 1
        self._notify_task_update(task)
        self._notify_workflow_update(workflow)
        logger.warning(f"Task failed: {task.task_name} - {error}")

    def complete_workflow(
        self,
        workflow_id: str,
        success: bool = True,
        message: str = ""
    ) -> Optional[WorkflowProgress]:
        """
        Mark workflow as completed

        Args:
            workflow_id: Workflow identifier
            success: Whether workflow succeeded
            message: Optional completion message

        Returns:
            Completed WorkflowProgress or None
        """
        if workflow_id not in self._active_workflows:
            return None

        workflow = self._active_workflows.pop(workflow_id)
        workflow.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        workflow.completed_at = time.time()
        if message:
            workflow.metadata["completion_message"] = message

        # Add to history
        self._completed_workflows.append(workflow)
        if len(self._completed_workflows) > self.max_history:
            self._completed_workflows.pop(0)

        if success:
            self._stats["workflows_completed"] += 1
        else:
            self._stats["workflows_failed"] += 1

        self._notify_workflow_update(workflow)
        logger.info(f"Completed workflow: {workflow_id} (success={success})")

        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """Get workflow progress by ID"""
        return self._active_workflows.get(workflow_id)

    def get_active_workflows(self) -> List[WorkflowProgress]:
        """Get all active workflows"""
        return list(self._active_workflows.values())

    def get_completed_workflows(self, limit: int = 10) -> List[WorkflowProgress]:
        """Get recently completed workflows"""
        return self._completed_workflows[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            "active_workflows": len(self._active_workflows),
            "completed_in_history": len(self._completed_workflows),
            "workflows_created": self._stats["workflows_created"],
            "workflows_completed": self._stats["workflows_completed"],
            "workflows_failed": self._stats["workflows_failed"],
            "tasks_completed": self._stats["tasks_completed"],
            "tasks_failed": self._stats["tasks_failed"],
        }

    def subscribe_workflow(
        self,
        callback: Callable[[WorkflowProgress], None]
    ) -> None:
        """Subscribe to workflow progress updates"""
        self._progress_callbacks.append(callback)

    def subscribe_task(
        self,
        callback: Callable[[TaskProgress], None]
    ) -> None:
        """Subscribe to task progress updates"""
        self._task_callbacks.append(callback)

    def unsubscribe_workflow(
        self,
        callback: Callable[[WorkflowProgress], None]
    ) -> None:
        """Unsubscribe from workflow updates"""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    def unsubscribe_task(
        self,
        callback: Callable[[TaskProgress], None]
    ) -> None:
        """Unsubscribe from task updates"""
        if callback in self._task_callbacks:
            self._task_callbacks.remove(callback)

    def _notify_workflow_update(self, workflow: WorkflowProgress) -> None:
        """Notify subscribers of workflow update"""
        for callback in self._progress_callbacks:
            try:
                callback(workflow)
            except Exception as e:
                logger.error(f"Workflow callback error: {e}")

    def _notify_task_update(self, task: TaskProgress) -> None:
        """Notify subscribers of task update"""
        for callback in self._task_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Task callback error: {e}")

    def clear_history(self) -> None:
        """Clear completed workflow history"""
        self._completed_workflows.clear()
        logger.info("Cleared workflow history")
