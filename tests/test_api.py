"""Loopback HTTP tests using a disposable database (CHK-B01, B02, B05 to B08)."""

import http.client
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path

from cover_studio import server as server_mod

STATIC = Path(server_mod.__file__).resolve().parent / "static"


class Running:
    """A real server on an ephemeral loopback port."""

    def __init__(self, data_dir):
        self.httpd = server_mod.create_server(data_dir, 0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(5)

    def call(self, method, path, body=None, headers=None, raw=None, host=None, origin=True):
        h = {}
        if host is not None:
            h["Host"] = host
        if origin is True and method in ("POST", "PUT"):
            h["Origin"] = f"http://127.0.0.1:{self.port}"
        elif isinstance(origin, str):
            h["Origin"] = origin
        data = raw
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.putrequest(method, path, skip_host="Host" in h)
            for k, v in h.items():
                conn.putheader(k, v)
            if data is not None and "Content-Length" not in h:
                conn.putheader("Content-Length", str(len(data)))
            conn.endheaders(data)
            resp = conn.getresponse()
            payload = resp.read()
            return resp.status, resp, payload
        finally:
            conn.close()

    def json(self, *args, **kw):
        status, resp, payload = self.call(*args, **kw)
        return status, json.loads(payload.decode("utf-8")), resp


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = Running(self.tmp.name)
        self.addCleanup(self.app.stop)

    def create(self, **over):
        body = {"title": "Sample Reel", "overlay_text": "Fresh start"}
        body.update(over)
        status, obj, _ = self.app.json("POST", "/api/v1/projects", body)
        self.assertEqual(status, 201, obj)
        return obj

    def update_body(self, p, **over):
        body = {k: p[k] for k in ("title", "overlay_text", "preset",
                                  "focal_x", "focal_y", "version")}
        body.update(over)
        return body


class HealthAndCrud(ApiTestCase):
    def test_health(self):  # CHK-B01
        status, obj, resp = self.app.json("GET", "/api/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(obj, {"status": "ok", "app": "cover_studio", "schema_version": 1})
        self.assertEqual(resp.getheader("X-Content-Type-Options"), "nosniff")
        self.assertIn("default-src 'self'", resp.getheader("Content-Security-Policy"))

    def test_create_list_get(self):  # CHK-B02
        a = self.create(title="First")
        b = self.create(title="Second", focal_x=0.25)
        self.assertEqual(a["version"], 1)
        self.assertEqual(a["crop"], {"x": 375, "y": 0, "width": 450, "height": 800})
        self.assertEqual(b["crop"]["x"], 75)
        status, obj, _ = self.app.json("GET", "/api/v1/projects")
        self.assertEqual(status, 200)
        self.assertEqual([p["id"] for p in obj["projects"]], [b["id"], a["id"]])
        status, got, _ = self.app.json("GET", f"/api/v1/projects/{a['id']}")
        self.assertEqual((status, got), (200, a))

    def test_create_sets_location(self):
        status, _, resp = self.app.json("POST", "/api/v1/projects", {"title": "x"})
        self.assertEqual(status, 201)
        self.assertRegex(resp.getheader("Location"), r"^/api/v1/projects/\d+$")

    def test_update_increments_version(self):
        p = self.create()
        status, q, _ = self.app.json(
            "PUT", f"/api/v1/projects/{p['id']}",
            self.update_body(p, title="Renamed", focal_x=1.0))
        self.assertEqual(status, 200, q)
        self.assertEqual((q["version"], q["title"], q["crop"]["x"]), (2, "Renamed", 750))

    def test_not_found_and_methods(self):
        self.assertEqual(self.app.json("GET", "/api/v1/projects/999")[0], 404)
        self.assertEqual(self.app.json("GET", "/api/v1/nope")[0], 404)
        status, obj, resp = self.app.json("DELETE", "/api/v1/projects/1")
        self.assertEqual(status, 405)
        self.assertEqual(obj["error"]["code"], "method_not_allowed")
        self.assertIn("GET", resp.getheader("Allow"))
        body = self.update_body(self.create(), version=1)
        self.assertEqual(self.app.json("PUT", "/api/v1/projects/999", body)[0], 404)

    def test_validation_errors(self):  # CHK-B04
        cases = [
            {"title": ""}, {"title": "t" * 81}, {"title": "ok", "overlay_text": "o" * 121},
            {"title": "ok", "focal_x": 2}, {"title": "ok", "focal_x": "0.5"},
            {"title": "ok", "extra": 1}, {"overlay_text": "no title"},
        ]
        for body in cases:
            with self.subTest(body=body):
                status, obj, _ = self.app.json("POST", "/api/v1/projects", body)
                self.assertEqual(status, 400)
                self.assertEqual(obj["error"]["code"], "bad_request")
                self.assertTrue(obj["error"]["details"]["fields"])
        status, obj, _ = self.app.json("POST", "/api/v1/projects", raw=b"{bad",
                                       headers={"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        status, obj, _ = self.app.json(
            "POST", "/api/v1/projects", raw=b'{"title":"x","focal_x":NaN}',
            headers={"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertEqual(self.app.json("GET", "/api/v1/projects")[1]["projects"], [])

    def test_boundary_lengths_accepted(self):
        p = self.create(title="t" * 80, overlay_text="o" * 120)
        self.assertEqual(len(p["title"]), 80)

    def test_markup_text_roundtrips(self):  # CHK-B08 (API half)
        text = "Hello <b>world</b> & friends é中"
        p = self.create(title="<i>t</i>", overlay_text=text)
        _, got, _ = self.app.json("GET", f"/api/v1/projects/{p['id']}")
        self.assertEqual((got["title"], got["overlay_text"]), ("<i>t</i>", text))


class Conflicts(ApiTestCase):
    def test_stale_version_conflict(self):  # CHK-B06
        p = self.create()
        path = f"/api/v1/projects/{p['id']}"
        ok, q, _ = self.app.json("PUT", path, self.update_body(p, title="Winner"))
        self.assertEqual(ok, 200)
        status, obj, _ = self.app.json("PUT", path, self.update_body(p, title="Loser"))
        self.assertEqual(status, 409)
        self.assertEqual(obj["error"]["code"], "version_conflict")
        self.assertEqual(obj["error"]["details"]["current"], q)
        _, still, _ = self.app.json("GET", path)
        self.assertEqual(still, q)

    def test_concurrent_updates_single_winner(self):
        p = self.create()
        path = f"/api/v1/projects/{p['id']}"
        results = []

        def go(n):
            results.append(self.app.json("PUT", path, self.update_body(p, title=f"T{n}"))[0])

        threads = [threading.Thread(target=go, args=(n,)) for n in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual(sorted(results), [200] + [409] * 7)
        self.assertEqual(self.app.json("GET", path)[1]["version"], 2)


class Security(ApiTestCase):
    def test_bad_host(self):  # CHK-B07
        for path in ("/api/v1/health", "/"):
            for host in ("evil.example", "127.0.0.1", f"127.0.0.1:{self.app.port + 1}"):
                with self.subTest(path=path, host=host):
                    status, obj, _ = self.app.json("GET", path, host=host)
                    self.assertEqual(status, 403)
                    self.assertEqual(obj["error"]["code"], "forbidden_host")

    def test_localhost_host_allowed(self):
        status, _, _ = self.app.json("GET", "/api/v1/health",
                                     host=f"localhost:{self.app.port}")
        self.assertEqual(status, 200)

    def test_write_origin_required(self):
        for origin in (False, "http://evil.example", "null",
                       f"http://127.0.0.1:{self.app.port + 1}"):
            with self.subTest(origin=origin):
                status, obj, _ = self.app.json(
                    "POST", "/api/v1/projects", {"title": "x"}, origin=origin)
                self.assertEqual(status, 403)
                self.assertEqual(obj["error"]["code"], "forbidden_origin")
        p = self.create()
        status, _, _ = self.app.json(
            "PUT", f"/api/v1/projects/{p['id']}", self.update_body(p),
            origin="http://evil.example")
        self.assertEqual(status, 403)
        self.assertEqual(len(self.app.json("GET", "/api/v1/projects")[1]["projects"]), 1)

    def test_body_cap_and_media_type(self):
        # Header only: the server rejects on Content-Length without reading.
        status, obj, _ = self.app.json(
            "POST", "/api/v1/projects", raw=b"",
            headers={"Content-Type": "application/json", "Content-Length": "16385"})
        self.assertEqual((status, obj["error"]["code"]), (413, "payload_too_large"))
        status, obj, _ = self.app.json("POST", "/api/v1/projects", raw=b'{"title":"x"}',
                                       headers={"Content-Type": "text/plain"})
        self.assertEqual((status, obj["error"]["code"]), (415, "unsupported_media_type"))

    def test_bad_content_length(self):
        status, _, _ = self.app.json(
            "POST", "/api/v1/projects", raw=b"", headers={
                "Content-Type": "application/json", "Content-Length": "abc"})
        self.assertEqual(status, 400)


class Persistence(unittest.TestCase):
    def test_reopen_after_restart(self):  # CHK-B05
        with tempfile.TemporaryDirectory() as tmp:
            first = Running(tmp)
            try:
                _, p, _ = first.json("POST", "/api/v1/projects", {
                    "title": "Persist", "overlay_text": "Still here", "focal_x": 0.25})
                _, q, _ = first.json("PUT", f"/api/v1/projects/{p['id']}", {
                    "title": "Persist 2", "overlay_text": "Still here", "preset": "reel_9_16",
                    "focal_x": 0.75, "focal_y": 0.5, "version": 1})
            finally:
                first.stop()
            second = Running(tmp)
            try:
                status, got, _ = second.json("GET", f"/api/v1/projects/{p['id']}")
                self.assertEqual((status, got), (200, q))
                self.assertEqual(got["crop"]["x"], 675)
                _, lst, _ = second.json("GET", "/api/v1/projects")
                self.assertEqual(lst["projects"], [q])
            finally:
                second.stop()


class StaticAssets(ApiTestCase):
    def test_static_served_with_types(self):
        for path, ctype in (("/", "text/html"), ("/static/app.js", "text/javascript"),
                            ("/static/style.css", "text/css")):
            with self.subTest(path=path):
                status, resp, body = self.app.call("GET", path)
                self.assertEqual(status, 200)
                self.assertTrue(resp.getheader("Content-Type").startswith(ctype))
                self.assertTrue(body)

    def test_unlisted_paths_404(self):
        for path in ("/static/../server.py", "/static/index.html", "/static/", "/x"):
            with self.subTest(path=path):
                self.assertEqual(self.app.call("GET", path)[0], 404)

    def test_no_unsafe_dom_or_inline_code(self):  # CHK-B08 (static half)
        js = (STATIC / "app.js").read_text(encoding="utf-8")
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        css = (STATIC / "style.css").read_text(encoding="utf-8")
        for pattern in (r"\.innerHTML\s*[+]?=", r"insertAdjacentHTML", r"document\.write",
                        r"\beval\(", r"new Function"):
            self.assertIsNone(re.search(pattern, js), pattern)
        self.assertIsNone(re.search(r"<script(?![^>]*\ssrc=)", html))
        self.assertIsNone(re.search(r"\son\w+\s*=", html))
        self.assertIsNone(re.search(r"<style|style\s*=", html))
        for text in (js, html, css):
            self.assertIsNone(re.search(r"https?://(?!127\.0\.0\.1|localhost)", text))

    def test_testid_hooks_present(self):
        text = (STATIC / "index.html").read_text(encoding="utf-8")
        for hook in ("title", "overlay", "focal-x", "focal-y", "save", "status",
                     "error", "preview", "overview", "project-list", "crop-readout"):
            self.assertIn(f'data-testid="{hook}"', text)


if __name__ == "__main__":
    unittest.main()
