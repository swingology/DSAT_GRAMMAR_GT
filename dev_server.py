#!/usr/bin/env python3
"""Simple frontend server with API proxy."""

import http.server
import os
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent / "APP" / "STUDENT_APP_REDUX" / "dist"
PORT = 5173


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Handle API proxying - but we'll let it 404 for now
        if path.startswith("/api/"):
            return path
        # For everything else, serve from dist
        path = super().translate_path(path)
        # For SPA routing, serve index.html for unknown routes
        relpath = os.path.relpath(path, FRONTEND_DIR)
        if not os.path.exists(path) or (os.path.isdir(path) and not os.path.exists(os.path.join(path, "index.html"))):
            path = os.path.join(FRONTEND_DIR, "index.html")
        return path


if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    print(f"Frontend: http://localhost:{PORT}")
    print(f"Serving:  {FRONTEND_DIR}\n")

    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
