"""RAG Document Q&A Router"""

import asyncio
from pathlib import Path

from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from src.utils import get_config, get_logger
from src.llm import LLMManager
from src.agents import RAGAgent
from src.web import database
from src.web.upload_manager import UploadManager
from src.web.dependencies.formatters import convert_markdown_to_html
from src.web.middleware import limiter, get_limit

logger = get_logger(__name__)

router = APIRouter()

# Global instances
rag_agent = None
upload_manager = None


async def initialize_rag():
    """Initialize RAG agent and dependencies"""
    global config, llm_manager, rag_agent, upload_manager

    if rag_agent is None:
        config = get_config()
        llm_manager = LLMManager(config=config)

        # Initialize RAG agent with config
        rag_agent = RAGAgent(
            llm_manager=llm_manager,
            config=config
        )

        upload_manager = UploadManager()
        logger.info("RAG agent initialized successfully")


@router.get("/rag", response_class=HTMLResponse)
async def rag_page(request: Request):
    """Render RAG document Q&A page"""
    templates = request.app.state.templates

    # Get statistics
    stats = await database.get_rag_statistics()

    return templates.TemplateResponse(
        "pages/rag.html",
        {
            "request": request,
            "breadcrumb_section": "Document Q&A",
            "stats": stats
        }
    )


@router.post("/rag/upload", response_class=HTMLResponse)
@limiter.limit(get_limit("upload"))  # 10 requests/minute
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Upload and process a document for RAG

    Supported formats: PDF, TXT, MD, DOCX
    """
    await initialize_rag()
    templates = request.app.state.templates

    try:
        # Validate file
        allowed_types = ['pdf', 'txt', 'md', 'docx', 'doc']
        await upload_manager.validate_file(
            file,
            allowed_types=allowed_types,
            max_size=50 * 1024 * 1024  # 50MB
        )

        # Save file
        file_info = await upload_manager.save_document(file)

        # Save to database
        doc_id = await database.save_rag_document(
            filename=file_info['filename'],
            saved_filename=file_info['saved_filename'],
            filepath=file_info['filepath'],
            file_type=Path(file.filename).suffix.lstrip('.'),
            file_size=file_info['file_size'],
            file_hash=file_info['file_hash'],
            metadata={
                'upload_timestamp': file_info['upload_timestamp'],
                'relative_path': file_info['relative_path']
            }
        )

        # Process document asynchronously
        asyncio.create_task(process_document_background(doc_id, file_info['filepath']))

        # Return success message
        return templates.TemplateResponse(
            "components/upload_success.html",
            {
                "request": request,
                "filename": file_info['filename'],
                "file_size": file_info['file_size'],
                "doc_id": doc_id,
                "message": "Document uploaded successfully and is being processed..."
            }
        )

    except ValueError as e:
        # Validation error
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": f"Upload failed: {str(e)}"
            }
        )


async def process_document_background(doc_id: int, filepath: str):
    """Process document in background"""
    try:
        await initialize_rag()

        # Update status to processing
        await database.update_rag_document_status(doc_id, "processing")

        # Ingest document using RAG agent
        result = await rag_agent.ingest_document(filepath, show_progress=False)

        # Update document with processing results
        await database.update_rag_document(
            doc_id,
            processing_status="completed",
            num_chunks=result.get('chunks', 0),
            vector_store_ids=result.get('ids', [])
        )

        logger.info(f"Document {doc_id} processed successfully: {result.get('chunks', 0)} chunks")

    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}", exc_info=True)
        await database.update_rag_document_status(doc_id, "failed")


@router.post("/rag/query", response_class=HTMLResponse)
@limiter.limit(get_limit("query"))  # 30 requests/minute
async def query_documents(
    request: Request,
    query: str = Form(...),
    top_k: int = Form(5)
):
    """
    Query documents using RAG

    Args:
        query: User question
        top_k: Number of relevant chunks to retrieve
    """
    await initialize_rag()
    templates = request.app.state.templates

    try:
        # Check if there are any documents
        stats = await database.get_rag_statistics()
        if stats['total_documents'] == 0:
            return templates.TemplateResponse(
                "components/error.html",
                {
                    "request": request,
                    "error_message": "No documents uploaded yet. Please upload documents first."
                }
            )

        # Query RAG agent
        logger.info(f"RAG query: {query}")
        result = await rag_agent.query(query, top_k=top_k, show_progress=False)

        # Convert answer to HTML markdown (using singleton processor)
        if result.get('answer'):
            result['answer'] = convert_markdown_to_html(result['answer'])

        # Save to conversation history
        import json
        await database.save_conversation(
            mode="rag",
            query=query,
            response=result.get('answer', ''),
            metadata=json.dumps({
                "num_sources": len(result.get('sources', [])),
                "top_k": top_k
            })
        )

        # Render result
        return templates.TemplateResponse(
            "components/result_rag.html",
            {
                "request": request,
                "query": query,
                "result": result,
                "top_k": top_k
            }
        )

    except Exception as e:
        logger.error(f"Error querying documents: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": str(e),
                "query": query
            }
        )


@router.get("/rag/documents", response_class=HTMLResponse)
async def list_documents(request: Request, limit: int = 50):
    """List all uploaded documents"""
    templates = request.app.state.templates

    try:
        documents = await database.get_rag_documents(limit=limit)
        stats = await database.get_rag_statistics()

        return templates.TemplateResponse(
            "components/document_list.html",
            {
                "request": request,
                "documents": documents,
                "stats": stats
            }
        )
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        return templates.TemplateResponse(
            "components/error.html",
            {
                "request": request,
                "error_message": str(e)
            }
        )


@router.delete("/rag/documents/{doc_id}")
async def delete_document(doc_id: int):
    """Delete a document"""
    try:
        await initialize_rag()

        # Get document info
        documents = await database.get_rag_documents(limit=1000)
        doc = next((d for d in documents if d['id'] == doc_id), None)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from vector store
        if doc.get('vector_store_ids'):
            import json
            vector_ids = json.loads(doc['vector_store_ids']) if isinstance(doc['vector_store_ids'], str) else doc['vector_store_ids']
            rag_agent.vector_store.delete_by_ids(vector_ids)

        # Delete file
        filepath = Path(doc['filepath'])
        if filepath.exists():
            filepath.unlink()

        # Delete from database
        await database.delete_rag_document(doc_id)

        return JSONResponse(
            content={
                "success": True,
                "message": f"Document {doc['filename']} deleted successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/stats")
async def get_statistics():
    """Get RAG statistics (JSON API)"""
    try:
        stats = await database.get_rag_statistics()
        documents = await database.get_rag_documents(limit=10)

        return JSONResponse(content={
            "statistics": stats,
            "recent_documents": [
                {
                    "id": doc['id'],
                    "filename": doc['filename'],
                    "status": doc['processing_status'],
                    "num_chunks": doc['num_chunks'],
                    "upload_timestamp": doc['upload_timestamp']
                }
                for doc in documents
            ]
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/reprocess/{doc_id}")
async def reprocess_document(doc_id: int):
    """Reprocess a failed document"""
    try:
        # Get document info
        documents = await database.get_rag_documents(limit=1000)
        doc = next((d for d in documents if d['id'] == doc_id), None)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Reprocess in background
        asyncio.create_task(process_document_background(doc_id, doc['filepath']))

        return JSONResponse(content={
            "success": True,
            "message": "Document reprocessing started"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
