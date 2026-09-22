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
