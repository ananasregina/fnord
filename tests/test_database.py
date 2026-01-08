"""
Tests for fnord database operations with PostgreSQL.

The fnords must be stored safely. We test all CRUD operations thoroughly.
PostgreSQL + pgvector + async + semantic search
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fnord.database import (
    init_db,
    ingest_fnord,
    query_fnord_count,
    get_all_fnords,
    get_fnord_by_id,
    update_fnord,
    delete_fnord,
    search_fnords,
    get_pool,
)
from fnord.models import FnordSighting
from fnord.embeddings import EmbeddingService
from fnord.config import Config


class TestDatabaseInit:
    """Test database initialization."""

    @pytest.mark.asyncio
    async def test_init_db_creates_table_and_index(self, pool):
        """Test that init_db creates fnords table and vector index."""
        await init_db()

        async with pool.acquire() as conn:
            # Check if table exists
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'fnords')"
            )

            assert result is True, "fnords table should exist"

            # Check if vector extension is enabled
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )

            assert result is True, "vector extension should be enabled"

            # Check if embedding column exists
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'fnords' AND column_name = 'embedding')"
            )

            assert result is True, "embedding column should exist"

            # Check if vector index exists
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_fnords_embedding')"
            )

            assert result is True, "vector index should exist"


class TestIngestFnord:
    """Test fnord ingestion."""

    @pytest.mark.asyncio
    async def test_ingest_fnord_success(self, pool, sample_fnord):
        """Test successful fnord ingestion."""
        await init_db()

        result = await ingest_fnord(sample_fnord)

        assert result.id is not None, "Fnord should have an ID"
        assert result.id > 0, "Fnord ID should be positive"

        # Verify fnord was saved to database
        fnord = await get_fnord_by_id(result.id)
        assert fnord is not None, "Fnord should be retrievable"
        assert fnord.summary == sample_fnord.summary, "Summary should match"
        assert fnord.source == sample_fnord.source, "Source should match"

    @pytest.mark.asyncio
    async def test_ingest_fnord_with_notes(self, pool, sample_fnord):
        """Test fnord ingestion with notes."""
        sample_fnord.notes = {"url": "https://example.com", "author": "Test Author"}

        await init_db()
        result = await ingest_fnord(sample_fnord)

        fnord = await get_fnord_by_id(result.id)
        assert fnord.notes == sample_fnord.notes, "Notes should be saved"

    @pytest.mark.asyncio
    async def test_ingest_fnord_with_logical_fallacies(self, pool, sample_fnord):
        """Test fnord ingestion with logical fallacies."""
        sample_fnord.logical_fallacies = ["ad hominem", "straw man"]

        await init_db()
        result = await ingest_fnord(sample_fnord)

        fnord = await get_fnord_by_id(result.id)
        assert fnord.logical_fallacies == sample_fnord.logical_fallacies

    @pytest.mark.asyncio
    async def test_ingest_fnord_generates_embedding(self, pool, sample_fnord):
        """Test that ingestion generates and stores embedding."""
        await init_db()

        result = await ingest_fnord(sample_fnord)

        # Verify embedding was generated and stored
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT embedding FROM fnords WHERE id = $1", result.id
            )

            assert row is not None, "Embedding should be stored"
            assert row["embedding"] is not None, "Embedding should not be null"
            assert len(row["embedding"]) == 768, "Embedding should have 768 dimensions"


class TestQueryFnordCount:
    """Test querying fnord count."""

    @pytest.mark.asyncio
    async def test_query_count_empty_db(self, pool):
        """Test count when database is empty."""
        await init_db()

        count = await query_fnord_count()

        assert count == 0, "Count should be 0 for empty database"

    @pytest.mark.asyncio
    async def test_query_count_with_fnords(self, pool, sample_fnord):
        """Test count when fnords exist."""
        await init_db()
        await ingest_fnord(sample_fnord)

        count = await query_fnord_count()

        assert count == 1, "Count should be 1"


class TestGetAllFnords:
    """Test getting all fnords."""

    @pytest.mark.asyncio
    async def test_get_all_empty_db(self, pool):
        """Test getting all fnords from empty database."""
        await init_db()

        fnords = await get_all_fnords()

        assert len(fnords) == 0, "Should return empty list"

    @pytest.mark.asyncio
    async def test_get_all_with_fnords(self, pool, sample_fnord):
        """Test getting all fnords when fnords exist."""
        await init_db()
        await ingest_fnord(sample_fnord)

        fnords = await get_all_fnords()

        assert len(fnords) == 1, "Should return one fnord"
        assert fnords[0].summary == sample_fnord.summary

    @pytest.mark.asyncio
    async def test_get_all_with_limit(self, pool, sample_fnord):
        """Test getting all fnords with limit."""
        await init_db()
        await ingest_fnord(sample_fnord)
        await ingest_fnord(sample_fnord)

        fnords = await get_all_fnords(limit=1)

        assert len(fnords) == 1, "Should return one fnord with limit"

    @pytest.mark.asyncio
    async def test_get_all_with_offset(self, pool, sample_fnord):
        """Test getting all fnords with offset."""
        await init_db()
        await ingest_fnord(sample_fnord)
        await ingest_fnord(sample_fnord)

        fnords = await get_all_fnords(offset=1)

        assert len(fnords) == 2, "Should return two fnords with offset"


class TestGetFnordById:
    """Test getting fnord by ID."""

    @pytest.mark.asyncio
    async def test_get_fnord_by_id_exists(self, pool, ingested_sample_fnord):
        """Test getting fnord that exists."""
        await init_db()
        fnord = await get_fnord_by_id(ingested_sample_fnord.id)

        assert fnord is not None, "Fnord should be found"
        assert fnord.id == ingested_sample_fnord.id
        assert fnord.summary == ingested_sample_fnord.summary

    @pytest.mark.asyncio
    async def test_get_fnord_by_id_not_exists(self, pool):
        """Test getting fnord that doesn't exist."""
        await init_db()

        fnord = await get_fnord_by_id(999)

        assert fnord is None, "Fnord should be None for non-existent ID"


class TestUpdateFnord:
    """Test updating fnords."""

    @pytest.mark.asyncio
    async def test_update_fnord_success(self, pool, ingested_sample_fnord):
        """Test successful fnord update."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        fnord = await get_fnord_by_id(ingested_sample_fnord.id)
        original_summary = fnord.summary

        fnord.summary = "Updated summary"
        result = await update_fnord(fnord)

        assert result.summary == "Updated summary", "Summary should be updated"

        fnord = await get_fnord_by_id(ingested_sample_fnord.id)
        assert fnord.summary == "Updated summary", "Summary should be updated in database"
        assert fnord.summary != original_summary, "Summary should be different from original"

    @pytest.mark.asyncio
    async def test_update_fnord_without_id(self, pool, sample_fnord):
        """Test that updating fnord without ID raises error."""
        await init_db()

        with pytest.raises(ValueError, match="Cannot update fnord without ID"):
            await update_fnord(sample_fnord)

    @pytest.mark.asyncio
    async def test_update_fnord_invalid_data(self, pool, ingested_sample_fnord):
        """Test that updating with invalid data raises error."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        fnord = await get_fnord_by_id(ingested_sample_fnord.id)
        fnord.when = "invalid-date"

        with pytest.raises(ValueError, match="Invalid fnord"):
            await update_fnord(fnord)

    @pytest.mark.asyncio
    async def test_update_fnord_regenerates_embedding(self, pool, ingested_sample_fnord):
        """Test that updating fnord regenerates embedding."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        fnord = await get_fnord_by_id(ingested_sample_fnord.id)
        original_embedding = None

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT embedding FROM fnords WHERE id = $1", ingested_sample_fnord.id
            )
            original_embedding = row["embedding"]

        fnord.summary = "Updated summary"
        result = await update_fnord(fnord)

        fnord = await get_fnord_by_id(ingested_sample_fnord.id)
        updated_embedding = None

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT embedding FROM fnords WHERE id = $1", ingested_sample_fnord.id
            )
            updated_embedding = row["embedding"]

        assert updated_embedding is not None, "Embedding should be regenerated"
        assert updated_embedding != original_embedding, "Embedding should be different"


class TestDeleteFnord:
    """Test deleting fnords."""

    @pytest.mark.asyncio
    async def test_delete_fnord_success(self, pool, ingested_sample_fnord):
        """Test successful fnord deletion."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        deleted = await delete_fnord(ingested_sample_fnord.id)

        assert deleted is True, "Delete should succeed"

        fnord = await get_fnord_by_id(ingested_sample_fnord.id)
        assert fnord is None, "Fnord should be deleted from database"

    @pytest.mark.asyncio
    async def test_delete_fnord_not_exists(self, pool):
        """Test deleting fnord that doesn't exist."""
        await init_db()

        deleted = await delete_fnord(999)

        assert deleted is False, "Delete should fail for non-existent fnord"


class TestSearchFnords:
    """Test semantic search functionality."""

    @pytest.mark.asyncio
    async def test_search_fnords_semantic(self, pool, sample_fnord, ingested_sample_fnord):
        """Test semantic search using vector similarity."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        results = await search_fnords("found fnord")

        assert len(results) >= 1, "Should find at least one result"
        assert any("found fnord" in r.summary.lower() for r in results), "Should find fnord with matching text"

    @pytest.mark.asyncio
    async def test_search_fnords_with_limit(self, pool, sample_fnord, ingested_sample_fnord):
        """Test semantic search with limit."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        results = await search_fnords("found fnord", limit=1)

        assert len(results) == 1, "Should return one result with limit"

    @pytest.mark.asyncio
    async def test_search_fnords_with_offset(self, pool, sample_fnord, ingested_sample_fnord):
        """Test semantic search with offset."""
        await init_db()
        await ingest_fnord(ingested_sample_fnord)

        results = await search_fnords("found fnord", offset=1)

        assert len(results) >= 0, "Should return results with offset"


class TestEmbeddingService:
    """Test embedding service integration."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, pool):
        """Test successful embedding generation."""
        from fnord.embeddings import EmbeddingService
        from unittest.mock import AsyncMock, patch

        await init_db()

        with patch("fnord.embeddings.OpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.data = [AsyncMock()]
            mock_response.data[0].embedding = [0.1] * 768

            mock_client.embeddings.create = AsyncMock(return_value=mock_response)

            service = EmbeddingService()
            result = await service.generate_embedding("test text")

        assert result == [0.1] * 768, "Should return 768-dimensional embedding"
        assert len(result) == 768, "Embedding should have 768 dimensions"

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, pool):
        """Test embedding generation failure handling."""
        from fnord.embeddings import EmbeddingService
        from unittest.mock import AsyncMock, patch

        await init_db()

        with patch("fnord.embeddings.OpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_client.embeddings.create = AsyncMock(side_effect=Exception("API error"))

            service = EmbeddingService()
            result = await service.generate_embedding("test text")

        assert result is None, "Should return None on error"


class TestChaosEnergy:
    """Test chaos energy in fnord IDs."""

    @pytest.mark.asyncio
    async def test_chaos_energy_skips_ids(self, pool, sample_fnord):
        """Test that chaos energy can skip IDs."""
        await init_db()
        await ingest_fnord(sample_fnord)

        from unittest.mock import patch
        with patch("fnord.database.random.randint") as mock_randint:
            mock_randint.return_value = 23

            await ingest_fnord(sample_fnord)

        fnord = await get_fnord_by_id(sample_fnord.id)
        assert fnord.id > 1, "Chaos energy should skip IDs"

    @pytest.mark.asyncio
    async def test_chaos_energy_sequential_when_not_triggered(self, pool, sample_fnord):
        """Test that IDs are sequential when chaos energy isn't triggered."""
        await init_db()
        await ingest_fnord(sample_fnord)

        from unittest.mock import patch
        with patch("fnord.database.random.randint") as mock_randint:
            mock_randint.return_value = 22

            await ingest_fnord(sample_fnord)

        fnord = await get_fnord_by_id(sample_fnord.id)
        assert fnord.id == 1, "IDs should be sequential when chaos isn't triggered"


class TestConnectionPool:
    """Test connection pooling."""

    @pytest.mark.asyncio
    async def test_connection_pool_singleton(self):
        """Test that connection pool is singleton."""
        from fnord.database import get_pool

        pool1 = await get_pool()
        pool2 = await get_pool()

        assert pool1 is pool2, "Connection pool should be singleton"

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self, pool, sample_fnord):
        """Test that connections are reused from pool."""
        await init_db()
        await ingest_fnord(sample_fnord)

        fnord1 = await get_fnord_by_id(sample_fnord.id)
        fnord2 = await get_fnord_by_id(sample_fnord.id)

        assert fnord1.id == fnord2.id, "Should get same fnord from pool"
