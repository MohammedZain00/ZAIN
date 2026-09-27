"""Local app: a tiny web server on 127.0.0.1 + an Arabic UI in the browser."""
from __future__ import annotations

import base64
import json
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import imaging, ipp, printing

PHOTOS: dict[str, imaging.Photo] = {}
UI = Path(__file__).with_name("ui.html")


def _data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code=200, body=b"", ctype="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _selected(self, body):
        missing = [i for i in body.get("ids", []) if i not in PHOTOS]
        if missing:
            raise ValueError("some photos are no longer loaded; add them again")
        return [PHOTOS[i] for i in body.get("ids", [])]

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                self._send(200, UI.read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/api/printers":
                self._send(200, printing.discover())
            elif u.path == "/api/caps":
                self._send(200, printing.capabilities(q["uri"]))
            elif u.path == "/api/jobs":
                self._send(200, ipp.IPPPrinter(q["uri"]).jobs())
            elif u.path == "/api/papers":
                self._send(200, [{"key": p.key, "label": p.label} for p in imaging.PAPERS.values()])
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def do_POST(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/upload":
                data = self.rfile.read(int(self.headers["Content-Length"]))
                photo = imaging.load(data, unquote(q.get("name", "photo")))
                pid = uuid.uuid4().hex[:10]
                PHOTOS[pid] = photo
                thumb = imaging.place_photo(photo, 240, 240, imaging.PrintSettings(fit="fit", sharpen=0))
                self._send(200, {"id": pid, "info": photo.describe(),
                                 "thumb": _data_url(imaging.preview_jpeg(thumb, 240))})
            elif u.path == "/api/remove":
                PHOTOS.pop(self._json().get("id"), None)
                self._send(200, {"ok": True})
            elif u.path == "/api/preview":
                body = self._json()
                s = imaging.PrintSettings.from_dict(body.get("settings", {}))
                caps = body.get("caps")
                margins, warnings = printing.plan_margins(s, caps, imaging.paper_from(s.paper))
                s.dpi = 110
                pages, _, paper = imaging.render_pages(self._selected(body)[:40], s, margins)
                self._send(200, {"pages": [_data_url(imaging.preview_jpeg(p)) for p in pages[:12]],
                                 "total": len(pages), "paper": [paper.w_mm, paper.h_mm],
                                 "warnings": warnings})
            elif u.path == "/api/print":
                body = self._json()
                s = imaging.PrintSettings.from_dict(body.get("settings", {}))
                res = printing.print_photos(self._selected(body), s, body["printer"])
                self._send(200, res)
            elif u.path == "/api/save":
                body = self._json()
                s = imaging.PrintSettings.from_dict(body.get("settings", {}))
                pages, dpi, paper = imaging.render_pages(self._selected(body), s)
                self._send(200, imaging.encode_pdf(pages, dpi, paper), "application/pdf",
                           {"Content-Disposition": 'attachment; filename="photos-print-ready.pdf"'})
            elif u.path == "/api/cancel":
                body = self._json()
                ipp.IPPPrinter(body["uri"]).cancel(int(body["job_id"]))
                self._send(200, {"ok": True})
            elif u.path == "/api/identify":
                ipp.IPPPrinter(self._json()["uri"]).identify()
                self._send(200, {"ok": True})
            else:
                self._send(404, {"error": "not found"})
        except Exception as exc:
            self._send(500, {"error": str(exc)})


def serve(port: int = 8631, open_browser: bool = True):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Photo Print is running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
