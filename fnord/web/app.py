"""
FastAPI web application for fnord tracker.

Modern, fast web interface with HTMX for interactivity.
No JavaScript required - Python + HTMX handles everything.
"""

import json
from datetime import datetime, UTC
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fnord.database import (
    get_all_fnords,
    get_fnord_by_id,
    ingest_fnord,
    update_fnord as update_fnord_db,
    delete_fnord as delete_fnord_db,
    search_fnords,
    query_fnord_count,
)
from fnord.models import FnordSighting

app = FastAPI(title="🍎 Fnord Tracker 🍎", version="23.5.0")

# Setup templates
templates = Jinja2Templates(directory="fnord/web/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = 1, search: Optional[str] = None):
    """
    Main page - list all fnords with search and pagination.

    The fnords await their audience.
    """
    limit = 23
    offset = (page - 1) * limit

    if search:
        fnords = search_fnords(search, limit=limit, offset=offset)
    else:
        fnords = get_all_fnords(limit=limit, offset=offset)

    total_count = query_fnord_count()
    total_pages = (total_count + limit - 1) // limit

    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "fnords": fnords,
            "page": page,
            "total_pages": total_pages,
            "search_query": search or "",
            "total_count": total_count,
        },
    )


@app.get("/fnord/{fnord_id}", response_class=HTMLResponse)
async def detail(request: Request, fnord_id: int):
    """
    Detail page - view/edit a specific fnord.

    The fnord reveals itself in full glory.
    """
    from fnord.database import get_db_connection

    fnord = None
    with get_db_connection() as conn:
        fnord = get_fnord_by_id(fnord_id)

    if not fnord:
        raise HTTPException(status_code=404, detail="Fnord not found!")

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "fnord": fnord,
            "is_new": False,
        },
    )


@app.get("/new", response_class=HTMLResponse)
async def new_fnord(request: Request):
    """
    New fnord form page.

    Prepare to welcome a new fnord.
    """
    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "fnord": None,
            "is_new": True,
        },
    )


@app.post("/fnord/{fnord_id}")
async def update_fnord_route(
    request: Request,
    fnord_id: int,
    when: str = Form(...),
    where_place_name: Optional[str] = Form(None),
    source: str = Form(...),
    summary: str = Form(...),
    logical_fallacies: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    """
    Update an existing fnord.

    The fnord evolves.
    """
    from fnord.database import get_db_connection

    fnord = None
    with get_db_connection() as conn:
        fnord = get_fnord_by_id(fnord_id)

    if not fnord:
        raise HTTPException(status_code=404, detail="Fnord not found!")

    # Parse logical_fallacies if provided
    logical_fallacies_list = None
    if logical_fallacies and logical_fallacies.strip():
        try:
            parsed = json.loads(logical_fallacies)
            if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                logical_fallacies_list = parsed
        except json.JSONDecodeError:
            pass

    # Parse notes if provided
    notes_dict = None
    if notes and notes.strip():
        try:
            notes_dict = json.loads(notes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in notes!")

    # Update the fnord
    fnord.when = when
    fnord.where_place_name = where_place_name if where_place_name else None
    fnord.source = source
    fnord.summary = summary
    fnord.logical_fallacies = logical_fallacies_list
    fnord.notes = notes_dict

    update_fnord_db(fnord)

    # Redirect back to detail page
    return RedirectResponse(f"/fnord/{fnord_id}", status_code=303)


@app.post("/fnord/new")
async def create_fnord(
    request: Request,
    when: str = Form(...),
    where_place_name: Optional[str] = Form(None),
    source: str = Form(...),
    summary: str = Form(...),
    logical_fallacies: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    """
    Create a new fnord.

    A new fnord enters the realm.
    """
    # Parse logical_fallacies if provided
    logical_fallacies_list = None
    if logical_fallacies and logical_fallacies.strip():
        try:
            parsed = json.loads(logical_fallacies)
            if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                logical_fallacies_list = parsed
        except json.JSONDecodeError:
            pass

    # Parse notes if provided
    notes_dict = None
    if notes and notes.strip():
        try:
            notes_dict = json.loads(notes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in notes!")

    # Create the fnord
    fnord = FnordSighting(
        when=when,
        where_place_name=where_place_name if where_place_name else None,
        source=source,
        summary=summary,
        logical_fallacies=logical_fallacies_list,
        notes=notes_dict,
    )

    result = ingest_fnord(fnord)

    # Redirect to detail page
    return RedirectResponse(f"/fnord/{result.id}", status_code=303)


@app.post("/fnord/{fnord_id}/delete")
async def delete_fnord_route(request: Request, fnord_id: int):
    """
    Delete a fnord.

    The fnord returns to the void.
    """
    delete_fnord_db(fnord_id)

    # Redirect to home
    return RedirectResponse("/", status_code=303)


@app.get("/api/stats")
async def stats():
    """
    API endpoint for statistics.

    Numbers that fnords care about.
    """
    count = query_fnord_count()

    return {
        "total_fnords": count,
        "sacred_number": 23,
        "is_sacred": count == 23,
    }


# Mount static files
# In production, use proper static file serving
# app.mount("/static", StaticFiles(directory="fnord/web/static"), name="static")
