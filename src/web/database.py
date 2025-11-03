"""Database module for storing conversation history"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "history.db"


async def init_db():
    """Initialize the database and create tables if not exists"""

    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Conversation history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                mode TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Create index for faster searches
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON conversation_history(timestamp DESC)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_mode
            ON conversation_history(mode)
        """)

        # RAG documents table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rag_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                saved_filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                file_hash TEXT,
                upload_timestamp TEXT NOT NULL,
                processing_status TEXT DEFAULT 'pending',
                num_chunks INTEGER DEFAULT 0,
                vector_store_ids TEXT,
                metadata TEXT
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_upload_timestamp
            ON rag_documents(upload_timestamp DESC)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_status
            ON rag_documents(processing_status)
        """)

        await db.commit()


async def save_conversation(
    mode: str,
    query: str,
    response: str,
    metadata: Optional[str] = None
) -> int:
    """
    Save a conversation to the database

    Args:
        mode: Conversation mode (research, code, chat)
        query: User query
        response: AI response
        metadata: Optional JSON metadata

    Returns:
        ID of the saved conversation
    """

    timestamp = datetime.now().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO conversation_history
            (timestamp, mode, query, response, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, mode, query, response, metadata)
        )
        await db.commit()
        return cursor.lastrowid


async def get_recent_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent conversations

    Args:
        limit: Maximum number of conversations to return

    Returns:
        List of conversation dictionaries
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, timestamp, mode, query, response, metadata
            FROM conversation_history
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_conversation_by_id(conversation_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific conversation by ID

    Args:
        conversation_id: The ID of the conversation

    Returns:
        Conversation dictionary or None if not found
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, timestamp, mode, query, response, metadata
            FROM conversation_history
            WHERE id = ?
            """,
            (conversation_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def search_conversations(
    search_query: str,
    mode: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search conversations by query text

    Args:
        search_query: Search term
        mode: Optional mode filter (research, code, chat)
        limit: Maximum number of results

    Returns:
        List of matching conversation dictionaries
    """

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if mode:
            cursor = await db.execute(
                """
                SELECT id, timestamp, mode, query, response, metadata
                FROM conversation_history
                WHERE mode = ? AND (query LIKE ? OR response LIKE ?)
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (mode, f"%{search_query}%", f"%{search_query}%", limit)
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, timestamp, mode, query, response, metadata
                FROM conversation_history
                WHERE query LIKE ? OR response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"%{search_query}%", f"%{search_query}%", limit)
            )

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_conversation(conversation_id: int) -> bool:
    """
    Delete a conversation by ID

    Args:
        conversation_id: The ID of the conversation to delete

    Returns:
        True if deleted, False if not found
    """

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM conversation_history WHERE id = ?",
            (conversation_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def clear_all_history() -> int:
    """
    Clear all conversation history

    Returns:
        Number of deleted conversations
    """

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM conversation_history")
        await db.commit()
        return cursor.rowcount


async def get_statistics() -> Dict[str, Any]:
    """
    Get database statistics

    Returns:
        Dictionary with statistics
    """

    async with aiosqlite.connect(DB_PATH) as db:
        # Total conversations
        cursor = await db.execute("SELECT COUNT(*) FROM conversation_history")
        total = (await cursor.fetchone())[0]

        # Count by mode
        cursor = await db.execute("""
            SELECT mode, COUNT(*) as count
            FROM conversation_history
            GROUP BY mode
        """)
        mode_counts = {row[0]: row[1] for row in await cursor.fetchall()}

        return {
            "total": total,
            "by_mode": mode_counts
        }


# ============================================
#  RAG Document Management Functions
# ============================================

async def save_rag_document(
    filename: str,
    saved_filename: str,
    filepath: str,
    file_type: str,
    file_size: int,
    file_hash: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Save RAG document metadata to database

    Returns:
        Document ID
    """
    import json

    timestamp = datetime.now().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO rag_documents
            (filename, saved_filename, filepath, file_type, file_size, file_hash,
             upload_timestamp, processing_status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (filename, saved_filename, filepath, file_type, file_size, file_hash,
             timestamp, json.dumps(metadata) if metadata else None)
        )
        await db.commit()
        return cursor.lastrowid


async def update_rag_document_status(
    doc_id: int,
    status: str,
    num_chunks: Optional[int] = None,
    vector_store_ids: Optional[List[str]] = None
) -> bool:
    """
    Update RAG document processing status

    Args:
        doc_id: Document ID
        status: Status (pending/processing/completed/error)
        num_chunks: Number of chunks created
        vector_store_ids: List of vector store IDs

    Returns:
        True if updated
    """
    import json

    async with aiosqlite.connect(DB_PATH) as db:
        if num_chunks is not None and vector_store_ids is not None:
            cursor = await db.execute(
                """
                UPDATE rag_documents
                SET processing_status = ?, num_chunks = ?, vector_store_ids = ?
                WHERE id = ?
                """,
                (status, num_chunks, json.dumps(vector_store_ids), doc_id)
            )
        else:
            cursor = await db.execute(
                """
                UPDATE rag_documents
                SET processing_status = ?
                WHERE id = ?
                """,
                (status, doc_id)
            )

        await db.commit()
        return cursor.rowcount > 0


async def update_rag_document(
    doc_id: int,
    processing_status: Optional[str] = None,
    num_chunks: Optional[int] = None,
    vector_store_ids: Optional[List[str]] = None
) -> bool:
    """
    Update RAG document with processing results

    Args:
        doc_id: Document ID
        processing_status: Processing status
        num_chunks: Number of chunks
        vector_store_ids: Vector store IDs

    Returns:
        True if updated
    """
    import json

    async with aiosqlite.connect(DB_PATH) as db:
        updates = []
        values = []

        if processing_status is not None:
            updates.append("processing_status = ?")
            values.append(processing_status)

        if num_chunks is not None:
            updates.append("num_chunks = ?")
            values.append(num_chunks)

        if vector_store_ids is not None:
            updates.append("vector_store_ids = ?")
            values.append(json.dumps(vector_store_ids))

        if not updates:
            return False

        values.append(doc_id)
        query = f"UPDATE rag_documents SET {', '.join(updates)} WHERE id = ?"

        cursor = await db.execute(query, values)
        await db.commit()
        return cursor.rowcount > 0


async def get_rag_documents(limit: int = 100) -> List[Dict[str, Any]]:
    """Get all RAG documents"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM rag_documents
            ORDER BY upload_timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_rag_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    """Get RAG document by ID"""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM rag_documents WHERE id = ?",
            (doc_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_rag_document(doc_id: int) -> bool:
    """Delete RAG document from database"""

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM rag_documents WHERE id = ?",
            (doc_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_rag_statistics() -> Dict[str, Any]:
    """Get RAG document statistics"""

    async with aiosqlite.connect(DB_PATH) as db:
        # Total documents
        cursor = await db.execute("SELECT COUNT(*) FROM rag_documents")
        total = (await cursor.fetchone())[0]

        # Count by status
        cursor = await db.execute("""
            SELECT processing_status, COUNT(*) as count
            FROM rag_documents
            GROUP BY processing_status
        """)
        status_counts = {row[0]: row[1] for row in await cursor.fetchall()}

        # Total chunks
        cursor = await db.execute("SELECT SUM(num_chunks) FROM rag_documents")
        total_chunks = (await cursor.fetchone())[0] or 0

        # Total size
        cursor = await db.execute("SELECT SUM(file_size) FROM rag_documents")
        total_size = (await cursor.fetchone())[0] or 0

        return {
            "total_documents": total,
            "by_status": status_counts,
            "total_chunks": total_chunks,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
