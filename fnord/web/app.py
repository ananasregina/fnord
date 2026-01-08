"""
FastAPI web application for fnord tracker.

Modern, fast web interface with HTMX for interactivity.
No JavaScript required - Python + HTMX handles everything.
"""

import asyncio
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
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
from fnord.config import get_config

app = FastAPI(title="🍎 Fnord Tracker 🍎", version="23.5.0")

# Setup templates and static files with absolute paths
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = 1, search: Optional[str] = None):
    """
    Main page - list all fnords with search and pagination.

    The fnords await their audience.
    """
    limit = 23
    offset = (page - 1) * limit

    if search:
        fnords = await search_fnords(search, limit=limit, offset=offset)
    else:
        fnords = await get_all_fnords(limit=limit, offset=offset)

    total_count = await query_fnord_count()
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
    fnord = await get_fnord_by_id(fnord_id)

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
    fnord = await get_fnord_by_id(fnord_id)

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

    result = await ingest_fnord(fnord)

    # Redirect to detail page
    return RedirectResponse(f"/fnord/{result.id}", status_code=303)


@app.post("/fnord/{fnord_id}/delete")
async def delete_fnord_route(request: Request, fnord_id: int):
    """
    Delete a fnord.

    The fnord returns to the void.
    """
    await delete_fnord_db(fnord_id)

    # Redirect to home
    return RedirectResponse("/", status_code=303)


@app.get("/api/stats")
async def stats():
    """
    API endpoint for statistics.

    Numbers that fnords care about.
    """
    count = await query_fnord_count()

    return {
        "total_fnords": count,
        "sacred_number": 23,
        "is_sacred": count == 23,
    }


@app.get("/events")
async def fnord_events():
    """
    SSE endpoint for real-time fnord updates.

    The fnords speak! Listen to their whispers.
    """
    async def event_stream():
        last_count = await query_fnord_count()
        while True:
            await asyncio.sleep(2)
            current_count = await query_fnord_count()

            if current_count > last_count:
                new_count = current_count - last_count
                new_fnords = await get_all_fnords(limit=new_count, offset=0)

                for fnord in new_fnords:
                    template = templates.get_template("fnord_card.html")
                    html = template.render(fnord=fnord, request={})
                    # Send as single data line for simpler parsing
                    html_oneline = html.replace('\n', '').replace('\r', '')
                    yield f"event: new-fnord\ndata: {html_oneline}\n\n"

                last_count = current_count

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
