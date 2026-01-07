# Fnord Tracker Web Interface

Modern web interface built with **FastAPI** + **HTMX**.

## Features

- ✅ **Fast API**: FastAPI backend for lightning-fast responses
- 🎨 **HTMX**: No JavaScript required - pure Python interactivity
- 📱 **Responsive**: Works beautifully on desktop and mobile
- 🔍 **Search**: Real-time search as you type
- ✏️ **Edit**: Full editing with multiline fields
- ➕ **Create**: Easy form for adding new fnords
- 🗑️ **Delete**: One-click deletion with confirmation
- 📄 **Pagination**: Browse hundreds of fnords easily

## Running the Web Server

```bash
# From the fnord directory
python -m fnord.web

# Or if you prefer uvicorn explicitly
python -m uvicorn fnord.web.app:app --reload

# The server will be available at:
http://localhost:8000
```

## Using the Interface

### Viewing All Fnords
- Visit `http://localhost:8000`
- Scroll through all your fnord sightings
- Use pagination to navigate
- Search fnords by typing in the search box

### Viewing a Single Fnord
- Click "View/Edit" on any fnord
- See all details in a clean, focused view
- Notes displayed as formatted JSON
- Use "Back to List" to return

### Creating a New Fnord
1. Click "Add New Fnord" button
2. Fill in the form (When, Place, Source, Summary are required)
3. Click "Create Fnord" to save
4. You'll be redirected to the new fnord's detail page

### Editing a Fnord
1. Click "View/Edit" on any fnord
2. Modify any field (they're multiline where appropriate)
3. Click "Save Changes" to update
4. Changes are reflected immediately

### Deleting a Fnord
1. Click "View/Edit" on a fnord
2. Click "Delete Fnord"
3. Confirm the deletion
4. You'll be redirected back to the list

## Architecture

```
fnord/
├── fnord/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py          # SQLite database layer
│   ├── models.py
│   ├── tui.py               # Textual TUI (CLI)
│   └── web/
│       ├── __init__.py
│       ├── app.py             # FastAPI application
│       └── templates/         # Jinja2 HTML templates
│           ├── base.html
│           ├── list.html
│           └── detail.html
└── tests/
    ├── test_tui.py
    └── test_tui_integration.py
```

## Technology Stack

- **Backend**: FastAPI 0.100+ - Modern, fast Python web framework
- **Database**: SQLite - Simple, embedded, no setup required
- **Frontend**: HTMX - Lightweight HTML interactivity without JavaScript
- **Styling**: Tailwind CSS - Utility-first CSS framework
- **Templating**: Jinja2 - Python's powerful template engine
- **Server**: Uvicorn - Lightning-fast ASGI server

## Why This Stack?

- **Modest & Maintainable**: FastAPI + HTMX keeps the codebase simple
- **Fast Development**: No complex JavaScript - just Python templates
- **No Build Step**: Pure Python - runs directly from source
- **Easy to Learn**: HTMX uses HTML attributes you already know
- **Perfect for CRUD**: Your fnord tracker is all about CRUD operations
- **Modern UX**: HTMX provides smooth, app-like interactions
- **Production Ready**: FastAPI is battle-tested and production-ready

## API Endpoints

### HTML Pages
- `GET /` - List all fnords with search and pagination
- `GET /fnord/{id}` - View/edit a specific fnord
- `GET /new` - New fnord form
- `GET /api/stats` - Statistics endpoint

### API Endpoints (POST)
- `POST /fnord/new` - Create a new fnord
- `POST /fnord/{id}` - Update an existing fnord
- `POST /fnord/{id}/delete` - Delete a fnord

## Future Enhancements

- [ ] Dark mode toggle
- [ ] Export fnords to JSON/CSV
- [ ] Bulk edit/delete
- [ ] Advanced search filters
- [ ] Statistics charts
- [ ] WebSocket for real-time updates
- [ ] Authentication (if needed)
