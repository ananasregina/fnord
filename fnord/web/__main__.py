#!/usr/bin/env python3
"""
Run the fnord web server.

Starts FastAPI with HTMX for a modern web interface.
Usage:
    python -m fnord.web.app
"""

import uvicorn

if __name__ == "__main__":
    print("🍎 Starting Fnord Tracker Web Server... 🍎")
    print("Open http://localhost:8000 in your browser")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "fnord.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
