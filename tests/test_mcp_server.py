"""
Tests for fnord MCP server.

The fnords must speak to AI. We test MCP protocol.
"""

import pytest
import json
from fnord.database import ingest_fnord, init_db, update_fnord, get_all_fnords
from fnord.models import FnordSighting
from fnord.mcp_server import get_server


class TestMCPServer:
    """Test MCP server initialization."""

    def test_get_server(self):
        """Test getting MCP server."""
        server = get_server()

        assert server is not None
        assert server.name == "fnord-tracker"

    @pytest.mark.asyncio
    async def test_list_tools(self, initialized_db):
        """Test listing available tools."""
        server = get_server()

        tools = server.list_tools()

        assert len(tools) == 7  # Seven sacred operations (6 + search_fnords)

        tool_names = [tool.name for tool in tools]
        assert "query_fnord_count" in tool_names
        assert "ingest_fnord" in tool_names
        assert "list_fnords" in tool_names
        assert "get_fnord_by_id" in tool_names
        assert "update_fnord" in tool_names
        assert "delete_fnord" in tool_names
        assert "search_fnords" in tool_names

    @pytest.mark.asyncio
    async def test_query_fnord_count_tool_schema(self, initialized_db):
        """Test that query_fnord_count tool has correct schema."""
        server = get_server()
        tools = server.list_tools()

        count_tool = next(t for t in tools if t.name == "query_fnord_count")

        assert count_tool.description is not None
        assert count_tool.inputSchema == {"type": "object", "properties": {}, "required": []}

    @pytest.mark.asyncio
    async def test_ingest_fnord_tool_schema(self, initialized_db):
        """Test that ingest_fnord tool has correct schema."""
        server = get_server()
        tools = server.list_tools()

        ingest_tool = next(t for t in tools if t.name == "ingest_fnord")

        assert ingest_tool.description is not None
        schema = ingest_tool.inputSchema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "when" in schema["properties"]
        assert "source" in schema["properties"]
        assert "summary" in schema["properties"]
        assert "where_place_name" in schema["properties"]
        assert "notes" in schema["properties"]

        # Check required fields
        assert set(schema["required"]) == {"when", "source", "summary"}

    @pytest.mark.asyncio
    async def test_list_fnords_tool_schema(self, initialized_db):
        """Test that list_fnords tool has correct schema."""
        server = get_server()
        tools = server.list_tools()

        list_tool = next(t for t in tools if t.name == "list_fnords")

        assert list_tool.description is not None
        schema = list_tool.inputSchema

        assert schema["type"] == "object"
        assert "limit" in schema["properties"]
        assert "offset" in schema["properties"]
        assert schema["required"] == []

    @pytest.mark.asyncio
    async def test_update_fnord_tool_schema(self, initialized_db):
        """Test that update_fnord tool has correct schema."""
        server = get_server()
        tools = server.list_tools()

        update_tool = next(t for t in tools if t.name == "update_fnord")

        assert update_tool.description is not None
        schema = update_tool.inputSchema

        assert schema["type"] == "object"
        assert "id" in schema["properties"]
        assert "id" in schema["required"]
        # ID is the only required field (partial updates supported)
        assert schema["required"] == ["id"]


class TestMCPCallTool:
    """Test MCP tool call operations."""

    @pytest.mark.asyncio
    async def test_call_query_fnord_count_empty(self, initialized_db):
        """Test querying fnord count when empty."""
        from fnord.mcp_server import _handle_query_fnord_count

        results = await _handle_query_fnord_count()

        assert len(results) == 1
        assert "No fnords recorded yet" in results[0].text

    @pytest.mark.asyncio
    async def test_call_query_fnord_count_one(self, initialized_db, sample_fnord):
        """Test querying fnord count with one fnord."""
        from fnord.mcp_server import _handle_query_fnord_count

        ingest_fnord(sample_fnord)

        results = await _handle_query_fnord_count()

        assert len(results) == 1
        assert "1 fnord" in results[0].text

    @pytest.mark.asyncio
    async def test_call_query_fnord_count_sacred_number(self, initialized_db):
        """Test querying fnord count with sacred number 23."""
        from fnord.mcp_server import _handle_query_fnord_count

        # Ingest 23 fnords
        for i in range(23):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="Test",
                summary=f"Fnord #{i + 1}",
            )
            ingest_fnord(fnord)

        results = await _handle_query_fnord_count()

        assert len(results) == 1
        assert "23 fnords" in results[0].text
        assert "Sacred" in results[0].text

    @pytest.mark.asyncio
    async def test_call_ingest_fnord_success(self, initialized_db):
        """Test successfully ingesting a fnord via MCP."""
        from fnord.mcp_server import _handle_ingest_fnord

        arguments = {
            "when": "2026-01-07T14:23:00Z",
            "source": "News",
            "summary": "Found fnord in article",
        }

        results = await _handle_ingest_fnord(arguments)

        assert len(results) == 1
        assert "Fnord ingested successfully!" in results[0].text
        assert "ID:" in results[0].text

    @pytest.mark.asyncio
    async def test_call_ingest_fnord_with_location(self, initialized_db):
        """Test ingesting fnord with location via MCP."""
        from fnord.mcp_server import _handle_ingest_fnord

        arguments = {
            "when": "2026-01-07T14:23:00Z",
            "source": "News",
            "summary": "Found fnord",
            "where_place_name": "Seattle, WA",
        }

        results = await _handle_ingest_fnord(arguments)

        assert len(results) == 1
        assert "Fnord ingested successfully!" in results[0].text

    @pytest.mark.asyncio
    async def test_call_ingest_fnord_with_notes(self, initialized_db):
        """Test ingesting fnord with notes via MCP."""
        from fnord.mcp_server import _handle_ingest_fnord

        notes = json.dumps({"url": "https://example.com", "author": "Test"})

        arguments = {
            "when": "2026-01-07T14:23:00Z",
            "source": "News",
            "summary": "Found fnord",
            "notes": notes,
        }

        results = await _handle_ingest_fnord(arguments)

        assert len(results) == 1
        assert "Fnord ingested successfully!" in results[0].text

    @pytest.mark.asyncio
    async def test_call_ingest_fnord_invalid_notes_json(self, initialized_db):
        """Test ingesting fnord with invalid JSON in notes."""
        from fnord.mcp_server import _handle_ingest_fnord

        arguments = {
            "when": "2026-01-07T14:23:00Z",
            "source": "News",
            "summary": "Found fnord",
            "notes": "not-valid-json",
        }

        results = await _handle_ingest_fnord(arguments)

        assert len(results) == 1
        assert "Invalid JSON" in results[0].text

    @pytest.mark.asyncio
    async def test_call_ingest_fnord_missing_required_field(self, initialized_db):
        """Test ingesting fnord without required field."""
        from fnord.mcp_server import _handle_ingest_fnord

        arguments = {
            "when": "2026-01-07T14:23:00Z",
            "summary": "Found fnord",  # Missing "source"
        }

        results = await _handle_ingest_fnord(arguments)

        assert len(results) == 1
        assert "Validation error" in results[0].text

    @pytest.mark.asyncio
    async def test_call_list_fnords(self, initialized_db):
        """Test listing fnords via MCP."""
        from fnord.mcp_server import _handle_list_fnords

        # Create multiple fnords
        for i in range(5):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="Test",
                summary=f"Fnord #{i + 1}",
            )
            ingest_fnord(fnord)

        results = await _handle_list_fnords({})

        assert len(results) == 1
        assert "Found 5 fnord(s)" in results[0].text

    @pytest.mark.asyncio
    async def test_call_list_fnords_with_limit(self, initialized_db):
        """Test listing fnords with limit via MCP."""
        from fnord.mcp_server import _handle_list_fnords

        # Create 30 fnords
        for i in range(30):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="Test",
                summary=f"Fnord #{i + 1}",
            )
            ingest_fnord(fnord)

        results = await _handle_list_fnords({"limit": 10})

        assert len(results) == 1
        assert "Found 10 fnord(s)" in results[0].text

    @pytest.mark.asyncio
    async def test_call_list_fnords_with_offset(self, initialized_db):
        """Test listing fnords with offset via MCP."""
        from fnord.mcp_server import _handle_list_fnords

        # Create 30 fnords
        for i in range(30):
            fnord = FnordSighting(
                when="2026-01-07T14:23:00Z",
                source="Test",
                summary=f"Fnord #{i + 1}",
            )
            ingest_fnord(fnord)

        results = await _handle_list_fnords({"limit": 10, "offset": 20})

        assert len(results) == 1
        assert "Found 10 fnord(s)" in results[0].text

    @pytest.mark.asyncio
    async def test_call_get_fnord_by_id(self, initialized_db, sample_fnord):
        """Test getting fnord by ID via MCP."""
        from fnord.mcp_server import _handle_get_fnord_by_id

        result = ingest_fnord(sample_fnord)

        results = await _handle_get_fnord_by_id({"id": result.id})

        assert len(results) == 1
        assert json.dumps(sample_fnord.to_dict()) in results[0].text

    @pytest.mark.asyncio
    async def test_call_get_fnord_by_id_not_found(self, initialized_db):
        """Test getting fnord that doesn't exist via MCP."""
        from fnord.mcp_server import _handle_get_fnord_by_id

        results = await _handle_get_fnord_by_id({"id": 999})

        assert len(results) == 1
        assert "not found" in results[0].text

    @pytest.mark.asyncio
    async def test_call_update_fnord(self, initialized_db, sample_fnord):
        """Test updating fnord via MCP."""
        from fnord.mcp_server import _handle_update_fnord

        # First ingest a fnord
        result = ingest_fnord(sample_fnord)

        # Update it via MCP (partial update - just summary)
        arguments = {
            "id": result.id,
            "summary": "Updated summary via MCP",
        }

        results = await _handle_update_fnord(arguments)

        assert len(results) == 1
        assert "updated successfully!" in results[0].text

    @pytest.mark.asyncio
    async def test_call_update_fnord_not_found(self, initialized_db):
        """Test updating fnord that doesn't exist via MCP."""
        from fnord.mcp_server import _handle_update_fnord

        arguments = {
            "id": 999,
            "summary": "This won't work",
        }

        results = await _handle_update_fnord(arguments)

        assert len(results) == 1
        assert "not found" in results[0].text

    @pytest.mark.asyncio
    async def test_call_delete_fnord(self, initialized_db, sample_fnord):
        """Test deleting fnord via MCP."""
        from fnord.mcp_server import _handle_delete_fnord

        result = ingest_fnord(sample_fnord)

        results = await _handle_delete_fnord({"id": result.id})

        assert len(results) == 1
        assert "deleted!" in results[0].text
        assert "vanished into the void" in results[0].text

    @pytest.mark.asyncio
    async def test_call_delete_fnord_not_found(self, initialized_db):
        """Test deleting fnord that doesn't exist via MCP."""
        from fnord.mcp_server import _handle_delete_fnord

        results = await _handle_delete_fnord({"id": 999})

        assert len(results) == 1
        assert "not found" in results[0].text

    @pytest.mark.asyncio
    async def test_call_search_fnords(self, initialized_db):
        """Test searching fnords via MCP."""
        from fnord.mcp_server import _handle_search_fnords

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
            ),
        ]

        for fnord in fnords:
            ingest_fnord(fnord)

        results = await _handle_search_fnords({"query": "graffiti"})

        assert len(results) == 1
        assert "Found 1 fnord(s)" in results[0].text
        assert "graffiti" in results[0].text.lower()

    @pytest.mark.asyncio
    async def test_call_search_fnords_no_results(self, initialized_db):
        """Test search with no results via MCP."""
        from fnord.mcp_server import _handle_search_fnords

        # Create a fnord
        fnord = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Found fnord",
        )
        ingest_fnord(fnord)

        results = await _handle_search_fnords({"query": "nonexistent fnord xyz123"})

        assert len(results) == 1
        assert "Found 0 fnord(s)" in results[0].text


class TestMCPServerIntegration:
    """Integration tests for MCP server."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, initialized_db):
        """Test full MCP workflow: ingest, list, update, delete."""
        from fnord.mcp_server import (
            _handle_query_fnord_count,
            _handle_ingest_fnord,
            _handle_list_fnords,
            _handle_update_fnord,
            _handle_delete_fnord,
        )

        # First, query count (should be 0)
        results = await _handle_query_fnord_count()
        assert "No fnords" in results[0].text

        # Ingest a fnord
        ingest_args = {
            "when": "2026-01-07T14:23:00Z",
            "source": "News",
            "summary": "Found fnord",
        }
        await _handle_ingest_fnord(ingest_args)

        # List fnords (should be 1)
        results = await _handle_list_fnords({})
        assert "Found 1 fnord(s)" in results[0].text

        # Update it
        # Get ID from list result
        import json

        list_data = json.loads(results[0].text.split("\n")[1])
        fnord_id = list_data[0]["id"]

        update_args = {
            "id": fnord_id,
            "summary": "Updated summary",
        }
        await _handle_update_fnord(update_args)
        assert "updated successfully!" in update_args

        # Delete it
        delete_args = {"id": fnord_id}
        await _handle_delete_fnord(delete_args)
        assert "deleted!" in delete_args

        # Query count again (should be 0)
        results = await _handle_query_fnord_count()
        assert "No fnords" in results[0].text

    @pytest.mark.asyncio
    async def test_partial_update(self, initialized_db):
        """Test that partial updates work correctly via MCP."""
        from fnord.mcp_server import _handle_update_fnord

        # Create a fnord with all fields
        original = FnordSighting(
            when="2026-01-07T14:23:00Z",
            source="News",
            summary="Original summary",
            where_place_name="Seattle",
            notes={"url": "https://example.com"},
        )

        result = ingest_fnord(original)

        # Update only summary
        update_args = {
            "id": result.id,
            "summary": "Updated summary only",
        }
        await _handle_update_fnord(update_args)

        # Verify update
        updated = get_all_fnords()[0]
        assert updated.summary == "Updated summary only"
        assert updated.source == "News"  # Unchanged
        assert updated.where_place_name == "Seattle"  # Unchanged
        assert updated.notes == {"url": "https://example.com"}  # Unchanged
