"""
Tests for fnord database operations.

The fnords must be stored safely. We test all CRUD operations thoroughly.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple

from fnord.database import (
    init_db,
    ingest_fnord,
    query_fnord_count,
    get_all_fnords,
    get_fnord_by_id,
    update_fnord,
    delete_fnord,
    search_fnords,
)
from fnord.models import FnordSighting


class TestDatabaseInit:
    """Test database initialization."""

    def test_init_db_creates_table(self, initialized_db: Path, db_connection):
        """Test that init_db creates the fnords table."""
        cursor = db_connection.cursor()

        # Check that table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fnords'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["name"] == "fnords"

    def test_init_db_creates_indexes(self, initialized_db: Path, db_connection):
        """Test that init_db creates indexes."""
        cursor = db_connection.cursor()

        # Check that indexes exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='fnords'"
        )
        indexes = cursor.fetchall()

        index_names = [idx["name"] for idx in indexes]

        assert "idx_fnords_when" in index_names
        assert "idx_fnords_source" in index_names


class TestIngestFnord:
    """Test fnord ingestion."""

    def test_ingest_fnord_success(self, initialized_db: Path, sample_fnord):
        """Test successful fnord ingestion."""
        result = ingest_fnord(sample_fnord)

        assert result.id is not None
        assert result.id == 1  # First fnord gets ID 1

    def test_ingest_fnord_saves_to_db(self, initialized_db: Path, sample_fnord, db_connection):
        """Test that fnord is saved to database."""
        ingest_fnord(sample_fnord)

        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM fnords WHERE id = 1")
        row = cursor.fetchone()

        assert row is not None
        assert row["when"] == sample_fnord.when
        assert row["source"] == sample_fnord.source
        assert row["summary"] == sample_fnord.summary

    def test_ingest_fnord_with_notes(self, initialized_db: Path, db_connection):
        """Test fnord with notes is saved correctly."""
        notes = {"url": "https://example.com", "author": "Test Author"}
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
            notes=notes,
        )

        result = ingest_fnord(fnord)

        cursor = db_connection.cursor()
        cursor.execute("SELECT notes FROM fnords WHERE id = ?", (result.id,))
        row = cursor.fetchone()

        assert row["notes"] == '{"url": "https://example.com", "author": "Test Author"}'

    def test_ingest_fnord_invalid_when(self, initialized_db: Path):
        """Test that fnord with invalid 'when' fails validation."""
        fnord = FnordSighting(
            when="not-a-date",
            source="News",
            summary="Found fnord",
        )

        with pytest.raises(ValueError, match="Invalid fnord"):
            ingest_fnord(fnord)

    def test_ingest_fnord_missing_source(self, initialized_db: Path):
        """Test that fnord with missing 'source' fails validation."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="",
            summary="Found fnord",
        )

        with pytest.raises(ValueError, match="Invalid fnord"):
            ingest_fnord(fnord)

    def test_ingest_multiple_fnords(self, initialized_db: Path, multiple_fnords):
        """Test ingesting multiple fnords."""
        results = [ingest_fnord(fnord) for fnord in multiple_fnords]

        assert len(results) == 5
        assert results[0].id == 1
        assert results[1].id == 2
        assert results[2].id == 3
        assert results[3].id == 4
        assert results[4].id == 5


class TestQueryFnordCount:
    """Test querying fnord count."""

    def test_query_count_empty_db(self, initialized_db: Path):
        """Test count when database is empty."""
        count = query_fnord_count()

        assert count == 0

    def test_query_count_one_fnord(self, initialized_db: Path, ingested_fnord):
        """Test count with one fnord."""
        count = query_fnord_count()

        assert count == 1

    def test_query_count_multiple_fnords(self, initialized_db: Path, ingested_multiple_fnords):
        """Test count with multiple fnords."""
        count = query_fnord_count()

        assert count == 5

    def test_query_count_sacred_number(self, initialized_db: Path):
        """Test the sacred number 23."""
        # Ingest 23 fnords
        for i in range(23):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="Test",
                summary=f"Fnord #{i+1}",
            )
            ingest_fnord(fnord)

        count = query_fnord_count()

        assert count == 23  # All hail Eris!


class TestGetAllFnords:
    """Test getting all fnords."""

    def test_get_all_empty_db(self, initialized_db: Path):
        """Test getting all fnords from empty database."""
        fnords = get_all_fnords()

        assert len(fnords) == 0

    def test_get_all_one_fnord(self, initialized_db: Path, ingested_fnord):
        """Test getting all fnords with one fnord."""
        fnords = get_all_fnords()

        assert len(fnords) == 1
        assert fnords[0].id == ingested_fnord.id
        assert fnords[0].summary == ingested_fnord.summary

    def test_get_all_multiple_fnords(self, initialized_db: Path, ingested_multiple_fnords):
        """Test getting all fnords with multiple fnords."""
        fnords = get_all_fnords()

        assert len(fnords) == 5

        # Check that all are returned
        ids = [f.id for f in fnords]
        assert all(id_val is not None for id_val in ids)

    def test_get_all_with_limit(self, initialized_db: Path, ingested_multiple_fnords):
        """Test getting fnords with limit."""
        fnords = get_all_fnords(limit=2)

        assert len(fnords) == 2

    def test_get_all_with_offset(self, initialized_db: Path, ingested_multiple_fnords):
        """Test getting fnords with offset."""
        fnords = get_all_fnords(limit=2, offset=1)

        assert len(fnords) == 2

    def test_get_all_ordered_by_when_desc(self, initialized_db: Path):
        """Test that fnords are ordered by 'when' descending."""
        # Create fnords with different times
        fnord1 = FnordSighting(
            when="2026-01-07T10:00:00Z",
            source="Test",
            summary="First fnord",
        )
        fnord2 = FnordSighting(
            when="2026-01-07T14:00:00Z",
            source="Test",
            summary="Second fnord",
        )
        fnord3 = FnordSighting(
            when="2026-01-07T12:00:00Z",
            source="Test",
            summary="Third fnord",
        )

        ingest_fnord(fnord1)
        ingest_fnord(fnord2)
        ingest_fnord(fnord3)

        fnords = get_all_fnords()

        # Should be ordered by when descending
        assert fnords[0].when == "2026-01-07T14:00:00Z"
        assert fnords[1].when == "2026-01-07T12:00:00Z"
        assert fnords[2].when == "2026-01-07T10:00:00Z"


class TestGetFnordById:
    """Test getting fnord by ID."""

    def test_get_fnord_by_id_exists(self, initialized_db: Path, ingested_fnord):
        """Test getting fnord that exists."""
        fnord = get_fnord_by_id(ingested_fnord.id)

        assert fnord is not None
        assert fnord.id == ingested_fnord.id
        assert fnord.summary == ingested_fnord.summary

    def test_get_fnord_by_id_not_exists(self, initialized_db: Path):
        """Test getting fnord that doesn't exist."""
        fnord = get_fnord_by_id(999)

        assert fnord is None


class TestUpdateFnord:
    """Test updating fnords."""

    def test_update_fnord_success(self, initialized_db: Path, ingested_fnord):
        """Test successful fnord update."""
        ingested_fnord.summary = "Updated fnord summary"
        ingested_fnord.source = "Updated Source"

        result = update_fnord(ingested_fnord)

        assert result.summary == "Updated fnord summary"
        assert result.source == "Updated Source"

        # Verify in database
        fnord = get_fnord_by_id(ingested_fnord.id)
        assert fnord.summary == "Updated fnord summary"

    def test_update_fnord_without_id(self, initialized_db: Path):
        """Test that updating fnord without ID fails."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
        )

        with pytest.raises(ValueError, match="Cannot update fnord without ID"):
            update_fnord(fnord)

    def test_update_fnord_invalid_data(self, initialized_db: Path, ingested_fnord):
        """Test that updating with invalid data fails."""
        ingested_fnord.when = "invalid-date"

        with pytest.raises(ValueError, match="Invalid fnord"):
            update_fnord(ingested_fnord)


class TestDeleteFnord:
    """Test deleting fnords."""

    def test_delete_fnord_success(self, initialized_db: Path, ingested_fnord):
        """Test successful fnord deletion."""
        result = delete_fnord(ingested_fnord.id)

        assert result is True

        # Verify fnord is gone
        fnord = get_fnord_by_id(ingested_fnord.id)
        assert fnord is None

    def test_delete_fnord_not_exists(self, initialized_db: Path):
        """Test deleting fnord that doesn't exist."""
        result = delete_fnord(999)

        assert result is False

    def test_delete_fnord_reduces_count(self, initialized_db: Path, ingested_fnord):
        """Test that deleting reduces count."""
        initial_count = query_fnord_count()
        assert initial_count == 1

        delete_fnord(ingested_fnord.id)

        final_count = query_fnord_count()
        assert final_count == 0


class TestSearchFnords:
    """Test searching fnords."""

    def test_search_fnords_by_summary(self, initialized_db: Path, ingested_multiple_fnords):
        """Test searching by summary."""
        fnords = search_fnords("graffiti")

        assert len(fnords) == 1
        assert "graffiti" in fnords[0].summary.lower()

    def test_search_fnords_by_source(self, initialized_db: Path, ingested_multiple_fnords):
        """Test searching by source."""
        fnords = search_fnords("News")

        assert len(fnords) == 1
        assert fnords[0].source == "News Article"

    def test_search_fnords_by_place(self, initialized_db: Path, ingested_multiple_fnords):
        """Test searching by place name."""
        fnords = search_fnords("Seattle")

        assert len(fnords) == 1
        assert "Seattle" in fnords[0].where_place_name

    def test_search_fnords_no_results(self, initialized_db: Path, ingested_multiple_fnords):
        """Test search with no results."""
        fnords = search_fnords("nonexistent fnord")

        assert len(fnords) == 0

    def test_search_fnords_with_limit(self, initialized_db: Path, ingested_multiple_fnords):
        """Test search with limit."""
        fnords = search_fnords("fnord", limit=2)

        assert len(fnords) <= 2

    def test_search_fnords_case_insensitive(self, initialized_db: Path, ingested_multiple_fnords):
        """Test that search is case-insensitive."""
        fnords_lower = search_fnords("news")
        fnords_upper = search_fnords("NEWS")
        fnords_mixed = search_fnords("NeWs")

        assert len(fnords_lower) == len(fnords_upper) == len(fnords_mixed)
