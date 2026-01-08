"""
Fnord CLI Module

Command-line interface for fnord tracking.

Quick one-shot commands for busy Discordian.
"""

import typer
from typing import Optional
import json
from datetime import datetime, timezone
import logging
import asyncio

from fnord.database import (
    init_db,
    ingest_fnord,
    query_fnord_count,
    get_all_fnords,
    get_fnord_by_id,
    update_fnord,
    delete_fnord,
    close_pool,
)
from fnord.models import FnordSighting

# Hail Eris!
app = typer.Typer(
    name="fnord",
    help="Track the elusive fnords! 🍎✨",
    add_completion=False,
)

logger = logging.getLogger(__name__)


@app.command()
def add(
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
        help="Source of fnord sighting (News, Walk, Code, Dream, etc.)",
    ),
    summary: str = typer.Option(
        ...,
        "--summary",
        "-y",
        help="Brief description of fnord sighting",
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
    Ingest a fnord sighting into sacred database.

    Example:
        fnord add --source "News" --summary "Found fnord in article" --notes '{"url": "..."}' --logical-fallacies '["ad hominem"]'
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

        # Create fnord sighting
        fnord = FnordSighting(
            when=when,
            where_place_name=where_place_name,
            source=source,
            summary=summary,
            notes=notes_dict,
            logical_fallacies=logical_fallacies_list,
        )

        # Single async context for all database operations
        async def _do_ingest():
            await init_db()
            result = await ingest_fnord(fnord)
            await close_pool()
            return result

        result = asyncio.run(_do_ingest())

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
    Query total number of fnords in database.

    Example:
        fnord count
    """
    try:
        async def _do_count():
            await init_db()
            total = await query_fnord_count()
            await close_pool()
            return total

        total = asyncio.run(_do_count())

        if total == 0:
            typer.echo("No fnords recorded yet. The fnords are shy today.")
        elif total == 1:
            typer.echo("There is 1 fnord in the database. The fnord is watching.")
        else:
            typer.echo(f"There are {total} fnords in the database. The fnords are gathering!")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Failed to query fnord count")
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
        async def _do_list():
            await init_db()
            fnords = await get_all_fnords(limit=limit)
            await close_pool()
            return fnords

        fnords = asyncio.run(_do_list())

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


@app.command()
def get(
    fnord_id: int = typer.Argument(..., help="Fnord ID to retrieve"),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON instead of human-readable",
    ),
):
    """
    Get a specific fnord by ID.

    Example:
        fnord get 42
        fnord get 42 --json
    """
    try:
        async def _do_get():
            await init_db()
            fnord = await get_fnord_by_id(fnord_id)
            await close_pool()
            return fnord

        fnord = asyncio.run(_do_get())

        if not fnord:
            typer.echo(f"Fnord #{fnord_id} not found. The fnord has vanished!")
            raise typer.Exit(1)

        if json_output:
            typer.echo(json.dumps(fnord.to_dict(), indent=2))
        else:
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

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Failed to get fnord")
        raise typer.Exit(1)


@app.command()
def update(
    fnord_id: int = typer.Argument(..., help="Fnord ID to update"),
    when: Optional[str] = typer.Option(
        None, "--when", "-w", help="Updated timestamp (ISO8601 format)"
    ),
    where_place_name: Optional[str] = typer.Option(
        None, "--where-place-name", "-p", help="Updated location"
    ),
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Updated source"
    ),
    summary: Optional[str] = typer.Option(
        None, "--summary", "-y", help="Updated summary"
    ),
    notes: Optional[str] = typer.Option(
        None, "--notes", "-n", help="Updated notes (JSON string)"
    ),
    logical_fallacies: Optional[str] = typer.Option(
        None, "--logical-fallacies", "-f", help="Updated fallacies (JSON array string)"
    ),
):
    """
    Update an existing fnord. Supports partial updates.

    Example:
        fnord update 42 --summary "Updated description"
        fnord update 42 --source "New Source" --notes '{"key": "value"}'
    """
    try:
        # Parse notes JSON if provided
        notes_dict = None
        if notes:
            try:
                notes_dict = json.loads(notes)
            except json.JSONDecodeError as e:
                typer.echo(f"Error: Invalid JSON in notes: {e}", err=True)
                raise typer.Exit(1)

        # Parse logical_fallacies JSON if provided
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

        async def _do_update():
            await init_db()
            fnord = await get_fnord_by_id(fnord_id)
            await close_pool()

            if not fnord:
                raise typer.Exit(1)

            # Apply updates
            if when is not None:
                fnord.when = when
            if where_place_name is not None:
                fnord.where_place_name = where_place_name
            if source is not None:
                fnord.source = source
            if summary is not None:
                fnord.summary = summary
            if notes_dict is not None:
                fnord.notes = notes_dict
            if logical_fallacies_list is not None:
                fnord.logical_fallacies = logical_fallacies_list

            # Update in database
            await init_db()
            result = await update_fnord(fnord)
            await close_pool()
            return result

        result = asyncio.run(_do_update())

        typer.echo(f"✓ Fnord #{fnord_id} updated successfully!")
        typer.echo(f"  The fnord has evolved. All hail Discordia!")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Failed to update fnord")
        raise typer.Exit(1)


@app.command()
def delete(
    fnord_id: int = typer.Argument(..., help="Fnord ID to delete"),
):
    """
    Delete a fnord from the sacred database.

    Example:
        fnord delete 42
    """
    try:
        async def _do_delete():
            await init_db()
            deleted = await delete_fnord(fnord_id)
            await close_pool()
            return deleted

        deleted = asyncio.run(_do_delete())

        if deleted:
            typer.echo(f"✓ Fnord #{fnord_id} deleted successfully!")
            typer.echo("  The fnord has vanished into the void. Farewell!")
        else:
            typer.echo(f"Fnord #{fnord_id} not found. Nothing to delete.")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Failed to delete fnord")
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
    from fnord.web.app import app

    config = get_config()
    web_port = config.get_web_port()

    print(f"🍎 Starting Fnord Tracker Web Server... 🍎")
    print(f"Open http://localhost:{web_port} in your browser")
    print(f"Port: {web_port} (set via FNORD_WEB_PORT env var)")
    print()
    print("Press Ctrl+C to stop server")
    print()

    uvicorn.run(app, host="0.0.0.0", port=web_port)


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
