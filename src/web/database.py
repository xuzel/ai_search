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
