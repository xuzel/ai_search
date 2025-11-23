"""Master Agent - Unified query processor with automatic tool orchestration

This agent serves as the central coordinator that:
1. Processes user queries (text + optional files)
2. Automatically determines which tools/agents are needed
3. Orchestrates multi-tool workflows
4. Aggregates results and generates natural language responses

Architecture:
    User Query → File Processing → Task Decomposition → Workflow Execution
    → Result Aggregation → LLM Enhancement → Unified Response
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.llm.manager import LLMManager
from src.agents import ResearchAgent, CodeAgent, ChatAgent, RAGAgent
from src.tools import (
    WeatherTool,
    FinanceTool,
    RoutingTool,
    OCRTool,
    VisionTool,
    SearchTool,
    ScraperTool,
    CodeExecutor,
)
from src.workflow import TaskDecomposer, WorkflowEngine, ResultAggregator
from src.workflow.task_decomposer import TaskPlan, SubTask
from src.workflow.workflow_engine import Task, ExecutionMode
from src.utils import get_logger, extract_location, extract_stock_symbol, extract_route

logger = get_logger(__name__)


class MasterAgent:
    """
    Master Agent for unified query processing

    This agent automatically:
    - Processes file uploads (images/documents)
    - Decomposes complex queries into subtasks
    - Calls appropriate tools/agents
    - Aggregates and synthesizes results
    - Returns natural language answers

    Example:
        master = MasterAgent(llm_manager, config)
        result = await master.process_query(
            query="What's the weather in Beijing?",
            uploaded_file=None
        )
        # Returns: {"answer": "...", "tools_used": [...], "details": {...}}
    """

    def __init__(
        self,
        llm_manager: LLMManager,
        search_tool: SearchTool,
        scraper_tool: ScraperTool,
        code_executor: CodeExecutor,
        weather_tool: Optional[WeatherTool] = None,
        finance_tool: Optional[FinanceTool] = None,
        routing_tool: Optional[RoutingTool] = None,
        ocr_tool: Optional[OCRTool] = None,
        vision_tool: Optional[VisionTool] = None,
        rag_agent: Optional[RAGAgent] = None,
        config: Any = None,
    ):
        """
        Initialize Master Agent

        Args:
            llm_manager: LLM manager instance
            search_tool: Web search tool
            scraper_tool: Web scraper tool
            code_executor: Code execution tool
            weather_tool: Weather API tool (optional)
            finance_tool: Finance API tool (optional)
            routing_tool: Routing API tool (optional)
            ocr_tool: OCR tool (optional)
            vision_tool: Vision AI tool (optional)
            rag_agent: RAG agent (optional)
            config: Configuration object
        """
        self.llm_manager = llm_manager
        self.config = config

        # Initialize sub-agents
        self.research_agent = ResearchAgent(
            llm_manager=llm_manager,
            search_tool=search_tool,
            scraper_tool=scraper_tool,
            config=config,
        )
        self.code_agent = CodeAgent(
            llm_manager=llm_manager,
            code_executor=code_executor,
            config=config,
        )
        self.chat_agent = ChatAgent(
            llm_manager=llm_manager,
            config=config,
        )
        self.rag_agent = rag_agent

        # Store tools
        self.weather_tool = weather_tool
        self.finance_tool = finance_tool
        self.routing_tool = routing_tool
        self.ocr_tool = ocr_tool
        self.vision_tool = vision_tool

        # Initialize workflow components
        self.task_decomposer = TaskDecomposer(llm_manager)
        self.workflow_engine = WorkflowEngine()
        self.result_aggregator = ResultAggregator(llm_manager)

        # Tool executor registry
        self._register_tool_executors()

        logger.info("MasterAgent initialized with all tools")

    def _register_tool_executors(self):
        """Register all tool executor functions"""
        self.tool_executors = {
            "search": self._execute_search,
            "code": self._execute_code,
            "chat": self._execute_chat,
            "rag": self._execute_rag,
            "weather": self._execute_weather,
            "finance": self._execute_finance,
            "routing": self._execute_routing,
            "ocr": self._execute_ocr,
            "vision": self._execute_vision,
        }

    async def process_query(
        self,
        query: str,
        uploaded_file: Optional[Any] = None,
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process user query with automatic tool orchestration

        Args:
            query: User query text
            uploaded_file: Optional UploadFile object (from FastAPI)
            file_path: Optional direct file path (if not using UploadFile)

        Returns:
            Dict with keys:
                - answer: Natural language answer
                - tools_used: List of tools called
                - sources: List of sources (if applicable)
                - details: Detailed results from each tool
                - confidence: Confidence score
        """
        logger.info(f"Processing query: {query[:100]}...")

        # Step 1: Handle file upload if present
        file_context = None
        if uploaded_file or file_path:
            file_context = await self._handle_file_upload(
                query, uploaded_file, file_path
            )

            # If file was processed directly (OCR/Vision), may return immediately
            if file_context.get("direct_answer"):
                return file_context["direct_answer"]

        # Step 2: Decompose query into subtasks
        context = {"file_context": file_context} if file_context else None
        task_plan = await self.task_decomposer.decompose(query, context)

        logger.info(
            f"Decomposed into {len(task_plan.subtasks)} subtasks "
            f"(complexity: {task_plan.complexity})"
        )

        # Step 3: Execute workflow
        tool_results = await self._execute_workflow(task_plan, file_context)

        # Step 4: Aggregate and synthesize results
        final_result = await self._synthesize_final_answer(
            query, task_plan, tool_results
        )

        return final_result

    async def _handle_file_upload(
        self,
        query: str,
        uploaded_file: Optional[Any],
        file_path: Optional[str],
    ) -> Dict[str, Any]:
        """
        Handle file upload and determine processing strategy

        Returns:
            Dict with file processing context or direct answer
        """
        # Determine file type and path
        if uploaded_file:
            filename = uploaded_file.filename
            # Save temp file
            temp_path = await self._save_temp_file(uploaded_file)
            file_path = temp_path
        else:
            filename = os.path.basename(file_path) if file_path else ""

        file_ext = filename.split('.')[-1].lower() if filename else ""

        logger.info(f"Processing file: {filename} (type: {file_ext})")

        # Image files → OCR or Vision
        if file_ext in ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp']:
            # Determine if OCR or Vision based on query intent
            if self._is_ocr_intent(query):
                # OCR: Extract text
                if not self.ocr_tool:
                    return {"error": "OCR tool not available"}

                ocr_result = await self.ocr_tool.extract_text(file_path)

                # Enhance OCR result with LLM if there's a question
                if query and query.strip() not in ["", "."]:
                    enhanced_answer = await self._enhance_ocr_with_llm(
                        query, ocr_result
                    )
                    return {
                        "direct_answer": {
                            "answer": enhanced_answer,
                            "tools_used": ["ocr", "chat"],
                            "details": {"ocr": ocr_result},
                            "confidence": 0.85,
                        }
                    }
                else:
                    # Just return OCR text
                    return {
                        "direct_answer": {
                            "answer": ocr_result.get("text", ""),
                            "tools_used": ["ocr"],
                            "details": {"ocr": ocr_result},
                            "confidence": 0.80,
                        }
                    }
            else:
                # Vision: Analyze image
                if not self.vision_tool:
                    return {"error": "Vision tool not available"}

                vision_result = await self.vision_tool.analyze_image(
                    file_path,
                    prompt=query if query else "Describe this image in detail"
                )

                return {
                    "direct_answer": {
                        "answer": vision_result.get("description", ""),
                        "tools_used": ["vision"],
                        "details": {"vision": vision_result},
                        "confidence": 0.85,
                    }
                }

        # Document files → RAG
        elif file_ext in ['pdf', 'txt', 'md', 'docx', 'doc']:
            if not self.rag_agent:
                return {"error": "RAG not available"}

            # Upload to RAG (async background)
            logger.info(f"Uploading document to RAG: {filename}")
            asyncio.create_task(
                self._upload_to_rag_background(file_path, filename)
            )

            # Return context for RAG query
            return {
                "document_uploaded": True,
                "filename": filename,
                "rag_available": True,
            }

        return {}

    async def _save_temp_file(self, uploaded_file: Any) -> str:
        """Save uploaded file to temporary location"""
        temp_dir = Path("src/web/uploads/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / uploaded_file.filename

        # Read and write file content
        content = await uploaded_file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path)

    def _is_ocr_intent(self, query: str) -> bool:
        """Determine if user wants OCR vs Vision analysis"""
        ocr_keywords = [
            "提取", "文字", "识别", "ocr", "扫描", "文本",
            "extract", "text", "recognize", "scan"
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in ocr_keywords)

    async def _enhance_ocr_with_llm(
        self,
        query: str,
        ocr_result: Dict[str, Any]
    ) -> str:
        """Use LLM to answer question based on OCR extracted text"""
        ocr_text = ocr_result.get("text", "")

        prompt = f"""用户上传了一张图片，我已经用OCR提取了文字。请根据提取的文字回答用户的问题。

提取的文字：
{ocr_text}

用户问题：{query}

请直接回答用户的问题。如果文字无法回答问题，请说明。"""

        response = await self.chat_agent.chat(prompt)
        return response

    async def _upload_to_rag_background(
        self,
        file_path: str,
        filename: str
    ):
        """Background task to upload document to RAG"""
        try:
            await self.rag_agent.ingest_document(file_path)
            logger.info(f"Document uploaded to RAG: {filename}")
        except Exception as e:
            logger.error(f"RAG upload failed: {e}")

    async def _execute_workflow(
        self,
        task_plan: TaskPlan,
        file_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Execute task plan using workflow engine

        Returns:
            Dict of {subtask_id: result}
        """
        # Create workflow tasks from subtasks
        tasks = []
        results_store = {}

        for subtask in task_plan.subtasks:
            # Get executor function
            executor = self.tool_executors.get(subtask.tool)

            if not executor:
                logger.warning(f"No executor for tool: {subtask.tool}")
                continue

            # Create async task function
            async def task_func(
                st=subtask,
                exec_func=executor,
                store=results_store,
                ctx=file_context,
                **kwargs  # Accept dependency results injected by WorkflowEngine
            ):
                # Resolve dependencies (replace {{variable}} in query)
                query = st.query
                for dep_id in st.dependencies:
                    if dep_id in store:
                        var_name = f"{{{{{dep_id}}}}}"
                        query = query.replace(var_name, str(store[dep_id]))

                # Execute tool
                result = await exec_func(query, ctx)
                store[st.output_variable] = result
                return result

            # Create Task for workflow engine
            task = Task(
                id=subtask.id,
                name=subtask.description,
                func=task_func,
                dependencies=set(subtask.dependencies),
            )
            tasks.append(task)

        # Execute workflow
        if len(tasks) == 1:
            # Single task: execute directly
            await tasks[0].func()
        else:
            # Multiple tasks: use workflow engine
            # Create workflow with DAG mode
            workflow = self.workflow_engine.create_workflow(
                workflow_id=f"master_plan_{task_plan.goal[:30]}",
                mode=ExecutionMode.DAG
            )

            # Add tasks to workflow
            for task in tasks:
                workflow.tasks[task.id] = task

            # Execute workflow
            await self.workflow_engine.execute(workflow)

        return results_store

    async def _synthesize_final_answer(
        self,
        query: str,
        task_plan: TaskPlan,
        tool_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesize final answer from all tool results using LLM

        Returns:
            Final result dict
        """
        # Extract tools used
        tools_used = [st.tool for st in task_plan.subtasks]

        # If only one result, simplify
        if len(tool_results) == 1:
            single_result = list(tool_results.values())[0]

            # If it's already a good answer, return it
            if isinstance(single_result, dict) and "answer" in single_result:
                return {
                    "answer": single_result["answer"],
                    "tools_used": tools_used,
                    "details": tool_results,
                    "confidence": single_result.get("confidence", 0.8),
                }

            # Otherwise, enhance with LLM
            answer = await self._enhance_single_result_with_llm(
                query, single_result, tools_used[0]
            )

            return {
                "answer": answer,
                "tools_used": tools_used,
                "details": tool_results,
                "confidence": 0.85,
            }

        # Multiple results: aggregate and synthesize
        # Convert results to list format for aggregator
        results_list = []
        for var_name, result in tool_results.items():
            results_list.append({
                "source": var_name,
                "content": str(result),
                "result": result,
            })

        # Aggregate using ResultAggregator
        aggregated = await self.result_aggregator.aggregate(
            results_list,
            query=query,
            strategy="synthesis",
        )

        # Extract sources if any
        sources = []
        for result in tool_results.values():
            if isinstance(result, dict) and "sources" in result:
                sources.extend(result["sources"])

        return {
            "answer": aggregated.summary,
            "tools_used": tools_used,
            "sources": sources,
            "details": tool_results,
            "key_points": aggregated.key_points,
            "confidence": aggregated.confidence,
        }

    async def _enhance_single_result_with_llm(
        self,
        query: str,
        result: Any,
        tool_name: str,
    ) -> str:
        """Enhance single tool result with LLM to generate natural language"""

        prompt = f"""用户提问：{query}

我使用了{tool_name}工具获取了以下信息：

{str(result)}

请根据这些信息，用自然语言回答用户的问题。回答要简洁、准确、友好。"""

        response = await self.chat_agent.chat(prompt)
        return response

    # Tool executor methods

    async def _execute_search(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute web search"""
        result = await self.research_agent.research(query, show_progress=False)
        return result

    async def _execute_code(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute code generation and execution"""
        result = await self.code_agent.solve(query)
        return result

    async def _execute_chat(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> str:
        """Execute chat/reasoning"""
        response = await self.chat_agent.chat(query)
        return response

    async def _execute_rag(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute RAG query"""
        if not self.rag_agent:
            return {"error": "RAG not available"}

        result = await self.rag_agent.query(query)
        return result

    async def _execute_weather(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute weather query

        Query is already processed by TaskDecomposer (LLM),
        so it should contain just the location (e.g., "Beijing")
        """
        if not self.weather_tool:
            return {"error": "Weather tool not available"}

        # Use query directly (LLM has already extracted the location)
        # Fallback to regex extraction only if needed
        location = query.strip()
        if not location or len(location) > 50:  # Sanity check
            location = extract_location(query)

        weather_data = await self.weather_tool.get_current_weather(location)
        return weather_data

    async def _execute_finance(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute finance/stock query

        Query is already processed by TaskDecomposer (LLM),
        so it should contain just the symbol (e.g., "AAPL")
        """
        if not self.finance_tool:
            return {"error": "Finance tool not available"}

        # Use query directly (LLM has already extracted the symbol)
        # Fallback to regex extraction only if needed
        symbol = query.strip().upper()
        if not symbol or len(symbol) > 10:  # Sanity check
            symbol = extract_stock_symbol(query)

        stock_data = await self.finance_tool.get_stock_price(symbol)
        return stock_data

    async def _execute_routing(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute routing query

        Query is already processed by TaskDecomposer (LLM),
        which should provide something like "Beijing to Shanghai" or "北京到上海"
        """
        if not self.routing_tool:
            return {"error": "Routing tool not available"}

        # Try to extract origin and destination from LLM-processed query
        origin, destination = extract_route(query)

        # If extraction fails, try using LLM for entity extraction
        if not origin or not destination:
            # Use LLM as fallback for complex routing queries
            logger.warning(f"Could not extract route from: {query}")
            return {
                "error": "Could not extract origin/destination from query",
                "suggestion": "Please specify route in format: 'from X to Y' or '从X到Y'"
            }

        route_data = await self.routing_tool.get_route(
            origin,
            destination,
            profile="driving-car",
        )
        return route_data

    async def _execute_ocr(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute OCR (should be handled in file upload)"""
        if not context or "file_path" not in context:
            return {"error": "No image file provided"}

        if not self.ocr_tool:
            return {"error": "OCR tool not available"}

        ocr_result = await self.ocr_tool.extract_text(context["file_path"])
        return ocr_result

    async def _execute_vision(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute vision analysis (should be handled in file upload)"""
        if not context or "file_path" not in context:
            return {"error": "No image file provided"}

        if not self.vision_tool:
            return {"error": "Vision tool not available"}

        vision_result = await self.vision_tool.analyze_image(
            context["file_path"],
            prompt=query,
        )
        return vision_result
