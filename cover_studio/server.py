"""Loopback HTTP server exposing the JSON API and static files."""

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import crop, store as store_mod

MAX_BODY = 16384
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/style.css": ("style.css", "text/css; charset=utf-8"),
    "/static/tokens.css": ("tokens.css", "text/css; charset=utf-8"),
}
CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self'; "
       "script-src 'self'; base-uri 'none'; form-action 'none'; "
       "frame-ancestors 'none'")
_ID_RE = re.compile(r"/api/v1/projects/([0-9]{1,18})")
_STATUS_CODES = {
    400: "bad_request", 403: "forbidden_host", 404: "not_found",
    405: "method_not_allowed", 408: "bad_request", 411: "bad_request",
    413: "payload_too_large", 414: "bad_request", 415: "unsupported_media_type",
    431: "bad_request", 501: "method_not_allowed",
}


class _Reject(Exception):
    def __init__(self, status, code, message, details=None, headers=None):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.details, self.headers = details, headers or {}


class Handler(BaseHTTPRequestHandler):
    """Request handler; every response is JSON except static files."""

    server_version = "CoverStudio"
    sys_version = ""
    timeout = 10

    def log_message(self, format, *args):
        pass

    # -- output helpers
    def _send(self, status, body, ctype, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Connection", "close")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True

    def _json(self, status, obj, extra=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8", extra)

    def _error(self, status, code, message, details=None, headers=None):
        err = {"code": code, "message": message}
        if details is not None:
            err["details"] = details
        self._json(status, {"error": err}, headers)

    def send_error(self, code, message=None, explain=None):
        try:
            phrase = HTTPStatus(code).phrase
        except ValueError:
            phrase = "Error"
        self._error(code, _STATUS_CODES.get(code, "bad_request"), phrase)

    # -- checks
    def _allowed_hosts(self):
        port = self.server.server_address[1]
        return {f"127.0.0.1:{port}", f"localhost:{port}"}

    def _check_host(self):
        if self.headers.get("Host") not in self._allowed_hosts():
            raise _Reject(403, "forbidden_host", "Host not allowed")

    def _check_origin(self):
        allowed = {"http://" + h for h in self._allowed_hosts()}
        if self.headers.get("Origin") not in allowed:
            raise _Reject(403, "forbidden_origin", "Origin not allowed")

    def _read_json(self):
        ctype = (self.headers.get("Content-Type") or "").split(";")[0]
        if ctype.strip().lower() != "application/json":
            raise _Reject(415, "unsupported_media_type",
                          "Content-Type must be application/json")
        if self.headers.get("Transfer-Encoding") is not None:
            raise _Reject(411, "bad_request", "Content-Length required")
        raw = self.headers.get("Content-Length")
        if raw is None:
            raise _Reject(411, "bad_request", "Content-Length required")
        if not raw.isascii() or not raw.isdigit():
            raise _Reject(400, "bad_request", "Invalid Content-Length")
        length = int(raw)
        if length > MAX_BODY:
            raise _Reject(413, "payload_too_large", "Body too large")
        data = self.rfile.read(length)
        if len(data) != length:
            raise _Reject(400, "bad_request", "Incomplete body")

        def bad_const(name):
            raise ValueError(name)

        try:
            return json.loads(data.decode("utf-8"), parse_constant=bad_const)
        except (ValueError, RecursionError):
            raise _Reject(400, "bad_request", "Invalid JSON",
                          {"fields": {"body": "invalid JSON"}})

    # -- dispatch
    def _handle(self):
        try:
            self._check_host()
            path = self.path.split("?", 1)[0].split("#", 1)[0]
            method = self.command
            if path in STATIC_FILES:
                self._route_static(path, method)
            elif path == "/api/v1/health":
                self._need(method, ("GET",))
                self._json(200, {"status": "ok", "app": "cover_studio",
                                 "schema_version": 1})
            elif path == "/api/v1/projects":
                self._need(method, ("GET", "POST"))
                if method == "GET":
                    self._json(200, {"projects": self.server.store.list()})
                else:
                    self._create()
            else:
                m = _ID_RE.fullmatch(path)
                if not m:
                    raise _Reject(404, "not_found", "Not found")
                self._need(method, ("GET", "PUT"))
                pid = int(m.group(1))
                if method == "GET":
                    self._json(200, self.server.store.get(pid))
                else:
                    self._update(pid)
        except _Reject as r:
            self._error(r.status, r.code, r.message, r.details, r.headers)
        except store_mod.NotFound:
            self._error(404, "not_found", "Project not found")
        except store_mod.VersionConflict as c:
            self._error(409, "version_conflict",
                        "Project was changed by another save",
                        {"current": c.current})
        except crop.ValidationError as v:
            self._error(400, "bad_request", "Invalid input",
                        {"fields": v.fields})
        except Exception:
            try:
                self._error(500, "internal_error", "Internal error")
            except Exception:
                pass

    def _need(self, method, allowed):
        if method not in allowed:
            raise _Reject(405, "method_not_allowed", "Method not allowed",
                          headers={"Allow": ", ".join(allowed)})

    def _route_static(self, path, method):
        self._need(method, ("GET",))
        name, ctype = STATIC_FILES[path]
        try:
            body = (STATIC_DIR / name).read_bytes()
        except OSError:
            raise _Reject(404, "not_found", "Not found")
        self._send(200, body, ctype)

    def _create(self):
        self._check_origin()
        payload = self._read_json()
        data = crop.validate_project_input(
            payload, require_all=False, require_version=False)
        project = self.server.store.create(data)
        self._json(201, project,
                   {"Location": f"/api/v1/projects/{project['id']}"})

    def _update(self, pid):
        self._check_origin()
        payload = self._read_json()
        data = crop.validate_project_input(
            payload, require_all=True, require_version=True)
        self._json(200, self.server.store.update(pid, data))

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = _handle
    do_OPTIONS = _handle


def create_server(data_dir, port):
    """Create (but do not start) a loopback server bound to 127.0.0.1."""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    store = store_mod.Store(data_dir / "cover_studio.sqlite3")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.store = store
    return server
