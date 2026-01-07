"""
Tests for fnord TUI.

The fnords deserve a beautiful interface. We test its parts.

Note: TUI testing is complex; these tests focus on core logic.
"""

import pytest
from fnord.database import ingest_fnord, get_all_fnords
from fnord.models import FnordSighting


class TestTUILogic:
    """Test TUI-specific logic (without actual UI rendering)."""

    def test_fnord_for_tui_display(self, initialized_db):
        """Test that fnords can be properly formatted for TUI display."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            where_place_name="Seattle, WA",
            source="News",
            summary="Found fnord in article about Law of Fives",
            notes={"url": "https://example.com"},
        )

        # Ingest the fnord
        result = ingest_fnord(fnord)

        # Retrieve and verify it can be displayed
        all_fnords = get_all_fnords()
        assert len(all_fnords) == 1

        displayed_fnord = all_fnords[0]
        assert displayed_fnord.id == result.id

        # Test string representation (what TUI would show)
        str_repr = str(displayed_fnord)
        assert "2026-01-07T14:23:00Z" in str_repr
        assert "News" in str_repr
        assert "Seattle, WA" in str_repr

    def test_tui_search_logic(self, initialized_db):
        """Test the search logic that TUI would use."""
        from fnord.database import search_fnords

        # Create multiple fnords
        fnords = [
            FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="News",
                summary="Found fnord in article",
                where_place_name="Seattle",
            ),
            FnordSighting(
                when="2026-01-06T09:15:00Z",
                source="Walk",
                summary="Saw fnord graffiti",
                where_place_name="San Francisco",
            ),
            FnordSighting(
                when="2026-01-05T22:30:00Z",
                source="Code",
                summary="Debug log had fnord",
                where_place_name="New York",
            ),
        ]

        for fnord in fnords:
            ingest_fnord(fnord)

        # Test search
        results = search_fnords("Seattle")
        assert len(results) == 1
        assert results[0].where_place_name == "Seattle"

        # Test search by source
        results = search_fnords("News")
        assert len(results) == 1
        assert results[0].source == "News"

        # Test search by summary
        results = search_fnords("graffiti")
        assert len(results) == 1
        assert "graffiti" in results[0].summary.lower()

    def test_tui_edit_flow(self, initialized_db):
        """Test the edit flow that TUI would use."""
        from fnord.database import update_fnord, get_fnord_by_id

        # Create a fnord
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Original summary",
        )

        result = ingest_fnord(fnord)
        assert result.id == 1

        # Simulate TUI edit
        updated = get_fnord_by_id(1)
        updated.summary = "Updated summary via TUI"
        updated.source = "Updated Source"

        update_fnord(updated)

        # Verify update
        final = get_fnord_by_id(1)
        assert final.summary == "Updated summary via TUI"
        assert final.source == "Updated Source"

    def test_tui_delete_flow(self, initialized_db):
        """Test the delete flow that TUI would use."""
        from fnord.database import delete_fnord, get_fnord_by_id

        # Create a fnord
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="To be deleted",
        )

        result = ingest_fnord(fnord)

        # Simulate TUI delete
        delete_fnord(result.id)

        # Verify deletion
        final = get_fnord_by_id(result.id)
        assert final is None

    def test_tui_pagination_logic(self, initialized_db):
        """Test the pagination logic that TUI would use."""
        # Create 30 fnords (more than default page size of 23)
        for i in range(30):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="Test",
                summary=f"Fnord #{i+1}",
            )
            ingest_fnord(fnord)

        # Test first page (limit 23)
        page1 = get_all_fnords(limit=23, offset=0)
        assert len(page1) == 23

        # Test second page
        page2 = get_all_fnords(limit=23, offset=23)
        assert len(page2) == 7

        # Verify no overlap
        page1_ids = {f.id for f in page1}
        page2_ids = {f.id for f in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0


class TestTUIEdgeCases:
    """Test TUI edge cases and error handling."""

    def test_tui_handles_empty_notes(self, initialized_db):
        """Test that TUI handles fnords without notes."""
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="No notes here",
        )

        result = ingest_fnord(fnord)

        # Retrieve and display
        all_fnords = get_all_fnords()
        retrieved = all_fnords[0]

        assert retrieved.notes is None
        # String representation should work
        str(retrieved)

    def test_tui_handles_long_summary(self, initialized_db):
        """Test that TUI handles very long summaries."""
        long_summary = "Fnord " * 100  # 600 characters

        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="Test",
            summary=long_summary,
        )

        ingest_fnord(fnord)

        # TUI should truncate this for display, but data should be intact
        all_fnords = get_all_fnords()
        retrieved = all_fnords[0]

        assert len(retrieved.summary) == len(long_summary)

    def test_tui_handles_complex_notes(self, initialized_db):
        """Test that TUI handles complex nested notes."""
        complex_notes = {
            "metadata": {
                "author": "Eris",
                "year": 2026,
                "tags": ["fnord", "discordia", "chaos"],
            },
            "location": {
                "coordinates": {"lat": 47.6062, "lon": -122.3321},
                "accuracy": "high",
            },
            "references": [
                {"name": "Principia Discordia", "page": 23},
                {"name": "Illuminatus! Trilogy", "page": 42},
            ],
        }

        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="Book",
            summary="Found deep fnord references",
            notes=complex_notes,
        )

        result = ingest_fnord(fnord)

        # Verify notes are preserved
        all_fnords = get_all_fnords()
        retrieved = all_fnords[0]

        assert retrieved.notes == complex_notes
        assert len(retrieved.notes["references"]) == 2

    def test_tui_search_no_results(self, initialized_db):
        """Test TUI search with no results."""
        from fnord.database import search_fnords

        # Create a fnord
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
        )
        ingest_fnord(fnord)

        # Search for something that doesn't exist
        results = search_fnords("nonexistent fnord xyz123")

        assert len(results) == 0
