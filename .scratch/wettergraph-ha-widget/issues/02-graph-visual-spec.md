# Graph visual specification

Type: grilling
Status: open

## Question

Settle, as a written spec, what the graph looks like: output surface and dimensions, time window and tick interval, temperature axis rules, the temperature curve, the icon row (size, spacing, which icons), the precipitation band (geometry, colour, when it hides), card background and dark-mode handling.

Explicitly out of scope for this spec: wind of any kind, and the met.no / NRK logos or any attribution text (operator ruled attribution out).

## Outcome

`assets/graph-spec.md`, numbered so implementation tickets can cite clauses (`spec §3.2`), plus one hand-written reference SVG in `assets/` showing the intended layout with real numbers.

## Done when

- The spec pins a default output size - start from yr's `782x391` for legibility - and states whether it is fixed or configurable.
- Every clause is a number, a rule, or an explicit "not shown".
- The reference SVG exists, matches the spec, and renders as a readable content asset.
- No clause contradicts the destination: nothing wind-shaped.

## Answer must record

Path of the spec, the default dimensions, and any clause deliberately left open with the reason.

## Refs

- `assets/meteogram-full.png` - the look being replaced.
- `assets/v3b-trim-noheader.png` - what "no wind" means for the temperature + icon region.
