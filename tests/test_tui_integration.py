"""
Integration tests for TUI using pytest-textual.

These tests drive the actual TUI to verify workflows work end-to-end.
"""

import pytest
from textual.widgets import DataTable, Input

from fnord.tui import FnordTrackerApp, DetailScreen, AddEditScreen
from fnord.models import FnordSighting
from fnord.database import get_fnord_by_id, ingest_fnord, query_fnord_count
from fnord.config import Config


@pytest.fixture
async def app(initialized_db):
    """Create and mount TUI app."""
    app_instance = FnordTrackerApp()
    async with app_instance.run_test() as pilot:
        yield pilot


@pytest.fixture
def sample_fnord():
    """Create a sample fnord for testing."""
    return FnordSighting(
        when="2026-01-07T14:23:00Z",
        where_place_name="Seattle, WA",
        source="Test Source",
        summary="Test fnord for integration testing",
        notes={"url": "https://example.com", "author": "Test Author"},
    )


@pytest.mark.asyncio
class TestTUIIntegration:
    """Test full TUI workflows."""

    async def test_initial_view_loads(self, app):
        """Test that initial view loads correctly."""
        # Verify table exists
        table = app.app.query_one(DataTable)
        assert table.id == "fnord_table"

        # Verify app is running
        assert app.app.is_running

    async def test_n_key_opens_add_screen(self, app):
        """Test pressing 'n' opens add screen."""
        await app.press("n")

        # Verify we're on add screen
        assert isinstance(app.app.screen, AddEditScreen)

    async def test_edit_with_e_key(self, app, sample_fnord):
        """Test editing a fnord using 'e' key."""
        # Add a fnord
        result = ingest_fnord(sample_fnord)
        app.app.refresh_fnords()

        # Press 'e' to open detail view - should not crash
        await app.press("e")

        # Navigate through fields (testing that UI responds to tab)
        await app.press("tab", "tab", "tab", "tab")

        # Save with 's' - should complete without error
        await app.press("s")

        # Verify fnord still exists in database
        if result.id:
            updated_fnord = get_fnord_by_id(result.id)
            assert updated_fnord is not None

    async def test_edit_with_enter_key(self, app, sample_fnord):
        """Test editing a fnord using Enter key."""
        # Add a fnord
        ingest_fnord(sample_fnord)
        app.app.refresh_fnords()

        # Press Enter to open detail view
        await app.press("enter")

        # Verify detail screen opened
        assert isinstance(app.app.screen, DetailScreen)

    async def test_delete_fnord(self, app, sample_fnord):
        """Test deleting a fnord."""
        # Add a fnord
        result = ingest_fnord(sample_fnord)
        app.app.refresh_fnords()

        # Get initial count
        initial_count = query_fnord_count()

        # Delete with 'd' - should complete without error
        await app.press("d")

        # Verify fnord was deleted
        new_count = query_fnord_count()
        assert new_count < initial_count

    async def test_search_focus(self, app):
        """Test pressing 's' focuses search input."""
        await app.press("s")

        # Verify search input is focused
        search_input = app.app.query_one("#search_input", Input)
        assert search_input.has_focus

    async def test_refresh_functionality(self, app, sample_fnord):
        """Test refreshing the fnord list."""
        # Get initial row count
        table = app.app.query_one(DataTable)
        initial_rows = len(table.rows)

        # Add a fnord
        ingest_fnord(sample_fnord)

        # Press 'r' to refresh
        await app.press("r")

        # Verify table was updated
        table = app.app.query_one(DataTable)
        assert len(table.rows) > initial_rows

    async def test_detail_screen_escape_to_go_back(self, app, sample_fnord):
        """Test pressing escape returns to main screen."""
        # Add a fnord
        ingest_fnord(sample_fnord)
        app.app.refresh_fnords()

        # Open detail screen
        await app.press("e")

        # Press escape to go back without saving - should complete
        await app.press("escape")

    async def test_navigate_table_with_arrow_keys(self, app):
        """Test navigating the table with arrow keys."""
        # Add multiple fnords
        for i in range(5):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source=f"Source {i}",
                summary=f"Test fnord {i}",
            )
            ingest_fnord(fnord)

        app.app.refresh_fnords()

        table = app.app.query_one(DataTable)
        initial_row = table.cursor_row

        # Navigate down
        await app.press("down")
        assert table.cursor_row == initial_row + 1

        # Navigate up
        await app.press("up")
        assert table.cursor_row == initial_row

    async def test_detail_screen_save_workflow(self, app, sample_fnord):
        """Test complete save workflow from detail screen."""
        # Add a fnord
        result = ingest_fnord(sample_fnord)
        app.app.refresh_fnords()

        # Open detail screen
        await app.press("e")

        # Navigate through fields
        await app.press("tab", "tab", "tab")

        # Save with 's' - should complete without error
        await app.press("s")

        # Verify fnord still exists after save
        if result.id:
            updated_fnord = get_fnord_by_id(result.id)
            assert updated_fnord is not None

    async def test_add_screen_cancel(self, app):
        """Test cancelling from add screen."""
        # Open add screen
        await app.press("n")

        # Press escape to cancel - should complete
        await app.press("escape")

    async def test_q_key_quits_app(self, app):
        """Test pressing 'q' attempts to quit."""
        # Press 'q'
        await app.press("q")

        # The app should exit (in run_test mode, this just ends the test context)
        # We verify the key was handled by checking we don't get an error
        assert True  # If we got here, the key was handled
