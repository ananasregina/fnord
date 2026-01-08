# Fnord Tracker 🍎✨

> "You are about to see fnord!" - The Illuminatus! Trilogy

A fnord is something that is seen out of the corner of your eye, but when you turn to look at it directly, it disappears. They are everywhere, and this tool helps you track them for the glory of Eris!

## Features

Hail Discordia! This sacred tool offers multiple modes of fnord interaction:

### 🖥️ CLI (Command Line Interface)
Quick one-shot commands for the busy Discordian:
- `fnord ingest` - Record a fnord sighting
- `fnord count` - Query the total fnord count (23 is sacred)
- `fnord list` - View all fnord sightings

### 🤖 MCP (Model Context Protocol) Server
For AI agents and LLMs to communicate with the fnord realm:
- `query_fnord_count` - Get the sacred count
- `ingest_fnord` - Add new fnord observations
- Runs via `fnord --mcp` flag

### 🌐 Web Interface
Modern web interface built with FastAPI + HTMX:
- Beautiful, responsive UI
- Create, View, Edit, Delete fnords
- Real-time search as you type
- Multiline editing for summary and notes
- Pagination for browsing large collections
- Works in any modern browser
- No JavaScript required - pure Python!
- Launch with `fnord web` or `python -m fnord.web`

## Installation

```bash
# Using uv (recommended by Eris herself)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

### Web Interface
```bash
# Launch web server
fnord web

# Or run directly with uvicorn
python -m fnord.web

# Visit in browser
open http://localhost:8000
```
```

## Data Model

Each fnord sighting contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `when` | ISO8601 datetime | ✅ | When the fnord appeared |
| `where_place_name` | string or None | ❌ | Location description (whatever you consider location) |
| `source` | string | ✅ | Where you found it (News, Walk, Code, etc.) |
| `summary` | string | ✅ | Brief description of the fnord |
| `notes` | JSON or None | ❌ | Additional metadata (URL, author, etc.) |

## Configuration

The fnord database location follows this sacred hierarchy:

1. `FNORD_DB_PATH` environment variable (highest priority)
2. `.env` file's `FNORD_DB_PATH` value
3. `./fnord.db` (current directory - default)
4. `~/.config/fnord/fnord.db` (the fnord sanctuary)

Copy `.env.example` to `.env` and customize as needed.

## Discordian References

This code is blessed by Eris and contains hidden gems:

- **23**: The sacred number appears throughout
- **Fnord**: The invisible word that controls your mind
- **Law of Fives**: All events are related to the number 5
- **The Apple**: Sacred symbol of Discordia
- **Greyface**: Beware his curse of order!

## Testing

Hail testing! The fnords demand rigorous verification:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fnord --cov-report=html

# Run specific test file
pytest tests/test_database.py

# Run with verbose output
pytest -v
```

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run linting
ruff check fnord/ tests/

# Run type checking
mypy fnord/

# Format code
ruff format fnord/ tests/
```

## License

**WTFPL** - Do What The Fuck You Want To Public License

The fnords don't care about licenses. Neither should you.

## Credits

- Inspired by *The Illuminatus! Trilogy* by Robert Shea and Robert Anton Wilson
- Built for Discordians everywhere
- May your fnords always be found

---

> "It is my firm belief that it is a mistake to hold firm beliefs."
> — Malaclypse the Younger, Principia Discordia

## MCP Server Usage

For AI agents and LLM integration:

```bash
# Start the MCP server
fnord --mcp

# The server exposes these tools:
# 1. query_fnord_count() -> int
# 2. ingest_fnord(data: dict) -> dict
```

---

**Remember: A fnord is something that you see out of the corner of your eye, but when you turn to look at it directly, it disappears.** 🍎✨
