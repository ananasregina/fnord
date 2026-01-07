"""
Pytest configuration and shared fixtures for fnord tracker tests.

Testing the fnords is sacred work. They demand verification!
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile
import os
from typing import Generator

from fnord.models import FnordSighting
from fnord.database import init_db, ingest_fnord, get_db_connection
from fnord.config import Config


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Fixture providing a temporary database path.

    The fnords need a temporary home for testing.

    Yields:
        Path: Path to temporary database file
    """
    db_path = tmp_path / "test_fnord.db"
    yield db_path

    # Cleanup happens automatically with tmp_path


@pytest.fixture
def temp_config(temp_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    """
    Fixture providing a test configuration with temporary database.

    Args:
        temp_db_path: Temporary database path
        monkeypatch: pytest fixture for patching environment

    Returns:
        Config: Test configuration
    """
    # Monkeypatch the database path
    monkeypatch.setenv("FNORD_DB_PATH", str(temp_db_path))

    # Return a new config instance
    return Config()


@pytest.fixture
def initialized_db(temp_db_path: Path) -> Generator[Path, None, None]:
    """
    Fixture providing an initialized temporary database.

    The fnords are ready to be tested!

    Yields:
        Path: Path to initialized temporary database
    """
    # Monkeypatch for this test
    old_env = os.environ.get("FNORD_DB_PATH")
    os.environ["FNORD_DB_PATH"] = str(temp_db_path)

    try:
        # Initialize the database
        init_db()

        yield temp_db_path

    finally:
        # Restore environment
        if old_env is None:
            os.environ.pop("FNORD_DB_PATH", None)
        else:
            os.environ["FNORD_DB_PATH"] = old_env

        # Cleanup database file
        if temp_db_path.exists():
            temp_db_path.unlink()

        # Cleanup WAL files
        for wal_file in temp_db_path.parent.glob(f"{temp_db_path.stem}*"):
            wal_file.unlink()


@pytest.fixture
def sample_fnord() -> FnordSighting:
    """
    Fixture providing a sample fnord sighting.

    A standard fnord for testing purposes.

    Returns:
        FnordSighting: Sample fnord
    """
    return FnordSighting(
        when="2026-01-07T14:23:00Z",
        where_place_name="Seattle, WA",
        source="News Article",
        summary="Found fnord hidden in tech news article",
        notes={"url": "https://example.com", "author": "Unknown"},
    )


@pytest.fixture
def multiple_fnords() -> list[FnordSighting]:
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
            summary="Debug log contained the word fnord",
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
def ingested_fnord(
    initialized_db: Path, sample_fnord: FnordSighting
) -> Generator[FnordSighting, None, None]:
    """
    Fixture providing a fnord that has been ingested into the database.

    The fnord is now in the sacred database!

    Yields:
        FnordSighting: Ingested fnord with ID
    """
    result = ingest_fnord(sample_fnord)
    yield result


@pytest.fixture
def ingested_multiple_fnords(
    initialized_db: Path, multiple_fnords: list[FnordSighting]
) -> Generator[list[FnordSighting], None, None]:
    """
    Fixture providing multiple ingested fnords.

    Many fnords in the database!

    Yields:
        list[FnordSighting]: List of ingested fnords with IDs
    """
    results = [ingest_fnord(fnord) for fnord in multiple_fnords]
    yield results


@pytest.fixture
def db_connection(initialized_db: Path) -> Generator:
    """
    Fixture providing a direct database connection.

    For advanced testing that needs direct SQL access.

    Yields:
        sqlite3.Connection: Database connection
    """
    with get_db_connection() as conn:
        yield conn
