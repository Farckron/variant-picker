#!/usr/bin/env python3
"""Variant picker server.

  python3 gallery.py <root> [port] [--on-pick CMD]      (default port 8765)

Serves <root> as static files (with HTTP Range, so video seeks work) and adds:
  /_pick/               the picker page (gallery.html next to this script)
  /_pick/gallery.json   manifest: <root>/gallery.json if it exists, else a fresh
                        scan of <root>/variants/<flow>/<V>/ on every request
  /_pick/picks  GET     <root>/picks.json   POST  writes it (validated, atomic)

--on-pick CMD runs CMD in <root> each time the picks change (not on note edits),
e.g. "python3 build.py", so in-context previews follow the current picks.

Scan layout: variants/<NN-flow>/<V>/ with NOTES.md (line 1 title, lines 2-3
description), one preview file (see PREVIEWS) and an optional thumb.png for the
square. The NN- prefix sets the order and the number on the squares.
"""
import argparse, json, os, re, subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIEWS = ["preview.html", "index.html", "preview.png", "preview.jpg", "preview.webp",
            "preview.gif", "preview.svg", "preview.pdf", "preview.mp4", "preview.md", "preview.txt"]
THUMBS = ["thumb.png", "thumb.jpg", "thumb.webp"]  # small screenshot shown on the square


def scan(root):
    vdir = root / "variants"
    flows = sorted(p for p in vdir.iterdir() if p.is_dir()) if vdir.is_dir() else []
    out = []
    for i, f in enumerate(flows, 1):
        # number from the NN- prefix, not the scan position: flows land out of order
        # while agents run, and notes are keyed by card id
        m = re.match(r"(\d+)[-_]", f.name)
        n = int(m.group(1)) if m else i
        cards = []
        for v in sorted(p for p in f.iterdir() if p.is_dir()):
            prev = next((v / x for x in PREVIEWS if (v / x).is_file()), None)
            notes = (v / "NOTES.md").read_text(encoding="utf-8").strip().splitlines() if (v / "NOTES.md").is_file() else []
            thumb = next((v / x for x in THUMBS if (v / x).is_file()), None)
            cards.append({"id": f"{n}{v.name}", "v": v.name,
                          "thumb": "/" + thumb.relative_to(root).as_posix() if thumb else "",
                          "title": notes[0].lstrip("# ") if notes else v.name,
                          "desc": " ".join(notes[1:3])[:300],
                          "href": "/" + prev.relative_to(root).as_posix() if prev else ""})
        out.append({"n": n, "flow": re.sub(r"^\d+[-_]", "", f.name), "key": f.name, "cards": cards})
    return {"title": root.name, "flows": out}


class H(SimpleHTTPRequestHandler):
    # show text previews in the iframe instead of downloading them
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8"}

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _foreign(self):
        # DNS rebinding: a remote page re-pointed at 127.0.0.1 still sends its own Host
        if (self.headers.get("Host") or "").rsplit(":", 1)[0] in ("127.0.0.1", "localhost"):
            return False
        self.send_error(403, "forbidden")
        return True

    def do_HEAD(self):
        if not self._foreign():
            super().do_HEAD()

    def do_GET(self):
        if self._foreign():
            return
        p = self.path.split("?")[0]
        if p in ("/_pick", "/_pick/"):
            b = (HERE / "gallery.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            return self.wfile.write(b)
        if p == "/_pick/gallery.json":
            g = ROOT / "gallery.json"
            return self._json(json.loads(g.read_text(encoding="utf-8")) if g.is_file() else scan(ROOT))
        if p == "/_pick/picks":
            f = ROOT / "picks.json"
            return self._json(json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {"picks": {}, "notes": {}})
        return super().do_GET()

    def do_POST(self):
        if self._foreign():
            return
        if self.path != "/_pick/picks":
            return self._json({"error": "not found"}, 404)
        # block other web pages: JSON content type forces a CORS preflight we never
        # answer, and Origin must be this local server
        origin = self.headers.get("Origin")
        if ("json" not in (self.headers.get("Content-Type") or "")
                or (origin and origin.split("://")[-1].rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"))):
            return self._json({"error": "forbidden"}, 403)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 <= n <= 100_000:
                raise ValueError("bad length")
            d = json.loads(self.rfile.read(n))
            ok = lambda m: isinstance(m, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in m.items())
            if not (isinstance(d, dict) and set(d) <= {"picks", "notes"} and ok(d.get("picks", {})) and ok(d.get("notes", {}))):
                raise ValueError("expected {picks: {flow: V}, notes: {id: text}}")
        except ValueError as e:  # json.JSONDecodeError is a ValueError
            return self._json({"error": str(e)}, 400)
        dst = ROOT / "picks.json"
        try:
            old = json.loads(dst.read_text(encoding="utf-8")).get("picks")
        except (OSError, ValueError, AttributeError):
            old = None
        tmp = ROOT / ".picks.json.tmp"
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, dst)
        if ON_PICK and d.get("picks", {}) != old:
            # ponytail: runs inline, no queue; the build must write its files atomically
            subprocess.run(ON_PICK, shell=True, cwd=ROOT)
        self._json({"saved": str(dst)})

    def send_head(self):  # Range support for <video>
        rng, path = self.headers.get("Range"), self.translate_path(self.path)
        m = re.match(r"bytes=(\d*)-(\d*)$", rng or "")
        self._left = None
        if not m or not any(m.groups()) or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        a, b = m.groups()
        if a:
            start, end = int(a), min(int(b) if b else size - 1, size - 1)
        else:  # bytes=-N means the last N bytes
            start, end = max(size - int(b), 0), size - 1
        if start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        f = open(path, "rb"); f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._left = end - start + 1
        return f

    def copyfile(self, src, dst):
        if getattr(self, "_left", None) is None:
            return super().copyfile(src, dst)
        while self._left > 0 and (chunk := src.read(min(1 << 18, self._left))):
            try: dst.write(chunk)
            except (BrokenPipeError, ConnectionResetError): break
            self._left -= len(chunk)

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")  # agents keep rewriting files
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Variant picker server")
    ap.add_argument("root")
    ap.add_argument("port", nargs="?", type=int, default=8765)
    ap.add_argument("--on-pick", help='shell command run in <root> when the picks change, e.g. "python3 build.py"')
    args = ap.parse_args()
    ROOT, PORT, ON_PICK = Path(args.root).resolve(), args.port, args.on_pick
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:  # port taken: let the OS pick one
        srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    print(f"picker: http://127.0.0.1:{srv.server_port}/_pick/   root: {ROOT}", flush=True)
    srv.serve_forever()  # ponytail: localhost only, no auth
