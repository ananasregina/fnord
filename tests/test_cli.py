"""
Tests for fnord CLI.

The command line must work! Discordians need quick fnord entry.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner

from fnord.cli import app
from fnord.models import FnordSighting

runner = CliRunner()


class TestCLIIngest:
    """Test CLI ingest command."""

    def test_ingest_success(self, initialized_db: Path):
        """Test successful fnord ingestion via CLI."""
        result = runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord in article",
            ],
        )

        assert result.exit_code == 0
        assert "Fnord ingested successfully!" in result.stdout

    def test_ingest_with_location(self, initialized_db: Path):
        """Test fnord ingestion with location."""
        result = runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord",
                "--where-place-name",
                "Seattle, WA",
            ],
        )

        assert result.exit_code == 0
        assert "Fnord ingested successfully!" in result.stdout

    def test_ingest_with_notes(self, initialized_db: Path):
        """Test fnord ingestion with notes."""
        notes = '{"url": "https://example.com", "author": "Test"}'

        result = runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord",
                "--notes",
                notes,
            ],
        )

        assert result.exit_code == 0
        assert "Fnord ingested successfully!" in result.stdout

    def test_ingest_invalid_notes_json(self, initialized_db: Path):
        """Test fnord ingestion with invalid JSON in notes."""
        result = runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord",
                "--notes",
                "not-valid-json",
            ],
        )

        assert result.exit_code == 1
        # Error message goes to stderr in typer
        assert "Invalid JSON" in result.stderr or "Expecting value" in str(result.exception)

    def test_ingest_missing_required_field(self, initialized_db: Path):
        """Test fnord ingestion with missing required field."""
        # Missing --source
        result = runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--summary",
                "Found fnord",
            ],
        )

        assert result.exit_code != 0


class TestCLICount:
    """Test CLI count command."""

    def test_count_empty_db(self, initialized_db: Path):
        """Test count when database is empty."""
        result = runner.invoke(app, ["count"])

        assert result.exit_code == 0
        assert "No fnords recorded yet" in result.stdout

    def test_count_one_fnord(self, initialized_db: Path):
        """Test count with one fnord."""
        # First ingest a fnord
        runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord",
            ],
        )

        result = runner.invoke(app, ["count"])

        assert result.exit_code == 0
        assert "1 fnord" in result.stdout

    def test_count_multiple_fnords(self, initialized_db: Path):
        """Test count with multiple fnords."""
        # Ingest multiple fnords
        for i in range(5):
            runner.invoke(
                app,
                [
                    "ingest",
                    "--when",
                    "2026-01-07T14:23:00Z",
                    "--source",
                    "Test",
                    "--summary",
                    f"Fnord #{i+1}",
                ],
            )

        result = runner.invoke(app, ["count"])

        assert result.exit_code == 0
        assert "5 fnords" in result.stdout


class TestCLIList:
    """Test CLI list command."""

    def test_list_empty_db(self, initialized_db: Path):
        """Test list when database is empty."""
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No fnords found" in result.stdout

    def test_list_one_fnord(self, initialized_db: Path):
        """Test list with one fnord."""
        runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord",
            ],
        )

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Found fnord" in result.stdout

    def test_list_with_limit(self, initialized_db: Path):
        """Test list with limit."""
        # Ingest multiple fnords
        for i in range(5):
            runner.invoke(
                app,
                [
                    "ingest",
                    "--when",
                    "2026-01-07T14:23:00Z",
                    "--source",
                    "Test",
                    "--summary",
                    f"Fnord #{i+1}",
                ],
            )

        result = runner.invoke(app, ["list", "--limit", "2"])

        assert result.exit_code == 0
        assert "Total: 2" in result.stdout

    def test_list_json_output(self, initialized_db: Path):
        """Test list with JSON output."""
        runner.invoke(
            app,
            [
                "ingest",
                "--when",
                "2026-01-07T14:23:00Z",
                "--source",
                "News",
                "--summary",
                "Found fnord",
            ],
        )

        result = runner.invoke(app, ["list", "--json"])

        assert result.exit_code == 0

        # Should be valid JSON
        import json

        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 1


class TestCLIVerbose:
    """Test CLI verbose mode."""

    def test_verbose_flag(self, initialized_db: Path):
        """Test that verbose flag works."""
        result = runner.invoke(app, ["--verbose", "count"])

        assert result.exit_code == 0
