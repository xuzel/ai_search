"""RAG Agent - Retrieval-Augmented Generation for document Q&A"""

import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from src.llm.manager import LLMManager
from src.tools.chunking import SmartChunker
from src.tools.document_processor import DocumentProcessor
from src.tools.advanced_pdf_processor import AdvancedPDFProcessor
from src.tools.vector_store import VectorStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGAgent:
    """RAG Agent for document-based question answering"""

    def __init__(
        self,
        llm_manager: LLMManager,
        vector_store: Optional[VectorStore] = None,
        config: Any = None,
        persist_directory: Optional[str] = None,
    ):
        """
        Initialize RAG Agent

        Args:
            llm_manager: LLM Manager instance
            vector_store: Optional VectorStore instance
            config: Configuration object
            persist_directory: Optional path to persist vector store
        """
        self.llm_manager = llm_manager
        self.config = config

        # Initialize components
        # Try AdvancedPDFProcessor first (better PDF handling), fallback to DocumentProcessor
        try:
            self.advanced_pdf_processor = AdvancedPDFProcessor()
            logger.info("AdvancedPDFProcessor initialized for enhanced PDF handling")
        except Exception as e:
            logger.warning(f"AdvancedPDFProcessor initialization failed: {e}")
            self.advanced_pdf_processor = None

        self.document_processor = DocumentProcessor()

        # Initialize vector store
        if vector_store:
            self.vector_store = vector_store
        else:
            # Create with default or config settings
            # Allow persist_directory parameter to override config
            if persist_directory:
                persist_dir = persist_directory
            else:
                persist_dir = getattr(config.rag, "persist_directory", "./data/vector_store") if config else "./data/vector_store"

            collection_name = getattr(config.rag, "collection_name", "documents") if config else "documents"
            embedding_model = getattr(config.rag, "embedding_model", "sentence-transformers/all-MiniLM-L6-v2") if config else "sentence-transformers/all-MiniLM-L6-v2"

            self.vector_store = VectorStore(
                persist_directory=persist_dir,
                collection_name=collection_name,
                embedding_model=embedding_model,
            )

        # Initialize chunker
        chunk_size = getattr(config.rag.chunking, "chunk_size", 512) if config else 512
        chunk_overlap = getattr(config.rag.chunking, "chunk_overlap", 77) if config else 77
        chunk_strategy = getattr(config.rag.chunking, "strategy", "semantic") if config else "semantic"

        self.chunker = SmartChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=chunk_strategy,
        )

        # RAG parameters
        if config and hasattr(config, 'rag') and hasattr(config.rag, 'retrieval'):
            self.retrieval_top_k = getattr(config.rag.retrieval, "top_k", 10)
            self.similarity_threshold = getattr(config.rag.retrieval, "similarity_threshold", 0.5)  # ✅ Changed default from 0.7 to 0.5
            logger.info(f"RAG retrieval settings: top_k={self.retrieval_top_k}, threshold={self.similarity_threshold}")
        else:
            # ✅ If config unavailable, use updated defaults matching config.yaml
            self.retrieval_top_k = 20
            self.similarity_threshold = 0.5  # ✅ Changed from 0.7 to 0.5
            logger.warning(f"Config not available, using defaults: top_k={self.retrieval_top_k}, threshold={self.similarity_threshold}")

        # Query expansion settings (default OFF to save costs)
        self.query_expansion_enabled = False

    async def ingest_document(
        self,
        file_path: str,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest a document into the vector store

        Args:
            file_path: Path to document
            show_progress: Show progress information

        Returns:
            Dict with ingestion stats
        """
        if show_progress:
            print(f"\n📄 Processing document: {file_path}")

        # 1. Process document
        # Use AdvancedPDFProcessor for PDFs (better OCR & table support), fallback to DocumentProcessor
        from pathlib import Path
        file_extension = Path(file_path).suffix.lower()

        if file_extension == ".pdf" and self.advanced_pdf_processor:
            if show_progress:
                print(f"🔍 Using Advanced PDF Processor (intelligent page type detection)...")
            try:
                pdf_result = await self.advanced_pdf_processor.process_pdf(file_path)

                # ✅ Check if PDF processing failed
                if "error" in pdf_result:
                    logger.error(f"PDF processing failed: {pdf_result['error']}")
                    if show_progress:
                        print(f"❌ PDF processing failed: {pdf_result['error']}")
                        print(f"🔄 Falling back to basic DocumentProcessor...")
                    # Fallback to DocumentProcessor
                    documents = self.document_processor.process_file(file_path)
                    if show_progress:
                        print(f"✅ Extracted {len(documents)} sections (using fallback)")
                else:
                    # Convert AdvancedPDFProcessor output to DocumentProcessor format
                    full_text = pdf_result.get("full_text", "")

                    # ✅ Check if extracted text is empty
                    if not full_text or not full_text.strip():
                        logger.warning(f"PDF {file_path} has no extractable text, trying fallback processor")
                        if show_progress:
                            print(f"⚠️ No text extracted, trying fallback processor...")
                        documents = self.document_processor.process_file(file_path)
                        if show_progress:
                            print(f"✅ Extracted {len(documents)} sections (using fallback)")
                    else:
                        # ✅ Convert page_type_distribution dict to JSON string for ChromaDB compatibility
                        import json
                        page_types_dict = pdf_result.get("page_type_distribution", {})
                        page_types_str = json.dumps(page_types_dict) if page_types_dict else "{}"

                        documents = [{
                            "content": full_text,
                            "metadata": {
                                "source": file_path,
                                "type": "pdf",
                                "page_count": pdf_result.get("total_pages", 0),
                                "processing_strategy": pdf_result.get("processing_strategy", "auto"),
                                "page_types": page_types_str  # ✅ Now a JSON string, not dict
                            }
                        }]
                        if show_progress:
                            stats = pdf_result.get("page_type_distribution", {})
                            print(f"✅ PDF processed: {pdf_result.get('total_pages', 0)} pages")
                            if stats:
                                print(f"   - Page types: text={stats.get('text', 0)}, "
                                      f"scanned={stats.get('scanned', 0)}, "
                                      f"complex={stats.get('complex', 0)}")
            except Exception as e:
                logger.warning(f"AdvancedPDFProcessor failed for {file_path}, fallback to DocumentProcessor: {e}")
                documents = self.document_processor.process_file(file_path)
                if show_progress:
                    print(f"✅ Extracted {len(documents)} sections (using fallback)")
        else:
            # For non-PDFs or if AdvancedPDFProcessor unavailable
            documents = self.document_processor.process_file(file_path)
            if show_progress:
                print(f"✅ Extracted {len(documents)} sections")

        # 2. Chunk documents
        if show_progress:
            print(f"🔪 Chunking documents...")

        chunks = self.chunker.chunk_documents(documents)

        if show_progress:
            print(f"✅ Created {len(chunks)} chunks")

        # 3. Add to vector store
        if show_progress:
            print(f"💾 Adding to vector store...")

        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        ids = self.vector_store.add_documents(
            texts=texts,
            metadatas=metadatas,
        )

        if show_progress:
            print(f"✅ Ingested {len(ids)} chunks")

        return {
            "file_path": file_path,
            "sections": len(documents),
            "chunks": len(chunks),
            "ids": ids,
        }

    async def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest all documents from a directory

        Args:
            directory_path: Path to directory
            recursive: Process subdirectories
            show_progress: Show progress information

        Returns:
            Dict with ingestion stats
        """
        if show_progress:
            print(f"\n📁 Processing directory: {directory_path}")

        # 1. Process all documents
        documents = self.document_processor.process_directory(
            directory_path,
            recursive=recursive,
        )

        if show_progress:
            print(f"✅ Extracted {len(documents)} sections from directory")

        # 2. Chunk documents
        chunks = self.chunker.chunk_documents(documents)

        if show_progress:
            print(f"✅ Created {len(chunks)} chunks")

        # 3. Add to vector store
        if show_progress:
            print(f"💾 Adding to vector store...")

        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        ids = self.vector_store.add_documents(
            texts=texts,
            metadatas=metadatas,
        )

        if show_progress:
            print(f"✅ Ingested {len(ids)} chunks from directory")

        return {
            "directory_path": directory_path,
            "sections": len(documents),
            "chunks": len(chunks),
            "ids": ids,
        }

    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        show_progress: bool = True,
    ) -> Dict[str, Any]:
        """
        Query documents with RAG

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            show_progress: Show progress information

        Returns:
            Dict with answer, sources, and metadata
        """
        if show_progress:
            print(f"\n🔍 Searching documents for: {question}")

        # Use config value if not specified
        if top_k is None:
            top_k = self.retrieval_top_k

        # 1. Retrieve relevant chunks
        results = self.vector_store.similarity_search(
            query=question,
            k=top_k,
        )

        if show_progress:
            print(f"✅ Found {len(results)} relevant chunks")

        # Filter by similarity threshold
        filtered_results = [
            r for r in results
            if r["score"] >= self.similarity_threshold
        ]

        if show_progress:
            print(f"✅ {len(filtered_results)} chunks above threshold ({self.similarity_threshold})")

        if not filtered_results:
            return {
                "question": question,
                "answer": "No relevant information found in the documents.",
                "sources": [],
                "retrieved_chunks": 0,
            }

        # 2. Generate answer with context
        if show_progress:
            print(f"🤖 Generating answer...")

        answer = await self._generate_answer(question, filtered_results)

        # 3. Prepare sources
        sources = []
        for result in filtered_results[:5]:  # Top 5 sources
            sources.append({
                "text": result["text"][:200] + "...",  # Preview
                "score": result["score"],
                "metadata": result["metadata"],
            })

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(filtered_results),
        }

    async def stream_query(
        self,
        question: str,
        top_k: Optional[int] = None,
        expand_query: Optional[bool] = None,
    ) -> AsyncGenerator[Union[Dict[str, Any], str], None]:
        """
        Query documents with streaming answer generation

        Args:
            question: User question
            top_k: Number of chunks to retrieve
            expand_query: Whether to expand query (None uses default setting)

        Yields:
            - Dict with 'type': 'progress' for stage updates
            - Dict with 'type': 'sources' for retrieved sources
            - Dict with 'type': 'expanded_queries' for expanded queries
            - String chunks for streaming answer
        """
        logger.info(f"Stream querying: {question}")

        # Determine if query expansion should be used
        use_expansion = expand_query if expand_query is not None else self.query_expansion_enabled

        # Use config value if not specified
        if top_k is None:
            top_k = self.retrieval_top_k

        # Step 1: Optional query expansion
        queries_to_search = [question]
        if use_expansion:
            yield {"type": "progress", "stage": "expansion", "message": "Expanding query..."}
            expanded = await self._expand_query(question)
            if expanded:
                queries_to_search.extend(expanded)
                yield {
                    "type": "expanded_queries",
                    "queries": queries_to_search
                }

        # Step 2: Retrieve relevant chunks
        yield {"type": "progress", "stage": "retrieve", "message": "Searching documents..."}

        all_results = []
        seen_texts = set()

        for query in queries_to_search:
            results = self.vector_store.similarity_search(
                query=query,
                k=top_k,
            )
            # Deduplicate results
            for r in results:
                text_hash = hash(r["text"][:100])
                if text_hash not in seen_texts:
                    seen_texts.add(text_hash)
                    all_results.append(r)

        # Sort by score and take top results
        all_results.sort(key=lambda x: x["score"], reverse=True)
        all_results = all_results[:top_k]

        yield {
            "type": "progress",
            "stage": "retrieve_complete",
            "message": f"Found {len(all_results)} relevant chunks"
        }

        # Filter by similarity threshold
        filtered_results = [
            r for r in all_results
            if r["score"] >= self.similarity_threshold
        ]

        yield {
            "type": "progress",
            "stage": "filter",
            "message": f"{len(filtered_results)} chunks above threshold ({self.similarity_threshold})"
        }

        if not filtered_results:
            yield {"type": "progress", "stage": "complete", "message": "No relevant information found"}
            yield "No relevant information found in the documents."
            return

        # Yield sources
        sources = []
        for result in filtered_results[:5]:
            sources.append({
                "text": result["text"][:200] + "...",
                "score": result["score"],
                "metadata": result["metadata"],
            })
        yield {"type": "sources", "sources": sources}

        # Step 3: Stream answer generation
        yield {"type": "progress", "stage": "generate", "message": "Generating answer..."}

        async for chunk in self._stream_generate_answer(question, filtered_results):
            yield chunk

        yield {"type": "progress", "stage": "complete", "message": "Complete!"}

    async def _expand_query(self, question: str) -> List[str]:
        """
        Expand original query into related queries for better retrieval

        Args:
            question: Original question

        Returns:
            List of expanded queries
        """
        prompt = f"""Given the following question, generate 2-3 alternative phrasings or related questions that would help retrieve more relevant information. These should cover different aspects or use different terminology.

Question: {question}

Return ONLY a JSON array of strings, no explanations:
["query1", "query2", "query3"]"""

        messages = [{"role": "user", "content": prompt}]

        try:
            response = await self.llm_manager.complete(messages, max_tokens=200)

            # Parse JSON array
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                queries = json.loads(json_match.group())
                if isinstance(queries, list):
                    return [q for q in queries if isinstance(q, str)][:3]
            return []

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return []

    async def _stream_generate_answer(
        self,
        question: str,
        results: List[Dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """
        Stream answer generation using LLM with retrieved context

        Args:
            question: User question
            results: Retrieved chunks with scores

        Yields:
            Answer text chunks
        """
        # Build context from top results
        context = "\n\n---\n\n".join([
            f"[Source {i+1}] (Relevance: {r['score']:.2f})\n{r['text']}"
            for i, r in enumerate(results[:5])
        ])

        prompt = f"""基于以下文档内容回答问题。请：
1. 仅使用提供的文档内容回答
2. 如果文档中没有相关信息，请明确说明
3. 引用具体的来源
4. 用中文或英文回答（根据问题的语言）

文档内容：
{context}

问题：{question}

回答："""

        messages = [{"role": "user", "content": prompt}]

        try:
            async for chunk in self.llm_manager.stream_complete(
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming answer: {e}")
            yield "Error generating answer. Please try again."

    def set_query_expansion(self, enabled: bool) -> None:
        """Enable or disable query expansion"""
        self.query_expansion_enabled = enabled
        logger.info(f"Query expansion {'enabled' if enabled else 'disabled'}")

    async def _generate_answer(
        self,
        question: str,
        results: List[Dict[str, Any]],
    ) -> str:
        """
        Generate answer using LLM with retrieved context

        Args:
            question: User question
            results: Retrieved chunks with scores

        Returns:
            Generated answer
        """
        # Build context from top results
        context = "\n\n---\n\n".join([
            f"[Source {i+1}] (Relevance: {r['score']:.2f})\n{r['text']}"
            for i, r in enumerate(results[:5])  # Use top 5 chunks
        ])

        prompt = f"""基于以下文档内容回答问题。请：
1. 仅使用提供的文档内容回答
2. 如果文档中没有相关信息，请明确说明
3. 引用具体的来源
4. 用中文或英文回答（根据问题的语言）

文档内容：
{context}

问题：{question}

回答："""

        messages = [
            {"role": "user", "content": prompt}
        ]

        try:
            answer = await self.llm_manager.complete(
                messages=messages,
                temperature=0.3,  # Lower temperature for factual answers
                max_tokens=1000,
            )
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Error generating answer. Please try again."

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        return self.vector_store.get_collection_stats()

    def clear_documents(self) -> None:
        """Clear all documents from the vector store"""
        self.vector_store.clear_collection()
        logger.info("Cleared all documents from vector store")
