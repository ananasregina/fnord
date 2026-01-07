"""
Tests for fnord models.

The fnords must have proper shape. We test their form.
"""

import pytest
from datetime import datetime, timezone
from typing import Tuple

from fnord.models import FnordSighting


class TestFnordSighting:
    """Test the FnordSighting model."""

    def test_create_minimal_fnord(self):
        """Test creating a fnord with only required fields."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
        )

        assert fnord.when == "2026-01-07T14:23:00Z"
        assert fnord.source == "News"
        assert fnord.summary == "Found fnord"
        assert fnord.id is None
        assert fnord.where_place_name is None
        assert fnord.notes is None

    def test_create_complete_fnord(self):
        """Test creating a fnord with all fields."""
        notes = {"url": "https://example.com"}

        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            where_place_name="Seattle, WA",
            source="News",
            summary="Found fnord",
            notes=notes,
        )

        assert fnord.where_place_name == "Seattle, WA"
        assert fnord.notes == notes

    def test_to_dict(self):
        """Test converting fnord to dictionary."""
        fnord = FnordSighting(
            id=1,
            when="2026-01-07T14:23:00Z",
            where_place_name="Seattle, WA",
            source="News",
            summary="Found fnord",
            notes={"url": "https://example.com"},
        )

        result = fnord.to_dict()

        assert result["id"] == 1
        assert result["when"] == "2026-01-07T14:23:00Z"
        assert result["where_place_name"] == "Seattle, WA"
        assert result["source"] == "News"
        assert result["summary"] == "Found fnord"
        assert result["notes"] == {"url": "https://example.com"}

    def test_from_dict(self):
        """Test creating fnord from dictionary."""
        data = {
            "id": 1,
            "when": "2026-01-07T14:23:00Z",
            "where_place_name": "Seattle, WA",
            "source": "News",
            "summary": "Found fnord",
            "notes": {"url": "https://example.com"},
        }

        fnord = FnordSighting.from_dict(data)

        assert fnord.id == 1
        assert fnord.when == "2026-01-07T14:23:00Z"
        assert fnord.where_place_name == "Seattle, WA"
        assert fnord.source == "News"
        assert fnord.summary == "Found fnord"
        assert fnord.notes == {"url": "https://example.com"}

    def test_validate_valid_fnord(self):
        """Test validation of a valid fnord."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
        )

        errors = fnord.validate()

        assert errors == []

    def test_validate_missing_when(self):
        """Test validation fails when 'when' is missing."""
        fnord = FnordSighting(when="", source="News", summary="Found fnord")

        errors = fnord.validate()

        assert len(errors) > 0
        assert any("when" in error for error in errors)

    def test_validate_invalid_when_format(self):
        """Test validation fails when 'when' has invalid format."""
        fnord = FnordSighting(
            when="not-a-date", source="News", summary="Found fnord"
        )

        errors = fnord.validate()

        assert len(errors) > 0
        assert any("when" in error and "ISO8601" in error for error in errors)

    def test_validate_missing_source(self):
        """Test validation fails when 'source' is missing."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z", source="", summary="Found fnord"
        )

        errors = fnord.validate()

        assert len(errors) > 0
        assert any("source" in error for error in errors)

    def test_validate_missing_summary(self):
        """Test validation fails when 'summary' is missing."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z", source="News", summary=""
        )

        errors = fnord.validate()

        assert len(errors) > 0
        assert any("summary" in error for error in errors)

    def test_validate_invalid_notes(self):
        """Test validation fails when 'notes' is not JSON-serializable."""
        # Use a non-serializable object (lambda)
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
            notes={"function": lambda x: x},  # type: ignore
        )

        errors = fnord.validate()

        assert len(errors) > 0
        assert any("notes" in error for error in errors)

    def test_validate_multiple_errors(self):
        """Test validation returns multiple errors."""
        fnord = FnordSighting(
            when="",
            source="",
            summary="",
        )

        errors = fnord.validate()

        # Should have at least 3 errors (when, source, summary)
        assert len(errors) >= 3

    def test_str_representation(self):
        """Test string representation of fnord."""
        fnord = FnordSighting(
            id=1,
            when="2026-01-07T14:23:00Z",
            where_place_name="Seattle, WA",
            source="News",
            summary="Found fnord in article",
        )

        result = str(fnord)

        assert "2026-01-07T14:23:00Z" in result
        assert "News" in result
        assert "Found fnord in article" in result
        assert "Seattle, WA" in result

    def test_str_without_location(self):
        """Test string representation without location."""
        fnord = FnordSighting(
            id=1,
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
        )

        result = str(fnord)

        assert "Unknown location" in result

    def test_repr_representation(self):
        """Test repr of fnord."""
        fnord = FnordSighting(
            id=23,
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord in article about Discordianism",
        )

        result = repr(fnord)

        assert "FnordSighting" in result
        assert "id=23" in result
        assert "2026-01-07T14:23:00Z" in result
        assert "News" in result
        assert "Found fnord in article" in result

    def test_is_valid_edge_case(self):
        """Test fnord with optional fields but valid."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="Code",
            summary="Fnord in debug log",
        )

        errors = fnord.validate()

        # Should be valid - optional fields can be None
        assert errors == []
