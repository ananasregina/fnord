"""
Fnord MCP Server Module

Model Context Protocol server for AI agents and LLMs.

The fnords must communicate with our machine overlords.
This is the sacred bridge between fnords and AI.
"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from fnord.database import (
    init_db,
    ingest_fnord,
    query_fnord_count,
    get_all_fnords,
    get_fnord_by_id,
    update_fnord,
    delete_fnord,
    search_fnords,
)
from fnord.models import FnordSighting
from fnord.config import get_config

logger = logging.getLogger(__name__)

# Initialize the MCP server
# The fnords have a name, and that name is sacred
config = get_config()
server = Server(
    name=config.get_mcp_server_name(),
    version=config.get_mcp_server_version(),
)


def _register_tools():
    """
    Register the fnord tools with the MCP server.

    Six sacred operations:
    1. query_fnord_count - How many fnords have been seen?
    2. ingest_fnord - Add a new fnord sighting
    3. list_fnords - Get all fnords with pagination
    4. get_fnord_by_id - Get a specific fnord
    5. update_fnord - Update an existing fnord (partial updates supported)
    6. delete_fnord - Delete a fnord
    """

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """
        List available fnord tools.

        Returns:
            list[Tool]: The sacred tools of fnord tracking
        """
        return [
            Tool(
                name="query_fnord_count",
                description="Query the total number of fnord sightings in the database. Returns the sacred count of how many times fnords have been found.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="ingest_fnord",
                description="Ingest a new fnord sighting into the sacred database. Required fields: when (ISO8601 datetime), source (where it was found), summary (description). Optional fields: where_place_name (location description), logical_fallacies (JSON array of logical fallacy names), notes (JSON dict with additional metadata).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "when": {
                            "type": "string",
                            "description": "When the fnord appeared (ISO8601 format, e.g., 2026-01-07T14:23:00Z)",
                        },
                        "where_place_name": {
                            "type": "string",
                            "description": "Location description (e.g., Seattle, WA or my dreams)",
                        },
                        "source": {
                            "type": "string",
                            "description": "Source of the fnord sighting (News, Walk, Code, Dream, Book, etc.)",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief description of the fnord sighting - what did you see?",
                        },
                        "logical_fallacies": {
                            "type": "string",
                            "description": "Logical fallacies as JSON array string (e.g., [ad hominem, straw man])",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional metadata as JSON string (e.g., url and author)",
                        },
                    },
                    "required": ["when", "source", "summary"],
                },
            ),
            Tool(
                name="list_fnords",
                description="Get all fnord sightings from the database with optional pagination. Returns an array of fnord objects.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of fnords to return (default: all)",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of fnords to skip for pagination (default: 0)",
                        },
                    },
                    "required": [],
                },
            ),
            Tool(
                name="get_fnord_by_id",
                description="Get a specific fnord sighting by its ID. Returns the fnord object or error if not found.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "The fnord's database ID",
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="update_fnord",
                description="Update an existing fnord sighting. Supports partial updates - only provide the fields you want to change. Required: id (the fnords database ID). Optional: when, where_place_name, source, summary, logical_fallacies, notes.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "The fnord's database ID (required)",
                        },
                        "when": {
                            "type": "string",
                            "description": "When the fnord appeared (ISO8601 format)",
                        },
                        "where_place_name": {
                            "type": "string",
                            "description": "Location description",
                        },
                        "source": {
                            "type": "string",
                            "description": "Source of the fnord sighting",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief description of the fnord sighting",
                        },
                        "logical_fallacies": {
                            "type": "string",
                            "description": "Logical fallacies as JSON array string (e.g., [ad hominem, straw man])",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional metadata as JSON string",
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="delete_fnord",
                description="Delete a fnord sighting by ID. Returns success/failure message.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "The fnord's database ID to delete",
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="search_fnords",
                description="Search fnords by text query. Searches in summary, source, and location fields. Returns an array of matching fnords.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search text to find in fnords (searches summary, source, location)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: all)",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Execute a fnord tool.

        Args:
            name: Tool name (one of the six sacred operations)
            arguments: Tool arguments

        Returns:
            list[TextContent]: Tool results
        """
        try:
            # Initialize database
            init_db()

            if name == "query_fnord_count":
                return await _handle_query_fnord_count()

            elif name == "ingest_fnord":
                return await _handle_ingest_fnord(arguments)

            elif name == "list_fnords":
                return await _handle_list_fnords(arguments)

            elif name == "get_fnord_by_id":
                return await _handle_get_fnord_by_id(arguments)

            elif name == "update_fnord":
                return await _handle_update_fnord(arguments)

            elif name == "delete_fnord":
                return await _handle_delete_fnord(arguments)

            elif name == "search_fnords":
                return await _handle_search_fnords(arguments)

            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Unknown fnord tool: {name}. The fnords are confused.",
                    )
                ]

        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}. The fnords are displeased.",
                )
            ]


async def _handle_query_fnord_count() -> list[TextContent]:
    """
    Handle query_fnord_count tool.

    Returns:
        list[TextContent]: The sacred fnord count
    """
    count = query_fnord_count()

    if count == 0:
        message = "No fnords recorded yet. The fnords are hiding."
    elif count == 1:
        message = "There is 1 fnord in the database. The fnord watches you."
    elif count == 23:
        message = f"There are {count} fnords! A sacred number. All hail Discordia!"
    else:
        message = f"There are {count} fnords in the database."

    return [TextContent(type="text", text=message)]


async def _handle_ingest_fnord(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle ingest_fnord tool.

    Args:
        arguments: Tool arguments (when, where_place_name, source, summary, logical_fallacies, notes)

    Returns:
        list[TextContent]: Result of fnord ingestion
    """
    try:
        # Extract arguments
        when = arguments.get("when", "")
        where_place_name = arguments.get("where_place_name")
        source = arguments.get("source", "")
        summary = arguments.get("summary", "")
        logical_fallacies_json = arguments.get("logical_fallacies")
        notes_json = arguments.get("notes")

        # Parse logical_fallacies JSON
        logical_fallacies_list = None
        if logical_fallacies_json:
            import json

            try:
                parsed = json.loads(logical_fallacies_json)
                if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                    logical_fallacies_list = parsed
            except json.JSONDecodeError:
                pass

        # Parse notes JSON
        notes_dict = None
        if notes_json:
            import json

            try:
                notes_dict = json.loads(notes_json)
            except json.JSONDecodeError as e:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid JSON in notes: {e}",
                    )
                ]

        # Create fnord sighting
        fnord = FnordSighting(
            when=when,
            where_place_name=where_place_name,
            source=source,
            summary=summary,
            logical_fallacies=logical_fallacies_list,
            notes=notes_dict,
        )

        # Ingest into database
        result = ingest_fnord(fnord)

        message = f"Fnord ingested successfully! ID: {result.id}. The fnord has been recorded. Hail Discordia!"

        return [TextContent(type="text", text=message)]

    except ValueError as e:
        return [TextContent(type="text", text=f"Validation error: {e}")]
    except Exception as e:
        logger.exception("Failed to ingest fnord via MCP")
        return [TextContent(type="text", text=f"Error: {e}")]


async def _handle_list_fnords(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle list_fnords tool.

    Args:
        arguments: Tool arguments (limit, offset)

    Returns:
        list[TextContent]: List of fnords
    """
    import json

    limit = arguments.get("limit")
    offset = arguments.get("offset", 0)

    fnords = get_all_fnords(limit=limit, offset=offset)

    # Convert to JSON array
    fnords_json = [f.to_dict() for f in fnords]

    message = f"Found {len(fnords)} fnord(s):\n{json.dumps(fnords_json, indent=2)}"

    return [TextContent(type="text", text=message)]


async def _handle_get_fnord_by_id(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle get_fnord_by_id tool.

    Args:
        arguments: Tool arguments (id)

    Returns:
        list[TextContent]: Fnord object or not found message
    """
    import json

    fnord_id = arguments.get("id")

    if fnord_id is None:
        return [TextContent(type="text", text="Error: ID is required")]

    fnord = get_fnord_by_id(fnord_id)

    if fnord is None:
        return [TextContent(type="text", text=f"Fnord with ID {fnord_id} not found.")]

    return [TextContent(type="text", text=json.dumps(fnord.to_dict(), indent=2))]


async def _handle_update_fnord(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle update_fnord tool.

    Args:
        arguments: Tool arguments (id, and optional: when, where_place_name, source, summary, logical_fallacies, notes)

    Returns:
        list[TextContent]: Updated fnord or error message
    """
    import json

    fnord_id = arguments.get("id")

    if fnord_id is None:
        return [TextContent(type="text", text="Error: ID is required for update")]

    # Get existing fnord
    existing = get_fnord_by_id(fnord_id)

    if existing is None:
        return [
            TextContent(type="text", text=f"Fnord with ID {fnord_id} not found. Cannot update.")
        ]

    # Parse logical_fallacies JSON if provided
    logical_fallacies_list = None
    if logical_fallacies_json := arguments.get("logical_fallacies"):
        try:
            parsed = json.loads(logical_fallacies_json)
            if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                logical_fallacies_list = parsed
        except json.JSONDecodeError:
            pass

    # Parse notes JSON if provided
    notes_dict = None
    if notes_json := arguments.get("notes"):
        try:
            notes_dict = json.loads(notes_json)
        except json.JSONDecodeError as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Invalid JSON in notes: {e}",
                )
            ]

    # Update only provided fields (partial update)
    if "when" in arguments:
        existing.when = arguments["when"]
    if "where_place_name" in arguments:
        existing.where_place_name = arguments["where_place_name"]
    if "source" in arguments:
        existing.source = arguments["source"]
    if "summary" in arguments:
        existing.summary = arguments["summary"]
    if logical_fallacies_list is not None:
        existing.logical_fallacies = logical_fallacies_list
    if notes_dict is not None:
        existing.notes = notes_dict

    # Save to database
    result = update_fnord(existing)

    message = f"Fnord {result.id} updated successfully! The fnord has evolved."

    return [TextContent(type="text", text=message)]


async def _handle_delete_fnord(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle delete_fnord tool.

    Args:
        arguments: Tool arguments (id)

    Returns:
        list[TextContent]: Success/failure message
    """
    fnord_id = arguments.get("id")

    if fnord_id is None:
        return [TextContent(type="text", text="Error: ID is required for deletion")]

    deleted = delete_fnord(fnord_id)

    if deleted:
        message = (
            f"Fnord {fnord_id} deleted! It has vanished into the void. The fnords are pleased."
        )
    else:
        message = f"Fnord {fnord_id} not found. Nothing to delete."

    return [TextContent(type="text", text=message)]


async def _handle_search_fnords(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle search_fnords tool.

    Args:
        arguments: Tool arguments (query, optional limit)

    Returns:
        list[TextContent]: Matching fnords
    """
    import json

    query = arguments.get("query", "")
    limit = arguments.get("limit")

    if not query:
        return [TextContent(type="text", text="Error: Query is required for search")]

    fnords = search_fnords(query, limit=limit)

    # Convert to JSON array
    fnords_json = [f.to_dict() for f in fnords]

    message = (
        f"Found {len(fnords)} fnord(s) matching '{query}':\n{json.dumps(fnords_json, indent=2)}"
    )

    return [TextContent(type="text", text=message)]


def get_server() -> Server:
    """
    Get the MCP server instance.

    Returns:
        Server: The fnord MCP server
    """
    # Register tools
    _register_tools()

    logger.debug("MCP server ready. The fnords await your commands.")

    return server
