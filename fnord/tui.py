"""
Fnord TUI Module

Text User Interface for interactive fnord browsing and editing.

The fnords deserve a beautiful interface. Textual provides it.
This is where Discordians commune with their fnords.
"""

import logging
import json
from typing import Optional
from datetime import datetime, timezone

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Button,
    Input,
    Label,
    TextArea,
    Static,
    ContentSwitcher,
)
from textual.screen import ModalScreen
from textual import events
from textual.message import Message

from fnord.database import (
    init_db,
    ingest_fnord,
    query_fnord_count,
    get_all_fnords,
    update_fnord,
    delete_fnord,
    search_fnords,
)
from fnord.models import FnordSighting

logger = logging.getLogger(__name__)


class AddEditScreen(ModalScreen):
    """
    Screen for adding or editing a fnord sighting.

    The fnords demand proper form filling.
    """

    CSS = """
    AddEditScreen {
        align: center middle;
    }
    #dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    Label {
        width: 20;
        text-align: right;
    }
    Input, TextArea {
        width: 1fr;
    }
    Button {
        width: 15;
        margin: 1;
    }
    """

    def __init__(self, fnord: Optional[FnordSighting] = None) -> None:
        """
        Initialize the add/edit screen.

        Args:
            fnord: Existing fnord to edit (None for new fnord)
        """
        super().__init__()
        self.fnord = fnord

    def compose(self) -> ComposeResult:
        """Compose the screen widgets."""
        title = "Edit Fnord Sighting" if self.fnord else "Add New Fnord Sighting"

        with Container(id="dialog"):
            yield Static(title, id="title")
            yield Horizontal(
                Label("When*:"),
                Input(
                    placeholder="2026-01-07T14:23:00Z",
                    value=self.fnord.when if self.fnord else datetime.now(timezone.utc).isoformat(),
                    id="when_input",
                ),
            )
            yield Horizontal(
                Label("Place:"),
                Input(
                    placeholder="Seattle, WA",
                    value=self.fnord.where_place_name if self.fnord and self.fnord.where_place_name else "",
                    id="place_input",
                ),
            )
            yield Horizontal(
                Label("Source*:"),
                Input(
                    placeholder="News, Walk, Code, Dream, etc.",
                    value=self.fnord.source if self.fnord else "",
                    id="source_input",
                ),
            )
            yield Horizontal(
                Label("Summary*:"),
                Input(
                    placeholder="Describe the fnord...",
                    value=self.fnord.summary if self.fnord else "",
                    id="summary_input",
                ),
            )
            yield Horizontal(
                Label("Notes (JSON):"),
                TextArea(
                    placeholder='{"url": "...", "author": "..."}',
                    value=json.dumps(self.fnord.notes, indent=2) if self.fnord and self.fnord.notes else "",
                    id="notes_input",
                ),
            )
            yield Horizontal(
                Button("[Now]", variant="primary", id="now_button"),
                Button("[Save]", variant="success", id="save_button"),
                Button("[Cancel]", variant="error", id="cancel_button"),
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "now_button":
            self._set_now()
        elif event.button.id == "save_button":
            self._save_fnord()
        elif event.button.id == "cancel_button":
            self.app.pop_screen()

    def _set_now(self) -> None:
        """Set the when field to current time."""
        now = datetime.now(timezone.utc).isoformat()
        self.query_one("#when_input", Input).value = now

    def _save_fnord(self) -> None:
        """Save the fnord and close the screen."""
        try:
            # Get input values
            when = self.query_one("#when_input", Input).value
            place = self.query_one("#place_input", Input).value
            source = self.query_one("#source_input", Input).value
            summary = self.query_one("#summary_input", Input).value
            notes_str = self.query_one("#notes_input", TextArea).text

            # Parse notes JSON
            notes = None
            if notes_str.strip():
                try:
                    notes = json.loads(notes_str)
                except json.JSONDecodeError:
                    self.app.notify("Invalid JSON in notes!", severity="error")
                    return

            # Create or update fnord
            if self.fnord:
                # Update existing
                self.fnord.when = when
                self.fnord.where_place_name = place if place else None
                self.fnord.source = source
                self.fnord.summary = summary
                self.fnord.notes = notes

                update_fnord(self.fnord)
                self.app.notify(f"Fnord {self.fnord.id} updated! Hail Discordia!", severity="success")
            else:
                # Create new
                fnord = FnordSighting(
                    when=when,
                    where_place_name=place if place else None,
                    source=source,
                    summary=summary,
                    notes=notes,
                )

                result = ingest_fnord(fnord)
                self.app.notify(f"Fnord created with ID {result.id}!", severity="success")

            # Refresh the main screen
            self.app.get_screen_by_name("main").refresh_fnords()

            # Close this screen
            self.app.pop_screen()

        except ValueError as e:
            self.app.notify(f"Error: {e}", severity="error")
        except Exception as e:
            self.app.notify(f"Unexpected error: {e}", severity="error")


class FnordTrackerApp(App):
    """
    Main fnord tracker TUI application.

    The fnords have a home, and it is beautiful.
    """

    CSS = """
    Screen {
        background: $background;
    }
    #stats {
        dock: top;
        height: 3;
        background: $panel;
        padding: 0 1;
    }
    #fnord_table {
        height: 1fr;
    }
    #search_input {
        dock: top;
        margin: 1;
    }
    .stat {
        text-style: bold;
    }
    """

    TITLE = "🍎 Fnord Tracker 🍎"

    def compose(self) -> ComposeResult:
        """Compose the app widgets."""
        yield Header()
        yield Static(id="stats")
        yield Input(placeholder="Search fnords...", id="search_input")
        yield DataTable(id="fnord_table")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Initialize database
        init_db()

        # Set up the data table
        table = self.query_one(DataTable)
        table.add_column("ID", width=5)
        table.add_column("When", width=20)
        table.add_column("Source", width=15)
        table.add_column("Summary", width=40)
        table.add_column("Location", width=25)

        # Load fnords
        self.refresh_fnords()

        # Focus on table
        table.focus()

    def refresh_fnords(self, search_query: Optional[str] = None) -> None:
        """
        Refresh the fnords table.

        Args:
            search_query: Optional search query
        """
        table = self.query_one(DataTable)
        table.clear()

        try:
            # Get fnords
            if search_query:
                fnords = search_fnords(search_query, limit=100)
            else:
                fnords = get_all_fnords(limit=100)

            # Update stats
            count = query_fnord_count()
            if count == 23:
                stats_text = f"[bold]Total Fnords: {count} (Sacred!)[/] "
            else:
                stats_text = f"[bold]Total Fnords: {count}[/] "

            if fnords:
                last_fnord = fnords[0]
                stats_text += f"| Last: {last_fnord.when}"
            else:
                stats_text += "| No fnords yet"

            self.query_one("#stats", Static).update(stats_text)

            # Populate table
            for fnord in fnords:
                location = fnord.where_place_name or "Unknown"

                table.add_row(
                    str(fnord.id),
                    fnord.when,
                    fnord.source,
                    fnord.summary[:40] + "..." if len(fnord.summary) > 40 else fnord.summary,
                    location,
                    key=str(fnord.id),
                )

        except Exception as e:
            self.notify(f"Error loading fnords: {e}", severity="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        if event.input.id == "search_input":
            self.refresh_fnords(event.input.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        fnord_id = int(event.row_key.value)

    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        table = self.query_one(DataTable)

        if event.key == "q":
            self.exit()
        elif event.key == "n":
            self._open_add_screen()
        elif event.key == "e":
            if table.cursor_row is not None:
                row_key = table.get_row_at(table.cursor_row).key
                fnord_id = int(row_key)
                self._open_edit_screen(fnord_id)
        elif event.key == "d":
            if table.cursor_row is not None:
                row_key = table.get_row_at(table.cursor_row).key
                fnord_id = int(row_key)
                self._delete_fnord(fnord_id)
        elif event.key == "s":
            self.query_one("#search_input", Input).focus()
        elif event.key == "r":
            self.refresh_fnords()
        elif event.key == "/":
            self._show_help()

    def _open_add_screen(self) -> None:
        """Open the add fnord screen."""
        self.push_screen(AddEditScreen())

    def _open_edit_screen(self, fnord_id: int) -> None:
        """Open the edit fnord screen."""
        fnord = get_all_fnords(limit=1000)
        target_fnord = next((f for f in fnord if f.id == fnord_id), None)

        if target_fnord:
            self.push_screen(AddEditScreen(target_fnord))
        else:
            self.notify("Fnord not found!", severity="error")

    def _delete_fnord(self, fnord_id: int) -> None:
        """Delete a fnord."""
        delete_fnord(fnord_id)
        self.refresh_fnords()
        self.notify(f"Fnord {fnord_id} deleted! It has vanished into the void.", severity="success")

    def _show_help(self) -> None:
        """Show help information."""
        help_text = """
[q] Quit  [n] New  [e] Edit  [d] Delete
[s] Search  [r] Refresh  [/] This help
        """
        self.notify(help_text, title="Keyboard Shortcuts", timeout=10)


def run_tui() -> None:
    """
    Run the fnord tracker TUI.

    Launch the beautiful Textual interface.
    """
    app = FnordTrackerApp()
    app.run()
