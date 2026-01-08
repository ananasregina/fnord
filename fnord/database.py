"""
Fnord Database Module

The fnords must be stored somewhere. SQLite is their sacred vault.

This module handles all database operations: create, read, update, delete fnords.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager
import logging
from datetime import datetime

from fnord.config import get_config
from fnord.models import FnordSighting

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """
    Get a database connection context manager.

    The fnords demand proper connection handling.

    Yields:
        sqlite3.Connection: Database connection
    """
    config = get_config()
    db_path = config.get_db_path()

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    # Enable WAL mode for better concurrency (fnords are social creatures)
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the fnord database schema.

    Creates the fnords table if it doesn't exist.
    Adds new columns if they don't exist (for migrations).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create the sacred fnords table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fnords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                "when" TEXT NOT NULL,
                where_place_name TEXT,
                source TEXT NOT NULL,
                summary TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for common queries
        # The fnords appreciate speed
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fnords_when ON fnords("when")')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fnords_source ON fnords(source)")

        # Migration: Add logical_fallacies column if it doesn't exist
        cursor.execute("PRAGMA table_info(fnords)")
        columns = {row[1] for row in cursor.fetchall()}

        if "logical_fallacies" not in columns:
            cursor.execute("ALTER TABLE fnords ADD COLUMN logical_fallacies TEXT")
            logger.info("Added logical_fallacies column to fnords table")

        conn.commit()

        logger.debug("Database initialized. The fnords have a home now.")


def ingest_fnord(fnord: FnordSighting) -> FnordSighting:
    """
    Ingest a fnord into the database.

    Args:
        fnord: The fnord sighting to store

    Returns:
        FnordSighting: The fnord with database-assigned ID

    Raises:
        ValueError: If fnord validation fails
    """
    # Validate the fnord before storing
    errors = fnord.validate()
    if errors:
        error_msg = f"Invalid fnord: {', '.join(errors)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Convert notes to JSON string if present
        notes_json = None
        if fnord.notes:
            notes_json = json.dumps(fnord.notes)

        # Convert logical_fallacies to JSON string if present
        logical_fallacies_json = None
        if fnord.logical_fallacies:
            logical_fallacies_json = json.dumps(fnord.logical_fallacies)

        # Insert the fnord
        cursor.execute(
            """
            INSERT INTO fnords ("when", where_place_name, source, summary, notes, logical_fallacies)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                fnord.when,
                fnord.where_place_name,
                fnord.source,
                fnord.summary,
                notes_json,
                logical_fallacies_json,
            ),
        )

        # Get the assigned ID
        fnord_id = cursor.lastrowid

        conn.commit()

        logger.info(f"Fnord ingested with ID: {fnord_id} - Hail Discordia!")

        # Return the fnord with the assigned ID
        fnord.id = fnord_id
        return fnord


def query_fnord_count() -> int:
    """
    Query the total number of fnords.

    Returns:
        int: The sacred count of fnords
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM fnords")
        result = cursor.fetchone()

        count = result["count"] if result else 0

        logger.debug(f"Fnord count queried: {count}")
        return count


def get_all_fnords(limit: Optional[int] = None, offset: int = 0) -> List[FnordSighting]:
    """
    Get all fnords from the database.

    Args:
        limit: Maximum number of fnords to return (None for all)
        offset: Number of fnords to skip (for pagination)

    Returns:
        List[FnordSighting]: List of fnord sightings
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = 'SELECT * FROM fnords ORDER BY "when" DESC'

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            cursor.execute(query, (limit, offset))
        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        fnords = [_row_to_fnord(row) for row in rows]

        logger.debug(f"Retrieved {len(fnords)} fnords from database")
        return fnords


def get_fnord_by_id(fnord_id: int) -> Optional[FnordSighting]:
    """
    Get a fnord by its sacred ID.

    Args:
        fnord_id: The fnord's ID

    Returns:
        FnordSighting: The fnord, or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM fnords WHERE id = ?", (fnord_id,))
        row = cursor.fetchone()

        if row:
            return _row_to_fnord(row)
        return None


def update_fnord(fnord: FnordSighting) -> FnordSighting:
    """
    Update a fnord in the database.

    Args:
        fnord: The fnord to update (must have an ID)

    Returns:
        FnordSighting: The updated fnord

    Raises:
        ValueError: If fnord ID is None or validation fails
    """
    if fnord.id is None:
        raise ValueError("Cannot update fnord without ID (fnords need to exist first!)")

    # Validate the fnord
    errors = fnord.validate()
    if errors:
        error_msg = f"Invalid fnord: {', '.join(errors)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Convert notes to JSON string if present
        notes_json = None
        if fnord.notes:
            notes_json = json.dumps(fnord.notes)

        # Convert logical_fallacies to JSON string if present
        logical_fallacies_json = None
        if fnord.logical_fallacies:
            logical_fallacies_json = json.dumps(fnord.logical_fallacies)

        # Update the fnord
        cursor.execute(
            """
            UPDATE fnords
            SET "when" = ?, where_place_name = ?, source = ?,
                summary = ?, notes = ?, logical_fallacies = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (
                fnord.when,
                fnord.where_place_name,
                fnord.source,
                fnord.summary,
                notes_json,
                logical_fallacies_json,
                fnord.id,
            ),
        )

        conn.commit()

        logger.info(f"Fnord updated: ID {fnord.id} - The fnord has evolved!")

        return fnord


def delete_fnord(fnord_id: int) -> bool:
    """
    Delete a fnord from the database.

    Args:
        fnord_id: The fnord's ID

    Returns:
        bool: True if deleted, False if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM fnords WHERE id = ?", (fnord_id,))

        deleted = cursor.rowcount > 0

        if deleted:
            conn.commit()
            logger.info(f"Fnord deleted: ID {fnord_id} - It has vanished into the void!")
        else:
            logger.warning(f"Fnord not found for deletion: ID {fnord_id}")

        return deleted


def search_fnords(
    query: str, limit: Optional[int] = None, offset: Optional[int] = None
) -> List[FnordSighting]:
    """
    Search fnords by text query.

    Searches in summary and source fields.

    Args:
        query: Search query
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List[FnordSighting]: Matching fnords
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        sql_query = """
            SELECT * FROM fnords
            WHERE summary LIKE ? OR source LIKE ? OR where_place_name LIKE ?
            ORDER BY "when" DESC
        """

        search_pattern = f"%{query}%"

        if limit is not None:
            sql_query += " LIMIT ?"
            if offset is not None:
                sql_query += " OFFSET ?"
                cursor.execute(
                    sql_query, (search_pattern, search_pattern, search_pattern, limit, offset)
                )
            else:
                cursor.execute(sql_query, (search_pattern, search_pattern, search_pattern, limit))
        else:
            if offset is not None:
                sql_query += " OFFSET ?"
                cursor.execute(sql_query, (search_pattern, search_pattern, search_pattern, offset))
            else:
                cursor.execute(sql_query, (search_pattern, search_pattern, search_pattern))

        rows = cursor.fetchall()

        fnords = [_row_to_fnord(row) for row in rows]

        logger.debug(f"Search for '{query}' returned {len(fnords)} fnords")
        return fnords


def _row_to_fnord(row: sqlite3.Row) -> FnordSighting:
    """
    Convert a database row to a FnordSighting object.

    Args:
        row: Database row

    Returns:
        FnordSighting: The fnord object
    """
    # Parse notes JSON
    notes = None
    if row["notes"]:
        try:
            notes = json.loads(row["notes"])
        except json.JSONDecodeError:
            notes = None

    # Parse logical_fallacies JSON
    logical_fallacies = None
    try:
        logical_fallacies_data = row["logical_fallacies"]
        if logical_fallacies_data:
            parsed = json.loads(logical_fallacies_data)
            # Validate it's a list of strings
            if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                logical_fallacies = parsed
    except (KeyError, json.JSONDecodeError):
        logical_fallacies = None

    return FnordSighting(
        id=row["id"],
        when=row["when"],
        where_place_name=row["where_place_name"],
        source=row["source"],
        summary=row["summary"],
        notes=notes,
        logical_fallacies=logical_fallacies,
    )
