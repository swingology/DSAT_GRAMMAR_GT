#!/usr/bin/env python3
"""Simple frontend server with API proxy."""

import http.server
import os
import urllib.error
import urllib.request
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent / "APP" / "STUDENT_APP_REDUX" / "dist"
PORT = 5173
BACKEND_URL = os.environ.get("BACKEND_PROXY_URL", "http://127.0.0.1:8000")


class Handler(http.server.SimpleHTTPRequestHandler):
    def _proxy_api(self):
        target = f"{BACKEND_URL}{self.path}"
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length"}
        }
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() not in {"connection", "transfer-encoding"}:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as exc:
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() not in {"connection", "transfer-encoding"}:
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(exc.read())
        except OSError as exc:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                f'{{"detail":"Backend unavailable at {BACKEND_URL}: {exc}"}}'.encode()
            )

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy_api()
            return
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy_api()
            return
        super().do_POST()

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            self._proxy_api()
            return
        super().do_OPTIONS()

    def translate_path(self, path):
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
    print(f"Proxying:  /api -> {BACKEND_URL}\n")

    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
