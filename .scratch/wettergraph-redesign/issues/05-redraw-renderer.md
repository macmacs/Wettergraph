# Redraw the renderer to the new spec

Type: task
Status: open
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
