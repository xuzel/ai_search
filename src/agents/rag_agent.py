"""RAG Agent - Retrieval-Augmented Generation for document Q&A"""

from typing import Any, Dict, List, Optional

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
        if config:
            self.retrieval_top_k = getattr(config.rag.retrieval, "top_k", 10)
            self.similarity_threshold = getattr(config.rag.retrieval, "similarity_threshold", 0.7)
        else:
            self.retrieval_top_k = 10
            self.similarity_threshold = 0.7

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
                # Convert AdvancedPDFProcessor output to DocumentProcessor format
                full_text = pdf_result.get("full_text", "")
                documents = [{
                    "content": full_text,
                    "metadata": {
                        "source": file_path,
                        "type": "pdf",
                        "page_count": pdf_result.get("total_pages", 0),
                        "processing_strategy": pdf_result.get("processing_strategy", "auto"),
                        "page_types": pdf_result.get("page_type_distribution", {})
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
