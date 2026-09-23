# Redraw the renderer to the new spec

Type: task
Status: resolved
Blocked by: 03, 04

## Question

Rewrite `wettergraph/app/render.py` so it draws the rewritten spec, and extend `tools/render-check.py` to prove it against the new reference.

## Done when

- The renderer emits the cloned layout: cell grid, day separators, gradient temperature curve, hourly rain bars on the fixed mm axis, both axis label columns, hour labels every 2 h, day labels, legend row, 24 px icons every 2 h.
- The temperature curve's red/blue gradient splits at 0 °C in user space, the way the original's `temperature-curve-gradient` does (its stops sit at 110 % when the whole window is above freezing).
- `?theme=dark` renders ticket 02's palette; `?width=` scales everything by k against the new design canvas and clamps to ticket 04's range.
- `tools/render-check.py` diffs our SVG against `assets/graph-reference-v2.svg` clause by clause and passes; the count of checks is recorded.
- Committed sample renders under `.scratch/wettergraph-redesign/assets/`: light, dark, a stale one, an empty-cache one, and one with rain over 10 mm/h.
- Same input JSON still produces a byte-identical PNG.

## Constraints

- Python plus the pinned `resvg-py`. No browser, no new runtime dependency.
- Load the font by file path (spec §3.4).
- The data side is untouched: `render.py` still reads `ForecastCache.view()` and nothing else changes in `metno.py` or `server.py` beyond what the shape change forces.
- 61 hourly points now, not 49: the window rule changes and the empty-tail case must be handled.

## Answer must record

The check count, the sample paths, and anything in the spec the implementation could not honour (with the reason).

## Answer

**91 checks, all passing** (`uv run --with resvg-py --with pillow python tools/render-check.py`),
every one named after the clause it proves. `wettergraph/app/render.py` is
redrawn against the rewritten spec; the old 782 x 391 two-panel renderer is
gone, replaced in place (§1.5).

### How the geometry is proved

The check does not re-derive the layout, it **diffs against
[ticket 01](01-layout-reference.md)'s reference**. Fed yr's own forecast - read
back out of `graph-reference-v2.svg`'s own curve - the renderer emits, element
for element: the same four row groups (`translate(30 8/32/56, 186)`), the same
**72** grid lines with the same two day separators, the same 30 hour labels,
the same 3 day labels, the same 5 + 5 axis labels, the same two axis glyphs at
`translate(-17, -6)` and `translate(739.2373, -6) scale(0.5)`, the same legend
(byte-identical once the per-node `font-family` is stripped), the same 60-segment
spline, and the same 30 icon boxes. Against `graph-reference-v2-rain.svg`, all
14 bars match to 0.05 px including the clipped 13.4 mm/h one and the position
of its printed value.

**One constant separates the two files, and it is §5.1 working.** The reference
hard-codes yr's own band (`3..33`); the ladder fits ours to `6..36` on the same
data, so every `y` differs by exactly 12 px and the gradient stop by 10 %. The
check reads both bands off the two files' own axis labels and carries the
difference, rather than pretending it is not there. That the ladder is right is
proved separately and harder: run against **yr's own dark meteogram**, read out
of `meteogram-6325496-dark.svg`'s curve, it returns `(4.0, 2.0)` - exactly the
band yr's dark file labels. §5.1's claim holds on yr's own data, not on a
fixture written to agree with it.

### Sample renders

`.scratch/wettergraph-redesign/assets/render-sample-{light,dark,stale,rain-overmax,empty}.{svg,png}`,
written by `make-samples.py` (pinned cache, pinned render hour, pinned font, so
a rerun is byte-identical). The first four run on the **real** met.no payload
from the previous map (88 entries, hourly then 6-hourly) at a render hour 13 h
after its fetch, so every one of them exercises §4.8's interpolated tail. The
over-max sample writes a wet afternoon over it, peaking at 13.4 mm/h.

### Decisions the spec left open to the implementation

1. **`k` is the `viewBox`, not a multiplication.** The SVG carries the design
   canvas (`viewBox="0 0 794.2373 210"`, `preserveAspectRatio="none"`) and the
   requested width as its intrinsic size. Same rendering, but no rounding noise,
   crisp at any size in the browser that now rescales it, and it is exactly how
   [ticket 04](04-width-range.md) measured the range. `preserveAspectRatio="none"`
   because `meet` would letterbox a sub-pixel transparent strip and §1.4 says
   opaque to the last row.
2. **The §7.5 chip's height.** The spec fixes its width (label + 2 px either
   side) but not its height: it runs `y = 0` to `12`, the plot top down to just
   under the value, which is where the clipped bar already is.
3. **Zero bars are not drawn at all.** The reference emits 60 rects a render,
   59 of them zero-height. §7.6 says no value draws no bar exactly like a `0.0`,
   so both cases emit nothing - visually identical, ~6 KB smaller.
4. **Gradient offsets are written raw**, including `120%` and negatives. SVG
   clamps them to `0..1` and collapses the two coincident stops, which is
   precisely the single flat colour §5.5 asks `pad` for; no special case.

### What the shape change forced outside `render.py`

- `server.py`: the PNG height is `render.height_for(width)`, not `width / 2`;
  the fixture self-check counts **30** icons and looks for the curve's gradient
  and the legend instead of the retired `mm/h` scale label; the width text and
  the `?width=480` probe move to the new range; the `§1.5` citation on the PNG
  route was retired by the rewrite and now cites §1.1.
- `config.yaml`: `image_width` `782 -> 794`, `int(480,1564) -> int(560,1588)`.
- `README.md`: the graph section rewritten to the new picture, the option table,
  the sample self-check output, and the render cost - **~140 ms at 794 px**
  (61 ms of it the SVG), about twice the retired 16-icon layout, measured here
  rather than carried over.

### Nothing in the spec was refused

Every clause is implemented. Two notes for whoever reads the code next:

- **§4.1 now anchors on the render hour**, so `window_slots` takes `now` and
  treats `fetched_at` only as a fallback. This is what makes §4.8 the normal
  path rather than an edge case.
- **§4.6 drops a label, never a day.** A 20:00 start still labels Mo/Di/Mi; it
  is the opening `So` that goes. An 18:00 start drops both edges, as the clause
  says.

The one thing this ticket could not do is look at it on HAOS: no HA and no
container here. That is [ticket 06](06-ship-and-confirm.md).
