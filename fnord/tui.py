"""
Fnord TUI Module

Text User Interface for interactive fnord browsing and editing.

The fnords deserve a beautiful interface. Textual provides it.
This is where Discordians commune with their fnords.
"""

import json
import logging
from datetime import UTC, datetime

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TextArea,
)

from fnord.database import (
    delete_fnord,
    get_all_fnords,
    get_fnord_by_id,
    ingest_fnord,
    init_db,
    query_fnord_count,
    search_fnords,
    update_fnord,
)
from fnord.models import FnordSighting

logger = logging.getLogger(__name__)


class DetailScreen(Screen):
    """
    Full-screen detail view for viewing and editing a fnord.

    The fnords deserve room to breathe.
    """

    BINDINGS = [
        ("s", "save", "Save"),
        ("escape,q", "cancel", "Cancel"),
    ]

    CSS = """
    DetailScreen {
        background: $background;
    }
    #title {
        text-align: center;
        text-style: bold;
        margin: 1 0;
        padding: 1;
        background: $primary;
        color: $text;
    }
    #form_container {
        padding: 1 2;
        height: 1fr;
    }
    Label {
        width: 15;
        text-align: right;
        padding: 1;
    }
    #when_input, #place_input, #source_input {
        width: 1fr;
        margin: 1 0;
    }
    #summary_input {
        width: 1fr;
        min-height: 5;
        margin: 1 0;
    }
    #notes_input {
        width: 1fr;
        min-height: 10;
        margin: 1 0;
    }
    #button_row {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $panel;
    }
    Button {
        width: 20;
        margin: 0 1;
        color: $text;
    }
    Button.-default {
        background: $boost;
    }
    Button.-primary {
        background: $primary;
    }
    #help_bar {
        dock: top;
        height: 2;
        background: $surface;
        padding: 0 1;
        text-style: bold;
    }
    """

    def __init__(self, fnord: FnordSighting) -> None:
        """Initialize the detail screen."""
        super().__init__()
        self.fnord = fnord

    def compose(self) -> ComposeResult:
        """Compose the screen widgets."""
        yield Static("🍎 Fnord Details 🍎", id="title")
        yield Static("[s] Save  [q/Escape] Back", id="help_bar")
        with Vertical(id="form_container"):
            yield Horizontal(
                Label("ID:"),
                Static(str(self.fnord.id), id="id_display"),
            )
            yield Horizontal(
                Label("When*:"),
                Input(
                    placeholder="2026-01-07T14:23:00Z",
                    value=self.fnord.when,
                    id="when_input",
                ),
            )
            yield Horizontal(
                Label("Place:"),
                Input(
                    placeholder="Seattle, WA",
                    value=self.fnord.where_place_name or "",
                    id="place_input",
                ),
            )
            yield Horizontal(
                Label("Source*:"),
                Input(
                    placeholder="News, Walk, Code, Dream, etc.",
                    value=self.fnord.source,
                    id="source_input",
                ),
            )
            yield Label("Summary*:")
            yield TextArea(
                self.fnord.summary,
                placeholder="Describe the fnord...",
                id="summary_input",
            )
            yield Label("Notes (JSON):")
            yield TextArea(
                json.dumps(self.fnord.notes, indent=2) if self.fnord.notes else "",
                placeholder='{"url": "...", "author": "..."}',
                id="notes_input",
            )
            yield Horizontal(
                Button("[Now]", id="now_button", variant="default"),
                Button("[Save]", id="save_button", variant="primary"),
                Button("[Back]", id="cancel_button", variant="default"),
            )

    def action_save(self) -> None:
        """Save the fnord and return to main screen."""
        self._save_fnord()

    def action_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.app.pop_screen()

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
        now = datetime.now(UTC).isoformat()
        self.query_one("#when_input", Input).value = now

    def _save_fnord(self) -> None:
        """Save the fnord and close the screen."""
        try:
            when = self.query_one("#when_input", Input).value
            place = self.query_one("#place_input", Input).value
            source = self.query_one("#source_input", Input).value
            summary = self.query_one("#summary_input", TextArea).text
            notes_str = self.query_one("#notes_input", TextArea).text

            notes = None
            if notes_str.strip():
                try:
                    notes = json.loads(notes_str)
                except json.JSONDecodeError:
                    self.app.notify("Invalid JSON in notes!", severity="error")
                    return

            self.fnord.when = when
            self.fnord.where_place_name = place if place else None
            self.fnord.source = source
            self.fnord.summary = summary
            self.fnord.notes = notes

            update_fnord(self.fnord)
            self.app.notify(f"Fnord {self.fnord.id} saved!", severity="information")

            self.app.pop_screen()

        except ValueError as e:
            self.app.notify(f"Error: {e}", severity="error")
        except Exception as e:
            self.app.notify(f"Unexpected error: {e}", severity="error")


class AddEditScreen(ModalScreen):
    """
    Screen for adding a new fnord sighting.

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
    #summary_input {
        min-height: 3;
    }
    #notes_input {
        min-height: 5;
    }
    Button {
        width: 15;
        margin: 1;
        color: $text;
    }
    Button.-success {
        background: $success;
    }
    Button.-error {
        background: $error;
    }
    Button.-primary {
        background: $primary;
    }
    """

    def __init__(self) -> None:
        """Initialize the add screen."""
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the screen widgets."""
        with Container(id="dialog"):
            yield Static("Add New Fnord Sighting", id="title")
            yield Horizontal(
                Label("When*:"),
                Input(
                    placeholder="2026-01-07T14:23:00Z",
                    value=datetime.now(UTC).isoformat(),
                    id="when_input",
                ),
            )
            yield Horizontal(
                Label("Place:"),
                Input(
                    placeholder="Seattle, WA",
                    id="place_input",
                ),
            )
            yield Horizontal(
                Label("Source*:"),
                Input(
                    placeholder="News, Walk, Code, Dream, etc.",
                    id="source_input",
                ),
            )
            yield Label("Summary*:")
            yield TextArea(
                placeholder="Describe the fnord...",
                id="summary_input",
            )
            yield Label("Notes (JSON):")
            yield TextArea(
                placeholder='{"url": "...", "author": "..."}',
                id="notes_input",
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
        now = datetime.now(UTC).isoformat()
        self.query_one("#when_input", Input).value = now

    def _save_fnord(self) -> None:
        """Save the fnord and close the screen."""
        try:
            when = self.query_one("#when_input", Input).value
            place = self.query_one("#place_input", Input).value
            source = self.query_one("#source_input", Input).value
            summary = self.query_one("#summary_input", TextArea).text
            notes_str = self.query_one("#notes_input", TextArea).text

            notes = None
            if notes_str.strip():
                try:
                    notes = json.loads(notes_str)
                except json.JSONDecodeError:
                    self.app.notify("Invalid JSON in notes!", severity="error")
                    return

            fnord = FnordSighting(
                when=when,
                where_place_name=place if place else None,
                source=source,
                summary=summary,
                notes=notes,
            )

            result = ingest_fnord(fnord)
            self.app.notify(f"Fnord created with ID {result.id}!", severity="information")

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
    #help_bar {
        dock: top;
        height: 2;
        background: $surface;
        padding: 0 1;
        text-style: bold;
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
        yield Static("[Ent/e] Edit [n] New [d] Del [s] Search [r] Refresh [q] Quit", id="help_bar")
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

    def refresh_fnords(self, search_query: str | None = None) -> None:
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

    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        table = self.query_one(DataTable)

        if event.key == "q":
            self.exit()
        elif event.key == "n":
            self._open_add_screen()
        elif event.key == "e" or event.key == "enter":
            if table.cursor_row is not None:
                row_keys = list(table.rows.keys())
                row_key = row_keys[table.cursor_row]
                if row_key is not None and row_key.value is not None:
                    fnord_id = int(row_key.value)
                    self._open_detail_screen(fnord_id)
        elif event.key == "d":
            if table.cursor_row is not None:
                row_keys = list(table.rows.keys())
                row_key = row_keys[table.cursor_row]
                if row_key is not None and row_key.value is not None:
                    fnord_id = int(row_key.value)
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

    def _open_detail_screen(self, fnord_id: int) -> None:
        """Open the detail screen for a fnord."""
        target_fnord = get_fnord_by_id(fnord_id)

        if target_fnord:
            self.push_screen(DetailScreen(target_fnord))
        else:
            self.notify("Fnord not found!", severity="error")

    def _delete_fnord(self, fnord_id: int) -> None:
        """Delete a fnord."""
        delete_fnord(fnord_id)
        self.refresh_fnords()
        self.notify(f"Fnord {fnord_id} deleted! Vanished into void.", severity="information")

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
