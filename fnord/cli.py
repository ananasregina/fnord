"""
Fnord CLI Module

Command-line interface for fnord tracking.

Quick one-shot commands for the busy Discordian.
"""

import typer
from typing import Optional
import json
from datetime import datetime, timezone
import logging

from fnord.database import init_db, ingest_fnord, query_fnord_count, get_all_fnords
from fnord.models import FnordSighting

# Hail Eris!
app = typer.Typer(
    name="fnord",
    help="Track the elusive fnords! 🍎✨",
    add_completion=False,
)

logger = logging.getLogger(__name__)


@app.command()
def ingest(
    when: str = typer.Option(
        datetime.now(timezone.utc).isoformat(),
        "--when",
        "-w",
        help="When the fnord appeared (ISO8601 format, e.g., 2026-01-07T14:23:00Z)",
    ),
    where_place_name: Optional[str] = typer.Option(
        None, "--where-place-name", "-p", help="Location description"
    ),
    source: str = typer.Option(
        ...,
        "--source",
        "-s",
        help="Source of the fnord sighting (News, Walk, Code, Dream, etc.)",
    ),
    summary: str = typer.Option(
        ...,
        "--summary",
        "-y",
        help="Brief description of the fnord sighting",
    ),
    notes: Optional[str] = typer.Option(
        None, "--notes", "-n", help="Additional metadata as JSON string"
    ),
    logical_fallacies: Optional[str] = typer.Option(
        None,
        "--logical-fallacies",
        "-f",
        help='Logical fallacies as JSON array string (e.g., \'["ad hominem", "straw man"]\')',
    ),
):
    """
    Ingest a fnord sighting into the sacred database.

    Example:
        fnord ingest --source "News" --summary "Found fnord in article" --notes '{"url": "..."}' --logical-fallacies '["ad hominem"]'
    """
    try:
        # Parse notes JSON
        notes_dict = None
        if notes:
            try:
                notes_dict = json.loads(notes)
            except json.JSONDecodeError as e:
                typer.echo(f"Error: Invalid JSON in notes: {e}", err=True)
                raise typer.Exit(1)

        # Parse logical_fallacies JSON
        logical_fallacies_list = None
        if logical_fallacies:
            try:
                parsed = json.loads(logical_fallacies)
                if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                    logical_fallacies_list = parsed
                else:
                    typer.echo(
                        f"Error: logical_fallacies must be a JSON array of strings", err=True
                    )
                    raise typer.Exit(1)
            except json.JSONDecodeError as e:
                typer.echo(f"Error: Invalid JSON in logical_fallacies: {e}", err=True)
                raise typer.Exit(1)

        # Create the fnord sighting
        fnord = FnordSighting(
            when=when,
            where_place_name=where_place_name,
            source=source,
            summary=summary,
            notes=notes_dict,
            logical_fallacies=logical_fallacies_list,
        )

        # Initialize database and ingest
        init_db()
        result = ingest_fnord(fnord)

        typer.echo(f"✓ Fnord ingested successfully! (ID: {result.id})")
        typer.echo(f"  The fnord has been recorded. All hail Discordia!")

    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        logger.exception("Failed to ingest fnord")
        raise typer.Exit(1)


@app.command()
def count():
    """
    Query the total number of fnords in the database.

    Example:
        fnord count
    """
    try:
        init_db()
        total = query_fnord_count()

        if total == 0:
            typer.echo("No fnords recorded yet. The fnords are shy today.")
        elif total == 1:
            typer.echo("There is 1 fnord in the database. The fnord is watching.")
        elif total == 23:
            typer.echo(f"There are {total} fnords in the database. A sacred number! All hail Eris!")
        else:
            typer.echo(f"There are {total} fnords in the database.")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Failed to query fnord count")
        raise typer.Exit(1)


@app.command()
def web(
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port for web server (default: 8000, overrides FNORD_WEB_PORT env var)",
    ),
):
    """
    Launch web interface for fnord tracking.

    FastAPI + HTMX web interface. The fnords deserve a modern home.

    Example:
        fnord web --port 8080

    Environment:
        Set FNORD_WEB_PORT to override default port.
    """
    import uvicorn

    from fnord.config import get_config

    config = get_config()
    web_port = config.get_web_port()

    print(f"🍎 Starting Fnord Tracker Web Server... 🍎")
    print(f"Open http://localhost:{web_port} in your browser")
    print(f"Port: {web_port} (set via FNORD_WEB_PORT env var)")
    print()
    print("Press Ctrl+C to stop the server")
    print()

    try:
        uvicorn.run(
            "fnord.web.app:app",
            host="127.0.0.1",
            port=web_port,
            reload=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped. The fnords await your return.")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"Error starting web server: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def list(
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of fnords to list (default: all)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON instead of human-readable",
    ),
):
    """
    List all fnord sightings.

    Example:
        fnord list
        fnord list --limit 5
        fnord list --json
    """
    try:
        init_db()
        fnords = get_all_fnords(limit=limit)

        if not fnords:
            typer.echo("No fnords found. The database is empty. Go find some fnords!")
            return

        if json_output:
            output = [f.to_dict() for f in fnords]
            typer.echo(json.dumps(output, indent=2))
        else:
            for fnord in fnords:
                where = fnord.where_place_name or "Unknown location"

                notes_str = f" [notes: {json.dumps(fnord.notes)}]" if fnord.notes else ""
                fallacies_str = (
                    f" [fallacies: {', '.join(fnord.logical_fallacies)}]"
                    if fnord.logical_fallacies
                    else ""
                )

                typer.echo(
                    f"ID {fnord.id}: [{fnord.when}] {fnord.source}: {fnord.summary} @ {where}{notes_str}{fallacies_str}"
                )

            typer.echo(f"\nTotal: {len(fnords)} fnord(s)")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Failed to list fnords")
        raise typer.Exit(1)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging (fnords love gossip)"
    ),
):
    """
    Fnord Tracker - Track the elusive fnords! 🍎✨
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    if verbose:
        logger.debug("Verbose logging enabled. The fnords are talking.")


if __name__ == "__main__":
    app()
