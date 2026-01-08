"""
Fnord Database Module

The fnords are stored in PostgreSQL with pgvector for semantic search.
Chaos energy still applies - 1/23 chance to skip IDs!
"""

import asyncpg
from pgvector.asyncpg import register_vector
import json
import logging
from typing import Optional, List
from datetime import datetime
import random

from fnord.config import get_config
from fnord.models import FnordSighting
from fnord.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

# Chaos energy: 1/23 chance to skip IDs
CHAOS_PROBABILITY = 23
CHAOS_MIN_SKIP = 1
CHAOS_MAX_SKIP = 23

# Global connection pool and embedding service
_pool = None
_embedding_service = None


async def get_pool():
    """
    Get or create async PostgreSQL connection pool.

    Returns:
        asyncpg.Pool: Connection pool
    """
    global _pool
    if _pool is None:
        config = get_config()
        _pool = await asyncpg.create_pool(config.get_postgres_uri())
        logger.debug("PostgreSQL connection pool created")
    return _pool


async def close_pool():
    """
    Close PostgreSQL connection pool.

    Must be called when done to prevent event loop issues.
    """
    global _pool
    if _pool is not None:
        try:
            await _pool.close()
        except Exception:
            pass
        _pool = None
        logger.debug("PostgreSQL connection pool closed")


async def get_embedding_service():
    """
    Get or create embedding service.

    Returns:
        EmbeddingService: Embedding service instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def init_db():
    """
    Initialize PostgreSQL database schema with pgvector.

    Creates fnords table, embedding column, and vector index.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

    pool = await get_pool()

    async with pool.acquire() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await register_vector(conn)
        logger.info("pgvector extension enabled")

        # Create fnords table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fnords (
                id SERIAL PRIMARY KEY,
                "when" TIMESTAMP NOT NULL,
                where_place_name TEXT,
                source TEXT NOT NULL,
                summary TEXT NOT NULL,
                notes JSONB,
                logical_fallacies JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Add embedding column if not exists
        config = get_config()
        dim = config.get_embedding_config()["dimension"]
        await conn.execute(f"""
            ALTER TABLE fnords
            ADD COLUMN IF NOT EXISTS embedding vector({dim})
        """)
        logger.debug(f"Embedding column added ({dim} dimensions)")

        # Create IVFFlat index for fast vector similarity search
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fnords_embedding
            ON fnords USING ivfflat (embedding vector_cosine_ops)
        """)
        logger.debug("Vector index created")

        # Create other indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_fnords_when ON fnords("when")')
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_fnords_source ON fnords(source)")

    logger.info("PostgreSQL database initialized. The fnords have a new home!")


async def ingest_fnord(fnord: FnordSighting) -> FnordSighting:
    """
    Ingest a fnord with semantic embedding.

    Args:
        fnord: The fnord sighting to store

    Returns:
        FnordSighting: The fnord with database-assigned ID

    Raises:
        ValueError: If fnord validation fails
    """
    # Validate the fnord
    errors = fnord.validate()
    if errors:
        error_msg = f"Invalid fnord: {', '.join(errors)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    pool = await get_pool()
    emb_service = await get_embedding_service()

    # Prepare text for embedding (combine searchable fields)
    search_text = f"{fnord.summary} {fnord.source}"
    if fnord.where_place_name:
        search_text += f" {fnord.where_place_name}"

    # Generate embedding
    embedding = await emb_service.generate_embedding(search_text)

    if embedding is None:
        raise ValueError("Failed to generate embedding for fnord")

    async with pool.acquire() as conn:
        # Check for chaos energy: 1/23 chance to skip IDs
        if random.randint(1, CHAOS_PROBABILITY) == CHAOS_PROBABILITY:
            # Chaos! Skip a random number of IDs
            skip_amount = random.randint(CHAOS_MIN_SKIP, CHAOS_MAX_SKIP)

            # Get current max ID
            result = await conn.fetchval("SELECT COALESCE(MAX(id), 0) FROM fnords")
            max_id = result

            # Calculate the sacred gap ID
            target_id = max_id + 1 + skip_amount

            # Insert with explicit ID (chaos mode!)
            # Convert datetime string to datetime object (offset-naive)
            when_str = fnord.when.replace("Z", "+00:00")
            when_dt = datetime.fromisoformat(when_str).replace(tzinfo=None)
            await conn.execute("""
                INSERT INTO fnords (id, "when", where_place_name, source, summary, notes, logical_fallacies, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, target_id, when_dt, fnord.where_place_name, fnord.source, fnord.summary,
                json.dumps(fnord.notes) if fnord.notes else None,
                json.dumps(fnord.logical_fallacies) if fnord.logical_fallacies else None, embedding)

            fnord_id = target_id
            logger.info(f"Chaos energy! Skipped to ID: {fnord_id}")
        else:
            # Normal insertion - let PostgreSQL assign the next ID
            # Convert datetime string to datetime object (offset-naive)
            when_str = fnord.when.replace("Z", "+00:00")
            when_dt = datetime.fromisoformat(when_str).replace(tzinfo=None)
            fnord_id = await conn.fetchval("""
                INSERT INTO fnords ("when", where_place_name, source, summary, notes, logical_fallacies, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, when_dt, fnord.where_place_name, fnord.source, fnord.summary,
                json.dumps(fnord.notes) if fnord.notes else None,
                json.dumps(fnord.logical_fallacies) if fnord.logical_fallacies else None, embedding)

        logger.info(f"Fnord ingested with ID: {fnord_id} - Hail Discordia!")

        # Return the fnord with the assigned ID
        fnord.id = fnord_id
        return fnord


async def query_fnord_count() -> int:
    """
    Query the total number of fnords.

    Returns:
        int: The sacred count of fnords
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT COUNT(*) FROM fnords")
        count = result if result is not None else 0

        #logger.debug(f"Fnord count queried: {count}")
        return count


async def get_all_fnords(limit: Optional[int] = None, offset: int = 0) -> List[FnordSighting]:
    """
    Get all fnords from the database with pagination.

    Args:
        limit: Maximum number of fnords to return
        offset: Number of fnords to skip

    Returns:
        List[FnordSighting]: List of fnord sightings
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        query = 'SELECT * FROM fnords ORDER BY created_at DESC'

        if limit is not None:
            query += " LIMIT $1 OFFSET $2"
            rows = await conn.fetch(query, limit, offset)
        else:
            query += " OFFSET $1"
            rows = await conn.fetch(query, offset)

        fnords = [_row_to_fnord(row) for row in rows]

        logger.debug(f"Retrieved {len(fnords)} fnords from database")
        return fnords


async def get_fnord_by_id(fnord_id: int) -> Optional[FnordSighting]:
    """
    Get a fnord by its sacred ID.

    Args:
        fnord_id: The fnord's ID

    Returns:
        FnordSighting: The fnord, or None if not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM fnords WHERE id = $1", fnord_id)

        if row:
            return _row_to_fnord(row)
        return None


async def update_fnord(fnord: FnordSighting) -> FnordSighting:
    """
    Update a fnord in the database with new embedding.

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

    pool = await get_pool()
    emb_service = await get_embedding_service()

    # Prepare text for embedding
    search_text = f"{fnord.summary} {fnord.source}"
    if fnord.where_place_name:
        search_text += f" {fnord.where_place_name}"

    # Generate new embedding
    embedding = await emb_service.generate_embedding(search_text)

    if embedding is None:
        raise ValueError("Failed to generate embedding for fnord")

    async with pool.acquire() as conn:
        # Update the fnord
        # Convert datetime string to datetime object (offset-naive)
        when_str = fnord.when.replace("Z", "+00:00")
        when_dt = datetime.fromisoformat(when_str).replace(tzinfo=None)
        await conn.execute("""
            UPDATE fnords
            SET "when" = $1, where_place_name = $2, source = $3, summary = $4,
                notes = $5, logical_fallacies = $6, embedding = $7, updated_at = NOW()
            WHERE id = $8
        """, when_dt, fnord.where_place_name, fnord.source, fnord.summary,
            json.dumps(fnord.notes) if fnord.notes else None,
            json.dumps(fnord.logical_fallacies) if fnord.logical_fallacies else None, embedding, fnord.id)

        logger.info(f"Fnord updated: ID {fnord.id} - The fnord has evolved!")

        return fnord


async def delete_fnord(fnord_id: int) -> bool:
    """
    Delete a fnord from the database.

    Args:
        fnord_id: The fnord's ID

    Returns:
        bool: True if deleted, False if not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM fnords WHERE id = $1", fnord_id)
        deleted = result == "DELETE 1"

        if deleted:
            logger.info(f"Fnord deleted: ID {fnord_id} - It has vanished into the void!")
        else:
            logger.warning(f"Fnord not found for deletion: ID {fnord_id}")

        return deleted


async def search_fnords(
    query: str,
    limit: Optional[int] = None,
    offset: int = 0,
    max_distance: float = 0.5,
) -> List[FnordSighting]:
    """
    Semantic search using vector similarity.

    Searches fnords by embedding similarity instead of exact text.
    The fnords understand meaning now!

    Args:
        query: Search query
        limit: Maximum number of results
        offset: Number of results to skip
        max_distance: Maximum cosine distance for results (0.0 = identical, 2.0 = opposite)

    Returns:
        List[FnordSighting]: Matching fnords
    """
    pool = await get_pool()
    emb_service = await get_embedding_service()

    # Generate embedding for query
    query_embedding = await emb_service.generate_embedding(query)

    if query_embedding is None:
        logger.error(f"Failed to generate embedding for query: {query}")
        return []

    async with pool.acquire() as conn:
        # Register vector codec for this connection
        await register_vector(conn)

        # Vector similarity search using cosine distance (<=>)
        # Filter by max_distance to only return sufficiently similar results
        sql = """
            SELECT *, embedding <=> $1 AS distance
            FROM fnords
            WHERE embedding <=> $1 <= $2
            ORDER BY distance
        """

        if limit is not None:
            sql += " LIMIT $3 OFFSET $4"
            rows = await conn.fetch(sql, query_embedding, max_distance, limit, offset)
        else:
            sql += " OFFSET $3"
            rows = await conn.fetch(sql, query_embedding, max_distance, offset)

        results = [_row_to_fnord(row) for row in rows]

        logger.debug(f"Semantic search for '{query}' returned {len(results)} fnords (max_distance={max_distance})")
        return results


def _row_to_fnord(row) -> FnordSighting:
    """
    Convert a PostgreSQL row to a FnordSighting object.

    Args:
        row: Database row

    Returns:
        FnordSighting: The fnord object
    """
    return FnordSighting(
        id=row["id"],
        when=row["when"].isoformat() if row["when"] else "",
        where_place_name=row["where_place_name"],
        source=row["source"],
        summary=row["summary"],
        notes=row["notes"],
        logical_fallacies=row["logical_fallacies"],
    )
