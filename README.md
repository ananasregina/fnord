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

### Prerequisites

Before installing, ensure you have:

1. **PostgreSQL 15+ with pgvector extension**
   - See [POSTGRES_SETUP.md](POSTGRES_SETUP.md) for detailed installation guide
   - Create database and user for fnord
   - Enable pgvector extension

2. **LM Studio running with embedding model**
   - Ensure LM Studio is running locally
   - Model should be loaded and accessible via API

### Install Dependencies

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Configuration

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
# Edit .env with your settings
```

### Environment Variables

**PostgreSQL Database Configuration:**
```bash
FNORD_DB_HOST=localhost
FNORD_DB_PORT=5432
FNORD_DB_NAME=fnord
FNORD_DB_USER=fnord_user
FNORD_DB_PASSWORD=your_secure_password
```

**LM Studio Embeddings (for semantic search):**
```bash
EMBEDDING_URL=http://127.0.0.1:1338/v1
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5-embedding
EMBEDDING_DIMENSION=768
```

**Other Configuration:**
- `FNORD_MCP_NAME`, `FNORD_MCP_VERSION` - MCP server settings
- `FNORD_WEB_PORT` - Web server port
- `FNORD_LOG_LEVEL` - Logging level

### Database Setup

After configuring `.env`, initialize the database:

```bash
# Initialize PostgreSQL schema
fnord init-db
```

This will:
- Create the `fnords` table with vector support
- Create IVFFlat vector index for fast semantic search
- Enable pgvector extension

## Quick Start

### Web Interface
```bash
# Launch web server
fnord web

# Or run directly with uvicorn
python -m fnord.web
```

Visit: http://localhost:8000

## Features

- **Semantic Search**: Search fnords by meaning, not exact text matching
- **Vector Embeddings**: Powered by LM Studio local models
- **Chaos Energy**: 1/23 chance to skip IDs (still sacred!)
- **Pagination**: Browse fnords in pages of 23

## Data Model

Each fnord sighting contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `when` | TIMESTAMP | ✅ | When the fnord appeared |
| `where_place_name` | TEXT | ❌ | Location description |
| `source` | TEXT | ✅ | Where you found it |
| `summary` | TEXT | ✅ | Brief description |
| `notes` | JSONB | ❌ | Additional metadata |
| `logical_fallacies` | JSONB | ❌ | Logical fallacies array |
| `embedding` | VECTOR(768) | ✅ | Semantic embedding vector |

## Discordian References

This code is blessed by Eris and contains hidden gems:

- **23**: The sacred number appears throughout
- **Fnord**: The invisible word that controls your mind
- **Law of Fives**: All events are related to the number 5
- **The Apple**: Sacred symbol of Discordia
- **Greyface**: Beware his curse of order!

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fnord --cov-report=html

# Run specific test file
pytest tests/test_database.py -v
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

> **"It is my firm belief that it is a mistake to hold firm beliefs."**
> — Malaclypse the Younger, Principia Discordia


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
