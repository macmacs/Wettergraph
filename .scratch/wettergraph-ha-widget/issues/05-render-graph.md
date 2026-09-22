# Render the graph: temperature, icons, precipitation

Type: task
Status: claimed
Blocked by: 03, 04

## Question

Draw the graph from ticket 04's series, to ticket 02's spec: temperature curve, icon row, precipitation band. No wind. Emit a real PNG via `resvg`.

## Done when

- Output matches `assets/graph-spec.md` clause for clause, and the Answer lists which clauses were checked.
- Icons come from ticket 03's set and switch day/night from the symbol's `_day` / `_night` suffix.
- The temperature axis is labelled and self-scaling; the curve uses a spline, matching the current graph's feel. A side-by-side against `assets/graph-reference.svg` is the fastest way to see the layout is right.
- Rain appears only when rain exists, at the threshold the spec sets.
- Deterministic: same input JSON produces a byte-identical PNG.

## Constraints

- Python with `resvg-py` (verified: 782-wide render in ~0.07 s). No browser rasterizer, no headless Chrome.
- Load the font **by file path**, never by font discovery (`assets/graph-spec.md` §3.4). `resvg` renders every text node as nothing when no font answers, with no error, and this dev box has no fonts installed at all, so a render check that only looks at the curve will pass while the whole axis is blank.
- Temperature and precipitation only. No wind axis, no wind arrows, no wind legend.

## Answer must record

Renderer path, the exact command to render a sample, and the committed sample PNG.

## Answer

**Renderer path.** `wettergraph/app/render.py` - Python + `resvg-py` (the wheel
ticket 01 declared), no browser and no headless Chrome. One render builds the
whole image as a single SVG in the spec's design units, multiplying every number
by `k = W / 782` as it is written (round to 0.1 px), then rasterises once with
`resvg_py.svg_to_bytes`, with the font passed as a file path
(`/usr/share/fonts/dejavu/DejaVuSans.ttf`, spec §3.4; `WG_FONT` overrides it for
checks on a box with no fonts). `wettergraph/app/server.py` wires it in:
`/image/graph` -> the PNG, `/image/graph.svg` -> the intermediate SVG (same
knobs; stays inside the app). The startup check exercises both plus a fixture
render, so the renderer's health is visible in the log before the first fetch.

**Exact command to render a sample.**

    uv sync --project wettergraph/app
    uv run --project wettergraph/app python wettergraph/app/render.py \
        --cache .scratch/wettergraph-ha-widget/assets/render-sample-cache.json \
        --out /tmp/wettergraph-sample.png

Fixture render, no network, reproducible (fixed `--now`):

    uv run --project wettergraph/app python wettergraph/app/render.py \
        --dry --age-hours 7 --now 1758456000 --out /tmp/wettergraph-dry.png

**Committed sample PNGs** - the first two from `assets/render-sample-cache.json`
(a live met.no snapshot, 88 samples), the third a fixture:

- `assets/render-sample-light.png` - 782x391, light, dry window (`kein Niederschlag`)
- `assets/render-sample-dark.png` - the same series, dark
- `assets/render-sample-dry-stale.png` - dry band text plus the `vor 7 h` chip

**Clause by clause.** `tools/render-check.py` (committed) parses the rendered SVG
as XML, compares the data-independent geometry against
`assets/graph-reference.svg`, and prints 56 checks; run it with
`uv run --with resvg-py --with pillow python tools/render-check.py`. What it
covers, by clause:

| Clause | What was checked |
| --- | --- |
| §1.1-§1.5 | 782x391 default PNG, width clamp 480..1564, height always round(W/2), alpha 255 everywhere, one background rect, no border |
| §2.1-§2.3 | light default, dark variant, unknown theme -> light, every palette colour present (including the dark stale colour) |
| §3.1-§3.5 | content 44..774, panels 8..283, baseline 383, labels x=38 anchor end, label rows equal to the reference, DejaVu Sans on every text node, text only appears when the font file is passed |
| §4.1-§4.6 | 49-point curve (48 spline segments) from x=44 to 774, 6 h grid equal to the reference x, midnight 1.5 px lines with Mo/Di at y=280, no clock times |
| §5.1-§5.7 | axis fit with the reserved step, every 5 °C line labelled, unit on the top label, 0 °C line heavy in the zero colour, 2.5 px round caps, Catmull-Rom tension 0.5 formula, Celsius only |
| §6.1-§6.6 | 16 icons, 28 px box (scale 0.28), 3 px clearance, clamp at y=8, day/night from the symbol code, inlined art (prefixed vector ids, webp data URI) |
| §7.1-§7.8 | one fill from the 383 baseline, straight top edge (no curve on it), scale buckets (1.2->2, 0.3->0.5, 3->5, 30->20 mm/h), label at (48,299), 55 % fill + 1.5 px stroke, dry text at (409,341), sub-zero still draws rain |
| §8.1-§8.4 | 6 h stale threshold (met.no's view flag), chip 70x18 at (704,8), dot at (712,17), age at (720,21), `vor 7 h`/`vor 48 h`/`vor 3 Tagen`, stale SVG is the fresh SVG plus the chip, no-cache frame with text and error |
| §9.1-§9.5 | no wind anywhere, no attribution text, German weekday labels |
| §10 | same input -> byte-identical PNG |

**Side-by-side against the reference.** The parity fixture uses
`graph-reference.svg`'s own numbers (-1.7..9.9 °C fits -5..15, peak 1.2 mm/h ->
2 mm/h) on its own window (Sunday 12:00 local, so Mo and Di land at the same x).
The rendered grid lines, label rows, time grid, midnights and band scale come
out at the reference's coordinates, and the check asserts that
element-for-element; the two images were also compared by eye.

**One build change this ticket had to make.** `resvg-py` is a Rust extension and
the container ran plain `/usr/bin/python3`, so the Dockerfile now installs
`font-dejavu` (spec §3.4) and runs `uv sync --frozen` from the committed
`wettergraph/app/uv.lock` into `/app/.venv`; `CMD` is now
`/app/.venv/bin/python`. musllinux wheels exist for both target arches, so no
compiler enters the image.

**Evidence on this box** (no container can be built here - see map "Verified
facts"):

- `tools/render-check.py` -> 56/56.
- `server.py --self-test` -> 13/13 (every route, the font file, the fixture render).
- Determinism: two renders of the same arguments are byte-identical, and each
  committed PNG re-rendered to its committed hash.
- One render at 782 px with 16 icons: ~70 ms; SVG 44-68 KB depending on the icon mix.
- `tools/addon-lint.py` -> loadable, `v0.2.0`.

**Version.** `wettergraph/config.yaml` 0.1.2 -> 0.2.0 (and the `metno.py`
fallback UA) so the store offers the update.

## Verification (operator installs, then reports)

Install step: Settings -> Add-ons -> Add-on Store -> refresh -> **Wettergraph**
0.2.0 -> Update (it restarts). Log tab: the two `wettergraph: starting` lines,
the `render font ... present` line, the first `metno:` line, then the startup
check block.

- [x] Local: render-check 56/56, self-test 13/13, linter, determinism, samples.
- [ ] The store offers 0.2.0; the app updates, starts, and the log ends with
  `wettergraph: startup check 13/13 passed`.
- [ ] The panel shows the real graph: temperature curve, one icon every 3 h, the
  precipitation band (or `kein Niederschlag`), German weekday names, no wind. A
  screenshot is the fastest yes.
- [ ] `http://<ha-host>:8099/image/graph?theme=dark` serves the dark variant.
