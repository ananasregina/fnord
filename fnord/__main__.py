"""
Fnord Tracker - Main Entry Point

The fnords have many ways to commune:
- CLI: Quick one-shot commands
- MCP: Server for AI agents

This module decides which path to take.
"""

import sys
import asyncio
import logging
from typing import NoReturn

from fnord.cli import app as cli_app
from fnord.mcp_server import get_server
from fnord.database import init_db

logger = logging.getLogger(__name__)


def main() -> NoReturn:
    """
    Main entry point for the fnord tracker.

    Dispatches to:
    - CLI mode (default)
    - MCP server mode (--mcp flag)

    All paths lead to fnord tracking!
    """
    # Check for --mcp flag (must be before Typer parsing)
    if "--mcp" in sys.argv or "-m" in sys.argv:
        # MCP server mode
        _run_mcp_server()
    else:
        # CLI mode
        try:
            cli_app()
        except SystemExit:
            # Typer calls sys.exit, which is normal
            pass


def _run_mcp_server() -> NoReturn:
    """
    Run the MCP server.

    The fnords communicate with AI through this sacred channel.
    """
    import mcp.server.stdio

    # Initialize database
    init_db()

    # Get the MCP server
    server = get_server()

    # Run the server
    logger.info("Starting fnord MCP server... All hail Discordia!")

    # Run the stdio server (async)
    async def run_server():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run_server())

    # Should never reach here
    sys.exit(0)


if __name__ == "__main__":
    main()
