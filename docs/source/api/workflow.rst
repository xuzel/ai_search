Workflow Module
===============

The workflow module provides orchestration for multi-step tasks with support for parallel execution, dependencies, and error handling.

Overview
--------

Features:

* **Sequential execution**: Run tasks one by one
* **Parallel execution**: Run all tasks simultaneously
* **DAG execution**: Execute based on dependency graph
* **Error recovery**: Automatic retry with configurable attempts
* **Progress tracking**: Monitor task execution status
* **Callbacks**: Hook into task success/failure events

Workflow Engine
---------------

.. automodule:: src.workflow.workflow_engine
   :members:
   :undoc-members:
   :show-inheritance:

Result Aggregator
-----------------

.. automodule:: src.workflow.result_aggregator
   :members:
   :undoc-members:
   :show-inheritance:

Task Decomposer
---------------

.. automodule:: src.workflow.task_decomposer
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Sequential Workflow
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import WorkflowEngine, ExecutionMode

   engine = WorkflowEngine()

   # Create sequential workflow
   workflow = engine.create_workflow(
       "data_pipeline",
       mode=ExecutionMode.SEQUENTIAL
   )

   # Add tasks
   async def fetch_data():
       return {"data": [1, 2, 3]}

   async def process_data(fetch_result):
       return {"processed": fetch_result["data"]}

   async def save_data(process_result):
       return {"saved": True}

   workflow.add_task("fetch", func=fetch_data)
   workflow.add_task("process", func=process_data)
   workflow.add_task("save", func=save_data)

   # Execute
   result = await engine.execute(workflow)
   print(result.results)

Parallel Workflow
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import WorkflowEngine, ExecutionMode

   engine = WorkflowEngine()

   # Create parallel workflow
   workflow = engine.create_workflow(
       "parallel_tasks",
       mode=ExecutionMode.PARALLEL
   )

   # Add independent tasks
   async def task_a():
       return {"result": "A"}

   async def task_b():
       return {"result": "B"}

   async def task_c():
       return {"result": "C"}

   workflow.add_task("A", func=task_a)
   workflow.add_task("B", func=task_b)
   workflow.add_task("C", func=task_c)

   # Execute all in parallel
   result = await engine.execute(workflow)
   print(f"Completed: {result.completed_count}/{result.task_count}")

DAG Workflow with Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import WorkflowEngine, ExecutionMode

   engine = WorkflowEngine()

   # Create DAG workflow
   workflow = engine.create_workflow(
       "complex_pipeline",
       mode=ExecutionMode.DAG
   )

   # Task A has no dependencies
   async def task_a():
       return {"value": 10}

   # Task B depends on A
   async def task_b(a_result):
       return {"value": a_result["value"] * 2}

   # Task C depends on both A and B
   async def task_c(a_result, b_result):
       return {"value": a_result["value"] + b_result["value"]}

   workflow.add_task("A", func=task_a)
   workflow.add_task("B", func=task_b, dependencies={"A"})
   workflow.add_task("C", func=task_c, dependencies={"A", "B"})

   # Execute with dependency resolution
   result = await engine.execute(workflow)
   # A executes first
   # B executes after A completes
   # C executes after both A and B complete

Task with Retry
~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import WorkflowEngine

   engine = WorkflowEngine()
   workflow = engine.create_workflow("retry_example")

   async def unstable_task():
       # May fail sometimes
       import random
       if random.random() < 0.7:
           raise Exception("Task failed")
       return {"success": True}

   # Add task with retry
   workflow.add_task(
       "unstable",
       func=unstable_task,
       retry_count=5,  # Retry up to 5 times
       timeout=10.0    # 10 second timeout
   )

   result = await engine.execute(workflow)

Task with Callbacks
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import WorkflowEngine

   engine = WorkflowEngine()
   workflow = engine.create_workflow("callbacks")

   async def main_task():
       return {"result": 42}

   def on_success(task_result):
       print(f"Task succeeded with result: {task_result}")

   def on_failure(task_error):
       print(f"Task failed with error: {task_error}")

   workflow.add_task(
       "main",
       func=main_task,
       on_success=on_success,
       on_failure=on_failure
   )

   result = await engine.execute(workflow)

Task Decomposer
~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import TaskDecomposer
   from src.llm import LLMManager
   from src.utils import get_config

   config = get_config()
   llm_manager = LLMManager(config)
   decomposer = TaskDecomposer(llm_manager)

   # Decompose complex task
   complex_query = "Research quantum computing, summarize findings, and create a presentation"

   subtasks = await decomposer.decompose(complex_query)

   # subtasks = [
   #     {"name": "Research quantum computing", "type": "research"},
   #     {"name": "Summarize findings", "type": "synthesis"},
   #     {"name": "Create presentation", "type": "formatting"}
   # ]

Result Aggregator
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.workflow import ResultAggregator
   from src.llm import LLMManager
   from src.utils import get_config

   config = get_config()
   llm_manager = LLMManager(config)
   aggregator = ResultAggregator(llm_manager)

   # Aggregate multiple results
   results = {
       "search_1": {"title": "Article 1", "content": "..."},
       "search_2": {"title": "Article 2", "content": "..."},
       "search_3": {"title": "Article 3", "content": "..."}
   }

   final_result = await aggregator.aggregate(
       results,
       query="What is quantum computing?",
       aggregation_strategy="summarize"
   )

   print(final_result["summary"])
