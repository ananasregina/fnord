"""
Pytest configuration and shared fixtures for fnord tracker tests.

Testing fnords is sacred work. They demand verification!

PostgreSQL + pgvector + async setup
"""

import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from fnord.database import init_db, get_pool
from fnord.models import FnordSighting
from fnord.config import Config
from fnord.embeddings import EmbeddingService


@pytest.fixture(scope="session")
async def pool():
    """
    Create a test PostgreSQL connection pool.

    Yields:
        asyncpg.Pool: Test connection pool
    """
    pool = await get_pool()
    yield pool
    await pool.close()


@pytest.fixture
async def initialized_pool(pool):
    """
    Fixture providing an initialized database with schema.

    The fnords are ready to be tested!

    Yields:
        pool: Initialized connection pool
    """
    async with pool.acquire() as conn:
        await init_db()

    yield pool


@pytest.fixture
def mock_config(monkeypatch) -> Config:
    """
    Mock configuration for testing.

    Args:
        monkeypatch: pytest fixture for patching environment

    Returns:
        Config: Test configuration with mocked environment
    """
    # Set test database name
    monkeypatch.setenv("FNORD_DB_NAME", "test_fnord")
    monkeypatch.setenv("FNORD_DB_HOST", "localhost")
    monkeypatch.setenv("FNORD_DB_PORT", "5432")
    monkeypatch.setenv("FNORD_DB_USER", "test_user")
    monkeypatch.setenv("FNORD_DB_PASSWORD", "test_password")

    # Mock LM Studio config
    monkeypatch.setenv("EMBEDDING_URL", "http://localhost:9999/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-model")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "768")

    return Config()


@pytest.fixture
async def clean_pool(pool):
    """
    Clean test database and recreate.

    Yields:
        pool: Clean connection pool
    """
    async with pool.acquire() as conn:
        # Drop all tables
        await conn.execute("DROP TABLE IF EXISTS fnords CASCADE")
        await conn.execute("DROP TABLE IF EXISTS test_table CASCADE")

    yield pool

    # Reinitialize
    await init_db()


@pytest.fixture
async def sample_fnord():
    """
    Fixture providing a sample fnord sighting.

    A standard fnord for testing purposes.

    Yields:
        FnordSighting: Sample fnord
    """
    yield FnordSighting(
        when="2026-01-07T14:23:00Z",
        where_place_name="Seattle, WA",
        source="News Article",
        summary="Found fnord hidden in tech news article",
        notes={"url": "https://example.com", "author": "Unknown"},
    )


@pytest.fixture
async def ingested_sample_fnord(sample_fnord, pool):
    """
    Fixture providing an ingested fnord.

    Yields:
        FnordSighting: Ingested fnord with ID
    """
    result = await ingested_fnord.fnord(sample_fnord)
    yield result


async def ingested_fnord(sample_fnord, pool):
    """
    Helper fixture - ingest a fnord into database.

    Args:
        sample_fnord: The fnord to ingest
        pool: Connection pool

    Returns:
        FnordSighting: The ingested fnord with ID
    """
    from fnord.database import ingest_fnord as ingest_fnord_fn

    return await ingest_fnord_fn(sample_fnord)


@pytest.fixture
def multiple_sample_fnords() -> list[FnordSighting]:
    """
    Fixture providing multiple sample fnord sightings.

    A collection of fnords for testing.

    Returns:
        list[FnordSighting]: List of sample fnords
    """
    return [
        FnordSighting(
            when="2026-01-07T14:23:00Z",
            where_place_name="Seattle, WA",
            source="News Article",
            summary="Found fnord hidden in tech news article",
            notes={"url": "https://example.com"},
        ),
        FnordSighting(
            when="2026-01-06T09:15:00Z",
            where_place_name="Golden Gate Park, SF",
            source="Walk",
            summary="Saw fnord graffiti on park bench",
            notes={"weather": "sunny"},
        ),
        FnordSighting(
            when="2026-01-05T22:30:00Z",
            source="Code",
            summary="Debug log contained word fnord",
            notes={"file": "app.py", "line": 42},
        ),
        FnordSighting(
            when="2026-01-04T16:45:00Z",
            where_place_name="New York, NY",
            source="Dream",
            summary="Dreamed of fnords in a coffee shop",
        ),
        FnordSighting(
            when="2026-01-03T11:00:00Z",
            source="Book",
            summary="Found fnord reference in Discordian text",
            notes={"book": "Principia Discordia", "page": 23},
        ),
    ]


@pytest.fixture
async def ingested_multiple_fnords(multiple_sample_fnords, pool):
    """
    Fixture providing multiple ingested fnords.

    Yields:
        list[FnordSighting]: List of ingested fnords with IDs
    """
    results = []
    for fnord in multiple_sample_fnords:
        result = await ingested_fnord(fnord, pool)
        results.append(result)

    yield results
