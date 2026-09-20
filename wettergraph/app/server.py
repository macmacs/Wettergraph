"""Placeholder service for the Wettergraph app.

This ticket installs nothing but the skeleton: it proves the app starts, that
Supervisor's options reach us at /data/options.json, and that something is
actually served on the configured port. The page reads its values from the
options file on every request, so editing an option in the UI changes the page
with no rebuild.
"""

from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

OPTIONS_PATH = Path(os.environ.get("WG_OPTIONS", "/data/options.json"))
DATA_DIR = Path("/data")
STARTED_AT = time.time()

# Placeholder asset, replaced by the real met.no-driven render later.
SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="782" height="391" viewBox="0 0 782 391">
  <rect width="782" height="391" fill="{bg}"/>
  <text x="32" y="120" font-family="DejaVu Sans, sans-serif" font-size="34" fill="#1f2d3d">{title}</text>
  <text x="32" y="170" font-family="DejaVu Sans, sans-serif" font-size="22" fill="#3a4b5c">{place}</text>
  <text x="32" y="212" font-family="DejaVu Sans, sans-serif" font-size="18" fill="#6b7b8c">up {uptime}s - update_interval {interval} min - note: {note}</text>
  <text x="32" y="256" font-family="DejaVu Sans, sans-serif" font-size="18" fill="#6b7b8c">{layer}</text>
  <text x="32" y="300" font-family="DejaVu Sans, sans-serif" font-size="16" fill="#9aa7b4">placeholder - no forecast data yet</text>
</svg>
"""


def options() -> dict:
    """Read /data/options.json fresh, so UI edits show up without a rebuild."""
    try:
        with OPTIONS_PATH.open() as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        return {"_error": f"invalid JSON: {exc}"}


def page_html(opts: dict) -> str:
    rows = "".join(
        f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in sorted(opts.items())
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>Wettergraph</title>
<style>
  body {{ font: 16px/1.5 DejaVu Sans, sans-serif; background: #1c1c1e; color: #f2f2f7; margin: 2rem; }}
  h1 {{ font-size: 1.4rem; }}
  table {{ border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: .3rem .8rem; border-bottom: 1px solid #3a3a3c; }}
  th {{ color: #9aa7b4; font-weight: normal; }}
  img {{ margin-top: 1.5rem; border-radius: 8px; }}
  code {{ color: #8fd6ff; }}
</style>
<h1>Wettergraph</h1>
<p>Skeleton is up. Rendering is not implemented yet.</p>
<p><code>{OPTIONS_PATH}</code> - read fresh on every request.</p>
<table>{rows}</table>
<img src="/image/graph" alt="placeholder graph" width="782">
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "wettergraph/0.1"

    def _send(self, code: int, body: bytes, ctype: str, cache: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        opts = options()
        path = self.path.split("?", 1)[0]

        if path in ("/", "/index.html"):
            self._send(200, page_html(opts).encode(), "text/html; charset=utf-8", "no-store")
            return

        if path == "/health":
            self._send(200, b"ok\n", "text/plain; charset=utf-8", "no-store")
            return

        if path in ("/image/graph", "/image/graph.svg"):
            svg = SVG.format(
                bg="#10131a",
                title="Wettergraph",
                place=f"place {opts.get('place_id', '?')} {opts.get('latitude', '?')},{opts.get('longitude', '?')}",
                uptime=int(time.time() - STARTED_AT),
                interval=opts.get("update_interval", "?"),
                note=opts.get("page_note", "-"),
                layer=f"python {os.sys.version.split()[0]} / /data writable: {os.access(DATA_DIR, os.W_OK)}",
            )
            self._send(200, svg.encode(), "image/svg+xml; charset=utf-8", "no-store")
            return

        self._send(404, b"not found\n", "text/plain; charset=utf-8", "no-store")

    def log_message(self, fmt: str, *args) -> None:
        print(f"wettergraph: {self.address_string()} {fmt % args}", flush=True)


def main() -> None:
    port = int(os.environ.get("WG_PORT", "8099"))
    print(
        f"wettergraph: starting on :{port}; options={OPTIONS_PATH} "
        f"present={OPTIONS_PATH.exists()} build={os.environ.get('BUILD_VERSION', 'dev')}",
        flush=True,
    )
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


def run_checks(bind_port: int = 0) -> list[tuple[str, bool, str]]:
    """Exercise every route against a throwaway in-process server.

    bind_port 0 asks the OS for a free port, which is what the startup run
    wants: it must not collide with the port the real server is about to take.
    """
    import threading
    import urllib.error
    import urllib.request

    httpd = ThreadingHTTPServer(("127.0.0.1", bind_port), Handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    def fetch(path: str):
        try:
            with urllib.request.urlopen(base + path, timeout=10) as resp:
                return resp.status, resp.headers.get("Content-Type", ""), resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type", ""), exc.read().decode()
        except OSError as exc:
            return 0, "", f"unreachable: {exc}"

    opts = options()
    checks: list[tuple[str, bool, str]] = []

    status, _, body = fetch("/health")
    checks.append(("/health returns 200 ok", status == 200 and body.strip() == "ok", f"{status} {body.strip()[:40]!r}"))

    status, ctype, body = fetch("/")
    rows = body.count("<tr>")
    checks.append(("/ serves an HTML page", status == 200 and "text/html" in ctype, f"{status} {ctype}"))
    checks.append(
        (
            "page lists every option",
            bool(opts) and rows == len(opts),
            f"{rows} rows for {len(opts)} options" + (" (options.json missing or unreadable)" if not opts else ""),
        )
    )
    if opts and "_error" not in opts:
        key, value = sorted(opts.items())[0]
        checks.append(("option values reach the page", str(value) in body, f"{key}={value!r}"))

    status, ctype, body = fetch("/image/graph")
    checks.append(
        (
            "/image/graph serves an SVG",
            status == 200 and "svg" in ctype and body.startswith("<svg") and 'width="782"' in body,
            f"{status} {ctype} {len(body)}B",
        )
    )

    status, _, _ = fetch("/definitely-not-a-route")
    checks.append(("unknown paths 404", status == 404, str(status)))
    checks.append(("options file is readable", OPTIONS_PATH.exists(), str(OPTIONS_PATH)))

    httpd.shutdown()
    return checks


def report(checks: list[tuple[str, bool, str]]) -> int:
    failed = 0
    for name, ok, detail in checks:
        print(f"wettergraph: {'PASS' if ok else 'FAIL'}  {name}  ({detail})", flush=True)
        failed += 0 if ok else 1
    print(f"wettergraph: startup check {len(checks) - failed}/{len(checks)} passed", flush=True)
    return failed


def main() -> None:
    port = int(os.environ.get("WG_PORT", "8099"))
    print(
        f"wettergraph: starting on :{port}; options={OPTIONS_PATH} "
        f"present={OPTIONS_PATH.exists()} build={os.environ.get('BUILD_VERSION', 'dev')}",
        flush=True,
    )
    # Report into the app log, where the operator can actually read it: HAOS
    # gives no shell inside an app container.
    report(run_checks())
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    if "--self-test" in os.sys.argv:
        os.sys.exit(1 if report(run_checks(int(os.environ.get("WG_PORT", "8099")))) else 0)
    main()
