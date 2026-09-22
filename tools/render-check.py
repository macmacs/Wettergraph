#!/usr/bin/env python3
"""Clause-level checks for the Wettergraph renderer (ticket 05).

    uv run --with resvg-py --with pillow python tools/render-check.py

Every check is named after the clause it proves from
``.scratch/wettergraph-ha-widget/assets/graph-spec.md``. The geometry checks
compare the renderer's output against ``assets/graph-reference.svg``, the
hand-made reference that ticket 02 drew before any renderer existed. No network
is used: the series are fixtures, so the output is reproducible.

The SVG is parsed as XML (``xml.etree``), and only top-level elements are
inspected, so art inlined into the icons cannot be mistaken for graph geometry.

Exit code 0 = every check passed.
"""

from __future__ import annotations

import io
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "wettergraph" / "app"))
REFERENCE = ROOT / ".scratch" / "wettergraph-ha-widget" / "assets" / "graph-reference.svg"
ICONS = ROOT / "wettergraph" / "app" / "icons"

import render  # noqa: E402  (path set above)

try:
    from PIL import Image  # noqa: E402
except ImportError:  # pragma: no cover - the run line installs pillow
    Image = None

# The checks need a real font: without one resvg draws no text and §3.4's check
# would report a difference that says nothing about the renderer.
FONT = os.environ.get("WG_FONT") or ""
if not Path(FONT).is_file():
    FONT = next(
        (str(candidate) for candidate in (render.FONT_PATH, Path("/tmp/DejaVuSans.ttf")) if Path(candidate).is_file()),
        str(render.FONT_PATH),
    )

# The renderer reads midnights from the local clock; pin the check to UTC so the
# parity fixture's Mo/Di land where the reference drew them (Sunday noon start).
os.environ["TZ"] = "UTC"
time.tzset()

START = int(datetime(2025, 9, 21, 12, 0, tzinfo=timezone.utc).timestamp())  # Sunday noon

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


# ------------------------------------------------------------- svg helpers


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def root_of(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def top(svg: str) -> list[ET.Element]:
    """Top-level elements only: the inlined icon art lives inside <g> groups."""
    return list(root_of(svg))


def by_tag(elements, name: str) -> list[ET.Element]:
    return [el for el in elements if local(el.tag) == name]


def texts(elements):
    return [(el, el.text or "") for el in by_tag(elements, "text")]


def number(el: ET.Element, name: str, default: float = 0.0) -> float:
    try:
        return float(el.get(name, default))
    except (TypeError, ValueError):
        return default


def close(a: float, b: float, tolerance: float = 0.05) -> bool:
    return abs(a - b) <= tolerance


def same(a: float, b: float) -> bool:
    return round(a, 1) == round(b, 1)


def iso(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fixture(t0: float, t1: float, p0: float = 0.0, p1: float = 0.0, hours: int = 49, code: str = "partlycloudy_day") -> list[dict]:
    samples = []
    for i in range(hours):
        frac = i / (hours - 1)
        samples.append(
            {
                "time": iso(START + i * 3600),
                "temperature": round(t0 + (t1 - t0) * frac, 2),
                "precipitation": round(p0 + (p1 - p0) * frac, 3),
                "symbol_code": code,
            }
        )
    return samples


def render_svg(samples, **kwargs) -> str:
    kwargs.setdefault("fetched_at", START)
    return render.build_svg(samples, icons_dir=ICONS, **kwargs)


def render_bytes(samples, **kwargs) -> bytes:
    kwargs.setdefault("fetched_at", START)
    kwargs.setdefault("now", START)
    font = kwargs.pop("font_path", FONT)
    return render.render_png(samples, icons_dir=ICONS, font_path=font, **kwargs)


def png_size(data: bytes) -> tuple[int, int]:
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def per_hour(value: float) -> float:
    return 44.0 + 730.0 * value / 48.0


def horizontal(lines_els) -> list[float]:
    return sorted(number(el, "y1") for el in lines_els if same(number(el, "x1"), 44.0) and same(number(el, "x2"), 774.0) and same(number(el, "y1"), number(el, "y2")))


def vertical(lines_els) -> list[float]:
    return sorted(number(el, "x1") for el in lines_els if same(number(el, "y1"), 8.0) and same(number(el, "y2"), 283.0) and same(number(el, "x1"), number(el, "x2")))


# ---------------------------------------------------------------- fixtures

check("the check font file exists", Path(FONT).is_file(), FONT)

parity = fixture(-1.7, 9.9, 0.0, 1.2)  # graph-reference.svg's own numbers
flat = fixture(10.0, 10.0)
dry = fixture(10.0, 14.0, 0.0, 0.0)
freezing = fixture(-10.0, -5.0, 0.0, 3.0)
peaked = [dict(sample) for sample in fixture(-20.0, -20.0)]
for i, sample in enumerate(peaked):  # a 30 °C peak inside the last icon's box
    sample["temperature"] = -20.0 + 50.0 * min(i, 45) / 45.0 if i <= 45 else 30.0 - (i - 45) * 3.0

reference_root = root_of(REFERENCE.read_text())
reference_lines = by_tag(reference_root.iter(), "line")
reference_vertical = sorted({round(number(el, "x1"), 1) for el in reference_lines if same(number(el, "y1"), 8.0) and same(number(el, "y2"), 283.0) and same(number(el, "x1"), number(el, "x2"))})
reference_horizontal = sorted({round(number(el, "y1"), 1) for el in reference_lines if same(number(el, "x1"), 44.0) and same(number(el, "x2"), 774.0) and same(number(el, "y1"), number(el, "y2"))})
reference_axis_y = sorted(round(number(el, "y"), 1) for el, _ in texts(reference_root.iter()) if same(number(el, "x"), 38.0))

parity_svg = render_svg(parity)
parity_top = top(parity_svg)
parity_lines = by_tag(parity_top, "line")
parity_horizontal = horizontal(parity_lines)
parity_vertical = vertical(parity_lines)
parity_texts = texts(parity_top)
parity_paths = by_tag(parity_top, "path")


# ------------------------------------------------------------------ §1 size


default_png = render_bytes(parity)
check("§1.1 default PNG is 782 x 391", png_size(default_png) == (782, 391), str(png_size(default_png)))
check("§1.1 the bytes are a real PNG", default_png[:8] == b"\x89PNG\r\n\x1a\n", default_png[:4].hex())

clamps = [(100, 480), (479, 480), (480, 480), (782, 782), (1564, 1564), (1600, 1564), ("junk", 782)]
clamp_detail = [(asked, png_size(render_bytes(parity, width=asked))[0]) for asked, _ in clamps]
check("§1.2 width clamps to 480..1564, junk falls back to 782", all(got == wanted for (asked, wanted), (_, got) in zip(clamps, clamp_detail)), str(clamp_detail))
check("§1.3 height is always round(W/2)", all(png_size(render_bytes(parity, width=w)) == (w, round(w / 2)) for w in (480, 781, 782, 1563, 1564)))

if Image is not None:
    alpha = Image.open(io.BytesIO(default_png)).convert("RGBA").getchannel("A").getextrema()
    check("§1.4 the image is opaque (alpha 255 everywhere)", alpha == (255, 255), str(alpha))
else:
    check("§1.4 opaqueness needs pillow", False, "run with --with pillow")

top_rects = by_tag(parity_top, "rect")
check("§1.4 no rounded panel corners, no border: one canvas rect and nothing else",
      len(top_rects) == 1 and number(top_rects[0], "x") == 0 and "stroke" not in top_rects[0].attrib,
      f"{len(top_rects)} rects")


# ---------------------------------------------------------------- §2 theme


check("§2.1/§2.2 light and dark are real variants", render_bytes(parity, theme="light") != render_bytes(parity, theme="dark"))
check("§2.2 an unknown theme falls back to light", render_bytes(parity, theme="chartreuse") == render_bytes(parity, theme="light"))

light_svg, dark_svg = render_svg(parity, theme="light"), render_svg(parity, theme="dark")
light_colours = ("#ffffff", "#dfe3e8", "#b9c0c8", "#c8cfd7", "#aab2bb", "#4a5158", "#d81e05", "#4a7fd4")
dark_colours = ("#171a1f", "#333a42", "#5b6570", "#454d57", "#c3c9d1", "#ff6a4d", "#6fa8ff")
check("§2.3 the light palette is in the light SVG", all(colour in light_svg for colour in light_colours), str([c for c in light_colours if c not in light_svg]))
check("§2.3 the dark palette is in the dark SVG", all(colour in dark_svg for colour in dark_colours), str([c for c in dark_colours if c not in dark_svg]))
check("§2.3 the dark stale colour is in a stale dark SVG", "#fbbf24" in render_svg(parity, theme="dark", stale=True, age_seconds=7 * 3600))


# --------------------------------------------------------------- §3 layout


check("§3.1/§3.2 content spans x=44..774 (padding 8, gutter 36)",
      all(same(number(el, "x1"), 44.0) and same(number(el, "x2"), 774.0) for el in parity_lines if same(number(el, "y1"), number(el, "y2"))),
      str([(number(el, "x1"), number(el, "x2")) for el in parity_lines if same(number(el, "y1"), number(el, "y2"))]))
check("§3.3 temperature panel 8..283 and precipitation baseline 383",
      close(parity_horizontal[0], 8.0) and close(parity_horizontal[-1], 383.0) and any(close(y, 283.0) for y in parity_horizontal),
      str(parity_horizontal))

axis_labels = [(el, text) for el, text in parity_texts if same(number(el, "x"), 38.0)]
check("§3.5 axis values are right-aligned at x=38",
      axis_labels and all(el.get("text-anchor") == "end" for el, _ in axis_labels), f"{len(axis_labels)} labels")
check("§3.5 the label rows match graph-reference.svg",
      sorted(round(number(el, "y"), 1) for el, _ in axis_labels) == reference_axis_y,
      f"{sorted(round(number(el, 'y'), 1) for el, _ in axis_labels)} vs {reference_axis_y}")

check("§3.4 every text node is DejaVu Sans",
      all(el.get("font-family") == "DejaVu Sans" for el, _ in parity_texts),
      str([el.get("font-family") for el, _ in parity_texts if el.get("font-family") != "DejaVu Sans"]))

with_font = render_bytes(parity, font_path=FONT)
without_font = render_bytes(parity, font_path="/nonexistent/DejaVuSans.ttf")
check("§3.4 the font is loaded by path (without it resvg draws no text)",
      with_font != without_font and len(with_font) > len(without_font), f"{len(with_font)}B vs {len(without_font)}B")


# ---------------------------------------------------------------- §4 time


curve_paths = [el for el in parity_paths if el.get("fill") == "none" and el.get("stroke") in ("#d81e05", "#ff6a4d")]
curve_d = curve_paths[0].get("d", "") if len(curve_paths) == 1 else ""
check("§4.1 one curve of 49 hourly points, x=44 to x=774",
      len(curve_paths) == 1 and curve_d.count("C") == 48 and curve_d.startswith("M 44.0") and " 774.0 " in curve_d.replace("C", " "),
      f"paths={len(curve_paths)} segments={curve_d.count('C')}")
check("§4.2 the curve is a spline (cubic Beziers)", " C " in curve_d, curve_d[:40])

expected_grid = [round(per_hour(h), 1) for h in (6, 12, 18, 24, 30, 36, 42)]
check("§4.3 a time grid line every 6 h, at the reference's x positions",
      sorted({round(x, 1) for x in parity_vertical}) == reference_vertical and reference_vertical == expected_grid,
      f"{[round(x, 1) for x in parity_vertical]} vs {reference_vertical}")

midnight_labels = [(el, text) for el, text in parity_texts if same(number(el, "y"), 280.0)]
check("§4.4/§4.5 midnights carry the German weekday at baseline y=280",
      sorted(round(number(el, "x"), 1) for el, _ in midnight_labels) == [226.5, 591.5]
      and sorted(text for _, text in midnight_labels) == ["Di", "Mo"],
      f"{[(round(number(el, 'x'), 1), text) for el, text in midnight_labels]}")
check("§4.4 midnight lines are 1.5 px",
      len([el for el in parity_lines if close(number(el, "y1"), 8.0) and close(number(el, "y2"), 283.0) and number(el, "stroke-width") == 1.5]) == 2)
check("§4.6 no clock times anywhere", not any(":" in text for _, text in parity_texts), str([t for _, t in parity_texts]))


# ------------------------------------------------------------- §5 axis/curve


labels = sorted((number(el, "y"), text) for el, text in axis_labels)
label_values = [float(text.replace(" °C", "")) for _, text in labels]
check("§5.1 the axis fits -1.7..9.9 to -5..15 with one reserved step",
      label_values == [15.0, 10.0, 5.0, 0.0, -5.0], str(label_values))
check("§5.4/§5.6 every 5 °C line is labelled, the top one carries the unit",
      labels[0][1] == "15 °C" and labels[-1][1] == "-5", str(labels))
check("§5.4/§5.5 the horizontal grid matches graph-reference.svg",
      [round(y, 1) for y in parity_horizontal if y <= 283] == [y for y in reference_horizontal if 8 <= y <= 283],
      f"{[round(y, 1) for y in parity_horizontal if y <= 283]} vs {reference_horizontal}")

zero_lines = [el for el in parity_lines if number(el, "stroke-width") == 1.5 and el.get("stroke") == "#b9c0c8"]
check("§5.5 the 0 °C line is 1.5 px in the zero colour", len(zero_lines) == 1 and close(number(zero_lines[0], "y1"), 214.2), str([(number(el, "y1"), el.get("stroke")) for el in zero_lines]))

stroke = re.search(r'stroke-width="([0-9.]+)" stroke-linecap="round" stroke-linejoin="round"', parity_svg)
check("§5.3 curve stroke 2.5 px, round caps and joins",
      bool(stroke) and stroke.group(1) == "2.5" and curve_paths and curve_paths[0].get("fill") == "none", stroke.group(1) if stroke else "no curve")
check("§5.7 celsius only", "°F" not in parity_svg and "fahrenheit" not in parity_svg.lower())

segments = render._bezier_segments([(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)])
check("§5.2 Catmull-Rom tension 0.5: C1 = P + (next - previous)/6, C2 = next - (after - P)/6",
      close(segments[0][1][0], 1.0 / 6.0) and close(segments[0][1][1], 1.0 / 6.0)
      and close(segments[0][2][0], 1.0 - 2.0 / 6.0) and close(segments[0][2][1], 1.0),
      str(segments[0]))


# ---------------------------------------------------------------- §6 icons


parity_icons = [el for el in top(parity_svg) if local(el.tag) == "g" and el.get("transform")]
icon_translates = [re.findall(r"translate\(([-0-9.]+) ([-0-9.]+)\)", el.get("transform"))[0] for el in parity_icons]
icon_scales = [re.findall(r"scale\(([-0-9.]+)\)", el.get("transform"))[0] for el in parity_icons]
check("§6.1 16 icons, one every 3 h", len(parity_icons) == 16, f"{len(parity_icons)} icons")
check("§6.2 the icon box is 28 x 28 (100-unit art scaled 0.28)",
      all(close(float(scale), 0.28, 0.0001) for scale in icon_scales), str(sorted(set(icon_scales))))
flat_icons = [el for el in top(render_svg(flat)) if local(el.tag) == "g" and el.get("transform")]
flat_translates = [re.findall(r"translate\(([-0-9.]+) ([-0-9.]+)\)", el.get("transform"))[0] for el in flat_icons]
check("§6.2/§6.3 a flat curve at the panel bottom puts the first box at (30, 252)",
      close(float(flat_translates[0][0]), 30.0) and close(float(flat_translates[0][1]), 252.0), str(flat_translates[0]))

peaked_svg = render_svg(peaked)
peaked_icons = [el for el in top(peaked_svg) if local(el.tag) == "g" and el.get("transform")]
peaked_tops = [float(re.findall(r"translate\([-0-9.]+ ([-0-9.]+)\)", el.get("transform"))[0]) for el in peaked_icons]
check("§6.3 the icon is clamped to the temperature panel top (y=8)",
      any(close(top_value, 8.0) for top_value in peaked_tops), f"tops {sorted(set(peaked_tops))}")

day = render_svg(fixture(10.0, 12.0, code="clearsky_day"))
night = render_svg(fixture(10.0, 12.0, code="clearsky_night"))
check("§6.4 day and night art come from the symbol code itself", day != night and 'id="wg0_' in day and 'id="wg0_' in night)
check("§6.6 vector icons keep their art under a prefixed id", 'id="wg0_partlycloudy_day"' in parity_svg)
check("§6.6 webp icons are inlined as a data URI",
      "base64" in render_svg(fixture(3.0, 4.0, code="fair_night")))
check("§6.5 no icon labels or legend", not any("icon" in text.lower() for _, text in parity_texts))


# -------------------------------------------------------------- §7 precip


band_fills = [el for el in parity_paths if el.get("fill-opacity") == "0.55"]
band_strokes = [el for el in parity_paths if el.get("stroke") in ("#4a7fd4", "#6fa8ff") and el.get("fill") == "none"]
check("§7.1/§7.2 one filled area from the 383 baseline",
      len(band_fills) == 1 and band_fills[0].get("d", "").startswith("M 44.0 383.0") and band_fills[0].get("d", "").count("L") == 50,
      f"fills={len(band_fills)} points={band_fills[0].get('d', '').count('L') if band_fills else 0}")
check("§7.8 the top edge joins with straight lines only",
      len(band_strokes) == 1 and band_strokes[0].get("d", "").count("C") == 0 and band_strokes[0].get("d", "").count("L") == 48,
      f"strokes={len(band_strokes)}")
check("§7.3 the scale top is the smallest of 0.5/1/2/5/10/20 that fits (peak 1.2 -> 2)",
      any(text == "2 mm/h" for _, text in parity_texts), str([t for _, t in parity_texts]))
check("§7.4 the scale label sits at (48, 299)",
      any(close(number(el, "x"), 48.0) and close(number(el, "y"), 299.0) for el, _ in parity_texts))
check("§7.5 the fill is 55 % opaque, the top edge 1.5 px",
      band_fills and band_fills[0].get("fill-opacity") == "0.55" and band_strokes and number(band_strokes[0], "stroke-width") == 1.5)

dry_svg = render_svg(dry)
dry_texts = texts(top(dry_svg))
check("§7.6 all-zero drops the band for the centred dry text",
      not any(el.get("fill-opacity") == "0.55" for el in by_tag(top(dry_svg), "path"))
      and "mm/h" not in dry_svg
      and any(text == "kein Niederschlag" and close(number(el, "x"), 409.0) and close(number(el, "y"), 341.0) for el, text in dry_texts),
      str([t for _, t in dry_texts]))

for peak, wanted in ((0.3, "0.5 mm/h"), (3.0, "5 mm/h"), (30.0, "20 mm/h")):
    check(f"§7.3 a {peak} mm/h peak is drawn against the {wanted} scale", f">{wanted}</text>" in render_svg(fixture(0.0, 1.0, 0.0, peak)))

freezing_svg = render_svg(freezing)
check("§7.7 sub-zero temperatures still draw precipitation (no snow switch)",
      any(el.get("fill-opacity") == "0.55" for el in by_tag(top(freezing_svg), "path")) and "mm/h" in freezing_svg)


# --------------------------------------------------------------- §8 stale


stale_svg = render_svg(parity, stale=True, age_seconds=7 * 3600)
stale_top = top(stale_svg)
chip_rect = [el for el in by_tag(stale_top, "rect") if close(number(el, "x"), 704.0)]
chip_dot = by_tag(stale_top, "circle")
check("§8.2 the chip is 70x18 at (704,8), the dot 6 px at (712,17), the age at (720,21)",
      len(chip_rect) == 1 and all(close(number(chip_rect[0], name), value) for name, value in (("x", 704.0), ("y", 8.0), ("width", 70.0), ("height", 18.0), ("rx", 3.0)))
      and chip_rect[0].get("fill-opacity") == "0.85"
      and len(chip_dot) == 1 and close(number(chip_dot[0], "cx"), 712.0) and close(number(chip_dot[0], "cy"), 17.0) and close(number(chip_dot[0], "r"), 3.0)
      and any(close(number(el, "x"), 720.0) and close(number(el, "y"), 21.0) and text == "vor 7 h" for el, text in texts(stale_top)),
      f"rects={len(chip_rect)} dots={len(chip_dot)}")
check("§8.2 the age reads hours up to 48, then days",
      render.stale_label(7 * 3600) == "vor 7 h"
      and render.stale_label(48 * 3600) == "vor 48 h"
      and render.stale_label(72 * 3600) == "vor 3 Tagen",
      f"{render.stale_label(7 * 3600)!r} {render.stale_label(48 * 3600)!r} {render.stale_label(72 * 3600)!r}")
check("§8.4 the marker never moves anything: the stale SVG is the fresh one plus the chip",
      stale_svg[:-6].startswith(parity_svg[:-6]) and len(stale_svg) > len(parity_svg),
      f"{len(stale_svg)}B vs {len(parity_svg)}B")

no_data = render_svg([], fetched_at=None, last_error="met.no unreachable: timeout")
check("§8.3 no cache draws the frame plus 'noch keine Daten' and the error",
      "noch keine Daten" in no_data and "met.no unreachable" in no_data
      and len(by_tag(top(no_data), "line")) == 3 and len(by_tag(top(no_data), "text")) == 2,
      f"{len(by_tag(top(no_data), 'line'))} lines, {len(by_tag(top(no_data), 'text'))} texts")


# ------------------------------------------------------- §9 nothing extra


check("§9.1 no wind of any kind", "wind" not in parity_svg.lower())
check("§9.2 no attribution text (operator decision)",
      all(word not in parity_svg.lower() for word in ("met.no", "norge", "nrk", "yr.no")))
check("§9.5 weekday labels are German", sorted(text for _, text in midnight_labels) == ["Di", "Mo"])


# ---------------------------------------------------------- determinism


check("§10 same input -> byte-identical PNG",
      render_bytes(parity) == render_bytes(parity) and render_bytes(dry) == render_bytes(dry))


# ------------------------------------------------------------------ report


failed = 0
for name, ok, detail in RESULTS:
    line = f"{'PASS' if ok else 'FAIL'}  {name}"
    if detail and not ok:
        line += f"  ({detail})"
    print(line)
    failed += 0 if ok else 1
print(f"\nrender-check: {len(RESULTS) - failed}/{len(RESULTS)} passed")
sys.exit(1 if failed else 0)
