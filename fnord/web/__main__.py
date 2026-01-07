#!/usr/bin/env python3
"""
Run fnord web server.

Starts FastAPI with HTMX for a modern web interface.
Usage:
    python -m fnord.web
"""

import uvicorn

from fnord.config import get_config
from fnord.web.app import app

if __name__ == "__main__":
    config = get_config()
    port = config.get_web_port()
    
    print(f"🍎 Starting Fnord Tracker Web Server... 🍎")
    print(f"Open http://localhost:{port} in your browser")
    print(f"Port: {port} (set via FNORD_WEB_PORT env variable)")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        reload=True,
    )
