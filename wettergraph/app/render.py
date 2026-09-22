#!/usr/bin/env python3
"""Render the Wettergraph image (ticket 05).

One render is one SVG built in the spec's design units (W0 = 782 x 391), scaled
by k = W / 782 as each number is written, then rasterised by ``resvg-py``. No
browser, no headless Chrome. The font is loaded by file path, never by font
discovery, because resvg draws every text node as nothing when no font answers
and reports no error (``assets/graph-spec.md`` §3.4).

Input is the normalised series from :mod:`metno` - ``ForecastCache.view()``:
``samples``, ``fetched_at``, ``stale``, ``age_seconds``, ``last_error``. Output
matches ``assets/graph-spec.md`` clause for clause; the clause numbers are cited
at each decision below.

``show_age=True`` (ticket 06) draws the §8.2 age chip even when the data is
fresh, with minutes instead of hours under one hour. It is a debug switch -
§9.4 keeps the clock off the image otherwise - so a dashboard can be watched
proving it refreshes on its own.

Local check (needs the font file; this dev box has no fonts in the usual path)::

    uv run --with resvg-py python wettergraph/app/render.py \
        --cache /tmp/wg/forecast-cache.json --now <epoch> --out /tmp/wg/sample.png
"""

from __future__ import annotations

import argparse
import functools
import html
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import resvg_py

DESIGN_WIDTH = 782.0  # §1.1 design width; every number in the spec is stated here
DESIGN_HEIGHT = 391.0
DEFAULT_WIDTH = 782
MIN_WIDTH = 480  # §1.2
MAX_WIDTH = 1564

PADDING = 8.0  # §3.1
GUTTER = 36.0  # §3.2
CONTENT_LEFT = PADDING + GUTTER  # 44
CONTENT_RIGHT = DESIGN_WIDTH - PADDING  # 774
CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT  # 730

TEMP_TOP = 8.0  # §3.3
TEMP_BOTTOM = 283.0
TEMP_HEIGHT = TEMP_BOTTOM - TEMP_TOP  # 275
PRECIP_TOP = 291.0
PRECIP_BOTTOM = 383.0
PRECIP_HEIGHT = PRECIP_BOTTOM - PRECIP_TOP  # 92
PRECIP_MID = (PRECIP_TOP + PRECIP_BOTTOM) / 2.0
PRECIP_LABEL_X = 48.0  # §7.4
PRECIP_LABEL_Y = 299.0

WINDOW_HOURS = 48  # §4.1
WINDOW_POINTS = WINDOW_HOURS + 1  # 49 hourly samples
TIME_GRID_HOURS = 6  # §4.3
ICON_EVERY_HOURS = 3  # §6.1
ICON_BOX = 28.0  # §6.2
ICON_CLEARANCE = 3.0  # §6.3
PRECIP_STEPS = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0)  # §7.3
AXIS_FONT = 11.0  # §3.4
WEEKDAY_FONT = 12.0
AXIS_LABEL_X = 38.0  # §3.5, right-aligned
WEEKDAY_BASELINE = 280.0  # §4.4
TEMP_STEP = 5.0  # §5.1
STALE_MAX_HOURS = 48  # §8.2
CHIP_X = 704.0
CHIP_Y = 8.0
CHIP_WIDTH = 70.0
CHIP_HEIGHT = 18.0
CHIP_RADIUS = 3.0
DOT_X = 712.0
DOT_Y = 17.0
DOT_RADIUS = 3.0
CHIP_TEXT_X = 720.0
CHIP_TEXT_Y = 21.0

WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")  # §4.5
SEGMENT_SAMPLES = 32  # spline samples per hour, used to find an icon's highest curve point

# §2.3, light and dark. Same geometry, only the palette changes (§2.1).
PALETTES = {
    "light": {
        "background": "#ffffff",
        "grid": "#dfe3e8",
        "zero": "#b9c0c8",
        "baseline": "#c8cfd7",
        "midnight": "#aab2bb",
        "text": "#4a5158",
        "curve": "#d81e05",
        "precip": "#4a7fd4",
        "stale": "#b45309",
    },
    "dark": {
        "background": "#171a1f",
        "grid": "#333a42",
        "zero": "#5b6570",
        "baseline": "#454d57",
        "midnight": "#5b6570",
        "text": "#c3c9d1",
        "curve": "#ff6a4d",
        "precip": "#6fa8ff",
        "stale": "#fbbf24",
    },
}

ICONS_DIR = Path(os.environ.get("WG_ICONS", Path(__file__).resolve().parent / "icons"))
# §3.4: the container path. WG_FONT exists so a box without fonts can still
# render a check (this development box has none at the container's path).
FONT_PATH = Path(os.environ.get("WG_FONT", "/usr/share/fonts/dejavu/DejaVuSans.ttf"))

_font_warned = False


# --------------------------------------------------------------- small maths


def clamp_width(width) -> int:
    """§1.2: clamp 480..1564, never refuse. Non-numeric falls back to 782."""
    try:
        value = int(round(float(width)))
    except (TypeError, ValueError):
        value = DEFAULT_WIDTH
    return max(MIN_WIDTH, min(MAX_WIDTH, value))


def _px(value: float, k: float) -> float:
    """Design units -> output pixels: multiply by k, round to 0.1 px."""
    return round(float(value) * k, 1)


def _n(value: float) -> str:
    """A number as SVG text, deterministic and without trailing zeros."""
    text = f"{float(value):.4f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def _p(value: float, k: float) -> str:
    """A path coordinate: one decimal, like the reference SVG."""
    return f"{_px(value, k):.1f}"


def _epoch(iso) -> int | None:
    if not iso:
        return None
    try:
        moment = datetime.fromisoformat(str(iso))
    except (TypeError, ValueError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return int(moment.timestamp())


def window_slots(samples, fetched_at=None, now=None) -> tuple[int, list[tuple[int, dict | None]]]:
    """The 49 hourly slots of §4.1, keyed by epoch, with the window start.

    The window starts at the hour of the fetch. If met.no's series begins later
    than that hour (fetched just before an hour boundary), the window starts at
    the first sample instead, so the left edge is never a hole.
    """
    if fetched_at is None:
        fetched_at = now if now is not None else time.time()
    start = int(float(fetched_at) // 3600) * 3600
    by_time: dict[int, dict] = {}
    first: int | None = None
    for sample in samples or []:
        moment = _epoch((sample or {}).get("time"))
        if moment is None:
            continue
        by_time[moment] = sample
        if first is None or moment < first:
            first = moment
    if first is not None and first > start:
        start = first
    return start, [(start + i * 3600, by_time.get(start + i * 3600)) for i in range(WINDOW_POINTS)]


# ------------------------------------------------------------------- spline


def _bezier_segments(points: list[tuple[float, float]]):
    """Catmull-Rom through the points, tension 0.5, as cubic Béziers (§5.2).

    Uniform form: C1 = P_i + (P_i+1 - P_i-1)/6, C2 = P_i+1 - (P_i+2 - P_i)/6.
    The ends duplicate their neighbour, so the curve starts and stops at the
    window edges.
    """
    segments = []
    count = len(points)
    for i in range(count - 1):
        p0, p1 = points[i], points[i + 1]
        before = points[i - 1] if i > 0 else p0
        after = points[i + 2] if i + 2 < count else p1
        c1 = (p0[0] + (p1[0] - before[0]) / 6.0, p0[1] + (p1[1] - before[1]) / 6.0)
        c2 = (p1[0] - (after[0] - p0[0]) / 6.0, p1[1] - (after[1] - p0[1]) / 6.0)
        segments.append((p0, c1, c2, p1))
    return segments


def _bezier_at(segment, t: float) -> tuple[float, float]:
    p0, c1, c2, p1 = segment
    mt = 1.0 - t
    a, b, c, d = mt * mt * mt, 3 * mt * mt * t, 3 * mt * t * t, t * t * t
    return (
        a * p0[0] + b * c1[0] + c * c2[0] + d * p1[0],
        a * p0[1] + b * c1[1] + c * c2[1] + d * p1[1],
    )


def _runs(points: list[tuple[int, float, float]]) -> list[list[tuple[int, float, float]]]:
    """Split the hourly points into runs of consecutive hours, so a gap in the
    series breaks the curve instead of joining across it."""
    runs: list[list[tuple[int, float, float]]] = []
    run: list[tuple[int, float, float]] = []
    previous = None
    for item in points:
        if previous is not None and item[0] == previous + 1:
            run.append(item)
        else:
            if run:
                runs.append(run)
            run = [item]
        previous = item[0]
    if run:
        runs.append(run)
    return runs


# -------------------------------------------------------------------- icons


@functools.lru_cache(maxsize=8)
def _icon_index(icons_dir: str) -> dict[str, str]:
    """``symbol_code`` -> icon file name, from ticket 03's ``index.json``."""
    try:
        document = json.loads((Path(icons_dir) / "index.json").read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(code): str(entry["file"])
        for code, entry in (document.get("icons") or {}).items()
        if isinstance(entry, dict) and entry.get("file")
    }


@functools.lru_cache(maxsize=256)
def _icon_text(path: str) -> str:
    return Path(path).read_text()


def _icon_for(code: str | None, icons_dir: Path) -> str | None:
    if not code:
        return None
    name = _icon_index(str(icons_dir)).get(str(code))
    if not name:
        return None
    try:
        return _icon_text(str(Path(icons_dir) / name))
    except OSError:
        return None


_OPEN_SVG = re.compile(r"^.*?<svg\b[^>]*>", re.S)
_ID = re.compile(r'\bid="([^"]*)"')
_URL = re.compile(r"url\(#([^)]*)\)")
_HREF = re.compile(r'href="#([^"]*)"')


def _inner_svg(text: str) -> str:
    """Drop the icon file's own ``<svg>`` wrapper; the art hangs on a ``<g>``."""
    match = _OPEN_SVG.search(text)
    inner = text[match.end():] if match else text
    return inner.rsplit("</svg>", 1)[0]


def _prefix_ids(text: str, prefix: str) -> str:
    """Namespace one icon's ids, so the same symbol can appear twice in a row."""
    text = _ID.sub(lambda m: f'id="{prefix}{m.group(1)}"', text)
    text = _URL.sub(lambda m: f"url(#{prefix}{m.group(1)})", text)
    return _HREF.sub(lambda m: f'href="#{prefix}{m.group(1)}"', text)


def _inline_icon(text: str, prefix: str, x: float, y: float, scale: float) -> str:
    inner = _prefix_ids(_inner_svg(text), prefix)
    return (
        f'<g transform="translate({_n(x)} {_n(y)}) scale({_n(scale)})">'
        f"{inner}</g>"
    )


# ------------------------------------------------------------------- stale


def stale_label(age_seconds) -> str:
    """§8.2: hours up to 48, then days."""
    age = max(0.0, float(age_seconds or 0.0))
    hours = round(age / 3600.0)
    if hours <= STALE_MAX_HOURS:
        return f"vor {hours} h"
    days = round(age / 86400.0)
    return f"vor {days} Tagen"


def age_label(age_seconds) -> str:
    """The same chip while the data is fresh: §8.2's wording, minutes first.

    Only reached with ``show_age=True``; a fresh graph is drawn without any
    chip by default.
    """
    age = max(0.0, float(age_seconds or 0.0))
    if age < 3600:
        return f"vor {int(age // 60)} min"
    return stale_label(age)


# --------------------------------------------------------------------- svg


def _document(width: int, height: int, body: list[str]) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        + "".join(body)
        + "</svg>"
    )


def build_svg(
    samples,
    *,
    fetched_at=None,
    now=None,
    stale: bool = False,
    age_seconds=None,
    last_error: str | None = None,
    width: int = DEFAULT_WIDTH,
    theme: str = "light",
    icons_dir: Path | str | None = None,
    show_age: bool = False,
) -> str:
    """The whole image as one SVG. Deterministic for the same arguments."""
    width = clamp_width(width)
    height = round(width / 2)  # §1.3
    k = width / DESIGN_WIDTH
    palette = PALETTES.get(str(theme), PALETTES["light"])  # §2.2 unknown -> light
    icons_dir = Path(icons_dir) if icons_dir is not None else ICONS_DIR
    _, slots = window_slots(samples, fetched_at, now)

    body: list[str] = []

    def line(x1, y1, x2, y2, colour, stroke_width=1.0) -> None:
        body.append(
            f'<line x1="{_n(_px(x1, k))}" y1="{_n(_px(y1, k))}"'
            f' x2="{_n(_px(x2, k))}" y2="{_n(_px(y2, k))}"'
            f' stroke="{colour}" stroke-width="{_n(_px(stroke_width, k))}"/>'
        )

    def text(x, y, value, *, size, colour, anchor=None) -> None:
        extra = f' text-anchor="{anchor}"' if anchor else ""
        body.append(
            f'<text x="{_n(_px(x, k))}" y="{_n(_px(y, k))}"'
            f' font-family="DejaVu Sans" font-size="{_n(_px(size, k))}"{extra}'
            f' fill="{colour}">{html.escape(str(value))}</text>'
        )

    # Background: opaque, no rounded corners, no frame of its own (§1.4).
    body.append(f'<rect width="{width}" height="{height}" fill="{palette["background"]}"/>')

    # §8.3: nothing was ever fetched. Background, axis frame, the text.
    if not any(slot and slot.get("temperature") is not None for _, slot in slots):
        line(CONTENT_LEFT, TEMP_TOP, CONTENT_RIGHT, TEMP_TOP, palette["grid"])
        line(CONTENT_LEFT, TEMP_BOTTOM, CONTENT_RIGHT, TEMP_BOTTOM, palette["grid"])
        line(CONTENT_LEFT, PRECIP_BOTTOM, CONTENT_RIGHT, PRECIP_BOTTOM, palette["baseline"])
        text(DESIGN_WIDTH / 2, DESIGN_HEIGHT / 2 + 4, "noch keine Daten", size=WEEKDAY_FONT, colour=palette["text"], anchor="middle")
        if last_error:
            text(DESIGN_WIDTH / 2, DESIGN_HEIGHT / 2 + 22, str(last_error)[:90], size=AXIS_FONT, colour=palette["text"], anchor="middle")
        return _document(width, height, body)

    readings = [(i, slot) for i, (_, slot) in enumerate(slots) if slot and slot.get("temperature") is not None]
    temperatures = [float(slot["temperature"]) for _, slot in readings]
    axis_bottom = math.floor(min(temperatures) / TEMP_STEP) * TEMP_STEP  # §5.1
    axis_high = math.ceil(max(temperatures) / TEMP_STEP) * TEMP_STEP
    axis_top = axis_high + TEMP_STEP  # one reserved step for the icon row
    span = axis_top - axis_bottom

    def y_temp(value: float) -> float:
        return TEMP_TOP + (axis_top - value) * TEMP_HEIGHT / span

    points = [  # (hour, x, y) for the curve
        (i, CONTENT_LEFT + CONTENT_WIDTH * i / WINDOW_HOURS, y_temp(float(slot["temperature"])))
        for i, slot in readings
    ]

    # §5.4 every 5 °C step, labelled; §5.5 the 0 °C line is heavier.
    axis_values = [axis_bottom + step * TEMP_STEP for step in range(int(round(span / TEMP_STEP)) + 1)]
    for value in axis_values:
        heavy = value == 0
        line(
            CONTENT_LEFT, y_temp(value), CONTENT_RIGHT, y_temp(value),
            palette["zero"] if heavy else palette["grid"],
            1.5 if heavy else 1.0,
        )

    # §4.3 a vertical grid line every 6 h; the edges are panel borders, not lines.
    for hour in range(TIME_GRID_HOURS, WINDOW_HOURS, TIME_GRID_HOURS):
        x = CONTENT_LEFT + CONTENT_WIDTH * hour / WINDOW_HOURS
        line(x, TEMP_TOP, x, TEMP_BOTTOM, palette["grid"])

    # §4.4 local midnights: heavier line plus the short weekday name.
    midnights: list[tuple[float, str]] = []
    for i, (moment, _) in enumerate(slots):
        local = datetime.fromtimestamp(moment).astimezone()
        if local.hour == 0 and local.minute == 0:
            x = CONTENT_LEFT + CONTENT_WIDTH * i / WINDOW_HOURS
            midnights.append((x, WEEKDAYS[local.weekday()]))
            line(x, TEMP_TOP, x, TEMP_BOTTOM, palette["midnight"], 1.5)

    # §5.2-§5.3 the curve: Catmull-Rom, 2.5 px, round caps, no fill, no markers.
    dense: list[tuple[float, float]] = []
    for run in _runs(points):
        run_points = [(x, y) for _, x, y in run]
        if len(run_points) == 1:
            dense.append(run_points[0])
            continue
        segments = _bezier_segments(run_points)
        path = f"M {_p(run_points[0][0], k)} {_p(run_points[0][1], k)}"
        for segment in segments:
            p0, c1, c2, p1 = segment
            path += (
                f" C {_p(c1[0], k)} {_p(c1[1], k)} {_p(c2[0], k)} {_p(c2[1], k)}"
                f" {_p(p1[0], k)} {_p(p1[1], k)}"
            )
        body.append(
            f'<path d="{path}" fill="none" stroke="{palette["curve"]}"'
            f' stroke-width="{_n(_px(2.5, k))}" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for segment in segments:
            for step in range(SEGMENT_SAMPLES + 1):
                dense.append(_bezier_at(segment, step / SEGMENT_SAMPLES))

    # §6 icons: one every 3 h, in a 28 px box riding 3 px above the highest
    # curve point under it, clamped to the temperature panel.
    for hour in range(0, WINDOW_HOURS, ICON_EVERY_HOURS):
        slot = slots[hour][1]
        icon = _icon_for((slot or {}).get("symbol_code"), icons_dir)
        if icon is None:
            continue
        centre = CONTENT_LEFT + CONTENT_WIDTH * hour / WINDOW_HOURS
        left = centre - ICON_BOX / 2.0
        right = centre + ICON_BOX / 2.0
        under = [y for x, y in dense if left <= x <= right]
        if not under:
            continue
        top = min(under) - ICON_CLEARANCE - ICON_BOX
        top = max(TEMP_TOP, min(TEMP_BOTTOM - ICON_BOX, top))
        body.append(
            _inline_icon(
                icon,
                prefix=f"wg{hour}_",
                x=_px(left, k),
                y=_px(top, k),
                scale=ICON_BOX * k / 100.0,
            )
        )

    # §7 precipitation band.
    rates = []
    for _, slot in slots:
        amount = (slot or {}).get("precipitation")
        rates.append(max(0.0, float(amount)) if amount is not None else 0.0)
    peak = max(rates)
    if peak > 0:  # §7.6 all-zero hides the band
        scale_top = next((step for step in PRECIP_STEPS if step >= peak), PRECIP_STEPS[-1])  # §7.3

        def y_precip(rate: float) -> float:
            return PRECIP_BOTTOM - min(1.0, rate / scale_top) * PRECIP_HEIGHT

        xs = [CONTENT_LEFT + CONTENT_WIDTH * i / WINDOW_HOURS for i in range(WINDOW_POINTS)]
        top_ys = [y_precip(rate) for rate in rates]
        fill = f"M {_p(xs[0], k)} {_p(PRECIP_BOTTOM, k)}"
        for x, y in zip(xs, top_ys):
            fill += f" L {_p(x, k)} {_p(y, k)}"
        fill += f" L {_p(xs[-1], k)} {_p(PRECIP_BOTTOM, k)} Z"  # §7.1, §7.8 straight joins
        body.append(f'<path d="{fill}" fill="{palette["precip"]}" fill-opacity="0.55"/>')  # §7.5
        stroke = "M " + " L ".join(f"{_p(x, k)} {_p(y, k)}" for x, y in zip(xs, top_ys))
        body.append(
            f'<path d="{stroke}" fill="none" stroke="{palette["precip"]}"'
            f' stroke-width="{_n(_px(1.5, k))}"/>'
        )
        text(PRECIP_LABEL_X, PRECIP_LABEL_Y, f"{_n(scale_top)} mm/h", size=AXIS_FONT, colour=palette["text"])  # §7.4
    else:
        text(CONTENT_LEFT + CONTENT_WIDTH / 2, PRECIP_MID + 4, "kein Niederschlag", size=AXIS_FONT, colour=palette["text"], anchor="middle")  # §7.6

    line(CONTENT_LEFT, PRECIP_BOTTOM, CONTENT_RIGHT, PRECIP_BOTTOM, palette["baseline"])  # §7.2

    # §3.5, §5.6: axis values right-aligned in the gutter; the top one carries the unit.
    for value in axis_values:
        label = f"{int(value)} °C" if value == axis_values[-1] else str(int(value))
        text(AXIS_LABEL_X, y_temp(value) + 4, label, size=AXIS_FONT, colour=palette["text"], anchor="end")

    # §4.4/§4.5 weekday names, centred on their midnight line.
    for x, weekday in midnights:
        text(x, WEEKDAY_BASELINE, weekday, size=WEEKDAY_FONT, colour=palette["text"], anchor="middle")

    # §8.2 stale marker, drawn over whatever is under it (§8.4: nothing moves).
    # show_age forces the same chip on fresh data (ticket 06's debug switch).
    age = age_seconds
    if age is None and fetched_at is not None and now is not None:
        age = max(0.0, float(now) - float(fetched_at))
    if (stale or show_age) and age is not None:
        body.append(
            f'<rect x="{_n(_px(CHIP_X, k))}" y="{_n(_px(CHIP_Y, k))}"'
            f' width="{_n(_px(CHIP_WIDTH, k))}" height="{_n(_px(CHIP_HEIGHT, k))}"'
            f' rx="{_n(_px(CHIP_RADIUS, k))}" fill="{palette["background"]}" fill-opacity="0.85"/>'
        )
        body.append(
            f'<circle cx="{_n(_px(DOT_X, k))}" cy="{_n(_px(DOT_Y, k))}"'
            f' r="{_n(_px(DOT_RADIUS, k))}" fill="{palette["stale"]}"/>'
        )
        text(
            CHIP_TEXT_X,
            CHIP_TEXT_Y,
            stale_label(age) if stale else age_label(age),
            size=AXIS_FONT,
            colour=palette["stale"],
        )

    return _document(width, height, body)


# ---------------------------------------------------------------- rasterising


def _font_file(font_path: Path | str | None = None) -> str | None:
    """The font file resvg may use. Missing -> log once and render no text."""
    global _font_warned
    path = Path(font_path) if font_path is not None else FONT_PATH
    if path.is_file():
        return str(path)
    if not _font_warned:
        print(
            f"wettergraph: render font {path} is not readable; "
            "resvg draws no text at all (graph-spec §3.4)",
            flush=True,
        )
        _font_warned = True
    return None


def _rasterise(svg: str, width: int, font_path: Path | str | None = None) -> bytes:
    font = _font_file(font_path)
    return resvg_py.svg_to_bytes(
        svg_string=svg,
        width=width,
        height=round(width / 2),
        font_files=[font] if font else None,
        skip_system_fonts=True,
    )


def render_png(samples, *, font_path: Path | str | None = None, **kwargs) -> bytes:
    """Render and return PNG bytes. Same arguments -> byte-identical PNG."""
    width = clamp_width(kwargs.get("width", DEFAULT_WIDTH))
    return _rasterise(build_svg(samples, **kwargs), width, font_path)


def _view_arguments(view: dict, *, width, theme, now, icons_dir, show_age=False) -> dict:
    view = view or {}
    return dict(
        samples=view.get("samples") or [],
        fetched_at=view.get("fetched_at"),
        now=now,
        stale=bool(view.get("stale")),
        age_seconds=view.get("age_seconds"),
        last_error=view.get("last_error"),
        width=width,
        theme=theme,
        icons_dir=icons_dir,
        show_age=show_age,
    )


def build_view_svg(
    view: dict, *, width=DEFAULT_WIDTH, theme="light", now=None, icons_dir=None, show_age=False
) -> str:
    """The view from :meth:`metno.ForecastCache.view`, as SVG text."""
    return build_svg(
        **_view_arguments(view, width=width, theme=theme, now=now, icons_dir=icons_dir, show_age=show_age)
    )


def render_view(
    view: dict, *, width=DEFAULT_WIDTH, theme="light", now=None, icons_dir=None, font_path=None, show_age=False
) -> bytes:
    """The view from :meth:`metno.ForecastCache.view`, as a PNG."""
    arguments = _view_arguments(
        view, width=width, theme=theme, now=now, icons_dir=icons_dir, show_age=show_age
    )
    return render_png(font_path=font_path, **arguments)


# ----------------------------------------------------------------------- cli


def fixture_samples(start: float, hours: int = 72, *, dry: bool = False) -> list[dict]:
    """A synthetic series for local renders, so a check needs no network."""
    every = ("clearsky_day", "partlycloudy_day", "cloudy", "lightrain", "clearsky_night", "fair_night")
    start = int(float(start) // 3600) * 3600  # window_slots anchors on the hour
    samples = []
    for i in range(hours):
        moment = start + i * 3600
        temperature = 9.0 + 7.0 * math.sin((i - 7) / 24.0 * 2.0 * math.pi) + 1.6 * math.sin(i / 5.0)
        rain = 0.0
        if not dry and 10 <= i % 24 <= 14:
            rain = 0.6 + 0.35 * ((i % 24) - 10)
        samples.append(
            {
                "time": datetime.fromtimestamp(moment, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "temperature": round(temperature, 1),
                "precipitation": round(rain, 2),
                "symbol_code": every[(i // 3) % len(every)],
            }
        )
    return samples


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="render a Wettergraph PNG")
    parser.add_argument("--cache", help="forecast-cache.json to read; without it, a fixture is rendered")
    parser.add_argument("--out", default="wettergraph-sample.png")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--theme", default="light", choices=("light", "dark"))
    parser.add_argument("--now", type=float, help="epoch seconds, for a reproducible window and chip")
    parser.add_argument("--dry", action="store_true", help="fixture with no precipitation")
    parser.add_argument("--age-hours", type=float, help="draw the stale chip with this age")
    parser.add_argument("--font", default=str(FONT_PATH))
    parser.add_argument("--icons", default=str(ICONS_DIR))
    arguments = parser.parse_args(argv)

    if arguments.cache:
        document = json.loads(Path(arguments.cache).read_text())
        samples = document.get("samples") or []
        fetched_at = document.get("fetched_at")
    else:
        fetched_at = arguments.now if arguments.now is not None else time.time()
        samples = fixture_samples(fetched_at, dry=arguments.dry)
    last_error = None

    age_seconds = arguments.age_hours * 3600 if arguments.age_hours is not None else None
    png = render_png(
        samples,
        fetched_at=fetched_at,
        now=arguments.now,
        stale=age_seconds is not None,
        age_seconds=age_seconds,
        last_error=last_error,
        width=arguments.width,
        theme=arguments.theme,
        icons_dir=arguments.icons,
        font_path=arguments.font,
    )
    Path(arguments.out).write_bytes(png)
    print(f"rendered {len(samples)} samples -> {arguments.out} ({len(png)} bytes, theme={arguments.theme}, width={clamp_width(arguments.width)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
