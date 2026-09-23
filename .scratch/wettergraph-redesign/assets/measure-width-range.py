"""Ticket 04: measure where the v2 layout stops holding together, by width.

Renders graph-reference-v2.svg through resvg at descending widths with the
container's DejaVu file, then measures the rasterised pixels - not the design
numbers - for the failures ticket 04 names. Writes width-range.json.

Usage: uv run --with pillow --with resvg-py python measure-width-range.py
"""
import io, json, time
from pathlib import Path
import resvg_py
from PIL import Image

HERE = Path("/home/coder/Wettergraph/.scratch/wettergraph-redesign/assets")
FONT = "/tmp/DejaVuSans.ttf"
CANVAS_W, CANVAS_H = 794.2373, 210.0
STEP = 722 / 59
GUTTER_L, PLOT_W, PLOT_H = 30.0, 734.2373, 120.0
ROW_HOUR, ROW_PLOT = 32.0, 56.0
OUT = HERE  # results land beside the reference


def rasterise(svg_text, width):
    height = round(width * CANVAS_H / CANVAS_W)
    svg = svg_text.replace(f'width="{CANVAS_W}" height="210"',
                           f'width="{width}" height="{height}" viewBox="0 0 {CANVAS_W} 210"', 1)
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=width, height=height,
                                      font_files=[FONT], skip_system_fonts=True))
    return Image.open(io.BytesIO(png)).convert("L"), len(png)


def ink_cols(px, y0, y1, x0, x1, thresh):
    return [x for x in range(max(0, x0), x1) if min(px[x, y] for y in range(y0, y1)) <= thresh]


def main():
    dry = (HERE / "graph-reference-v2.svg").read_text()
    widths = [1588, 1400, 1200, 1000, 900, 794, 720, 680, 640, 600, 560, 520,
              480, 440, 400, 360, 320]
    rows = []
    for w in widths:
        k = w / CANVAS_W
        s = lambda v: v * k
        t0 = time.time(); img, nbytes = rasterise(dry, w); ms = (time.time() - t0) * 1000
        px = img.load()
        hy0, hy1 = int(s(ROW_HOUR)), int(s(ROW_HOUR + 24))

        # --- hour labels: 30 of them, at even point indices 0..58 ------------
        gaps, present, digit_gaps = [], 0, []
        prev_right = None
        for i in range(0, 60, 2):
            cx = GUTTER_L + i * STEP
            x0, x1 = int(s(cx - STEP)), int(s(cx + STEP)) + 1
            cols = ink_cols(px, hy0, hy1, x0, min(x1, img.width), 200)
            if not cols:
                continue
            present += 1
            if prev_right is not None:
                gaps.append(cols[0] - prev_right - 1)
            prev_right = cols[-1]
            # ink-free columns strictly inside this label = the digit split
            inner = [x for x in range(cols[0], cols[-1] + 1) if x not in set(cols)]
            digit_gaps.append(len(inner))
        hour_ink = min((min(px[x, y] for y in range(hy0, hy1))
                        for x in ink_cols(px, hy0, hy1, int(s(GUTTER_L)),
                                          int(s(GUTTER_L + PLOT_W)), 250)), default=255)

        # --- degC axis labels vs the plot's left edge ------------------------
        ay0, ay1 = int(s(ROW_PLOT + 12)), int(s(ROW_PLOT + PLOT_H))
        plot_x0 = int(s(GUTTER_L))
        acols = ink_cols(px, ay0, ay1, 0, plot_x0, 200)
        axis_gap = (plot_x0 - 1 - acols[-1]) if acols else None
        axis_ink = min((min(px[x, y] for y in range(ay0, ay1)) for x in acols), default=255)

        # --- grid hairlines vs the day separator, in the plot's top 8 px -----
        gy0, gy1 = int(s(ROW_PLOT)) + 1, int(s(ROW_PLOT + 8))
        verticals = []
        for i in range(1, 60):
            cx = GUTTER_L + i * STEP
            x0, x1 = int(s(cx)) - 1, int(s(cx)) + 2
            verticals.append(min(min(px[x, y] for y in range(gy0, gy1))
                                 for x in range(max(0, x0), min(x1, img.width))))
        verticals.sort()
        sep_ink = verticals[0]                      # #56616c day separator, L=95
        grid_ink = verticals[len(verticals) // 2]   # #c3d0d8 cell grid, L=205

        rows.append(dict(
            width=w, k=round(k, 3), hour_px=round(13 * k, 1), day_px=round(16 * k, 1),
            icon_px=round(24 * k, 1), hair_px=round(k, 2),
            hour_labels=present, hour_gap_min=min(gaps) if gaps else None,
            hour_gap_med=sorted(gaps)[len(gaps) // 2] if gaps else None,
            digit_split=sum(1 for g in digit_gaps if g > 0), hour_ink=hour_ink,
            axis_gap=axis_gap, axis_ink=axis_ink,
            grid_ink=grid_ink, sep_ink=sep_ink,
            png_kb=round(nbytes / 1024, 1), ms=round(ms)))
        print(json.dumps(rows[-1]), flush=True)
    (OUT / "width-range.json").write_text(json.dumps(rows, indent=1))


main()
