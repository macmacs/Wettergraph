"""Ticket 05's sample renders: the five cases the ticket asks to see.

    uv run --with resvg-py python .scratch/wettergraph-redesign/assets/make-samples.py

Everything is pinned - the cache, the render hour, the font - so a rerun writes
byte-identical files. The forecast is the real met.no payload the previous map
captured (`render-sample-cache.json`, 88 entries: hourly, then 6-hourly), and
the render hour sits 13 h after its fetch, so the window's tail runs past the
hourly entries and §4.8's interpolation is exercised on every sample but the
empty one.
"""
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ["TZ"] = "UTC"
time.tzset()
ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "wettergraph" / "app"))
import render  # noqa: E402

HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".scratch" / "wettergraph-ha-widget" / "assets" / "render-sample-cache.json"
FONT = next(str(p) for p in (render.FONT_PATH, Path("/tmp/DejaVuSans.ttf")) if Path(p).is_file())
ICONS = ROOT / "wettergraph" / "app" / "icons"

import json  # noqa: E402

document = json.loads(CACHE.read_text())
samples = document["samples"]
fetched_at = document["fetched_at"]
NOW = int(datetime(2026, 9, 23, 8, 0, tzinfo=timezone.utc).timestamp())  # Mi 23.09., 08:00

# §7.5 needs a rate over 10 mm/h; the real payload never has one. Same series,
# a wet afternoon written over it, peaking at 13.4 mm/h.
wet = [dict(sample) for sample in samples]
for offset, mm in ((28, 0.4), (29, 1.8), (30, 4.2), (31, 8.6), (32, 13.4), (33, 5.1), (34, 1.3), (35, 0.2)):
    wet[offset]["precipitation"] = mm

CASES = (
    ("light", samples, dict(theme="light")),
    ("dark", samples, dict(theme="dark")),
    ("stale", samples, dict(theme="light", stale=True, age_seconds=7 * 3600)),
    ("rain-overmax", wet, dict(theme="light")),
    ("empty", [], dict(theme="light", last_error="met.no unreachable: timed out after 10 s")),
)

for name, series, options in CASES:
    arguments = dict(fetched_at=fetched_at, now=NOW, width=794, icons_dir=ICONS, **options)
    svg = render.build_svg(series, **arguments)
    png = render.render_png(series, font_path=FONT, **arguments)
    (HERE / f"render-sample-{name}.svg").write_text(svg)
    (HERE / f"render-sample-{name}.png").write_bytes(png)
    print(f"render-sample-{name}: {len(svg)} B svg, {len(png)} B png")
