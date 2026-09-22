# Graph visual specification

Type: grilling
Status: resolved

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

## Answer

Spec: `assets/graph-spec.md` (§1-§10, every clause numbered for citation).
Reference layout: `assets/graph-reference.svg`, preview `assets/graph-reference.png`.
Settled with the operator over three rounds of questions; every answer below is
their choice, not a guess.

**Default dimensions:** `W = 782`, `H = round(W / 2) = 391` (always 2:1). Width is
the only size knob; it clamps to `480..1564`. So the size is configurable, and
height is never set directly.

The calls, in the spec's own terms:

- **§1-§2 surface:** one opaque PNG per request; `width` and `theme=light|dark`
on the request; light is the default.
- **§3-§4 window:** always 48 h hourly (49 samples), a 6 h time grid, heavier
midnight lines carrying German short weekday names, no clock times at all.
- **§5 axis:** fitted in 5 °C steps plus one reserved step of headroom for the
icon row; Catmull-Rom curve, 2.5 px, red; 0 °C line drawn heavier; Celsius only.
- **§6 icons:** one every 3 h in a 28 x 28 box, riding 3 px above the highest
curve point under it, day or night art from the symbol code itself.
- **§7 precipitation:** one filled area, straight top edge, band top from
`{0.5, 1, 2, 5, 10, 20}` mm/h, and the whole band is dropped when 48 h are dry.
- **§8 stale:** last good graph plus a small age chip (`vor 7 h`); a graph that
was never fetched shows `noch keine Daten`, never a fake curve.

**Left open on purpose:**

- **§9.5 `lang`:** weekday labels are German short forms (`Mo Di Mi`) for now.
Three strings do not earn a config option before a second language is needed.
- **§9.1/§9.2/§9.3:** wind, attribution, and moon phases stay out. The first two
follow the map's destination and the operator's earlier ruling; moon phases are
dropped because night is already carried by the icon art.

**Two tickets contradicted this spec and were corrected, not left dangling:**
ticket 04's "stale since HH:MM" note (the spec has no clock times, §4.6) and its
"unit conversion happens here" bullet (the spec is Celsius only, §5.7).

**Fact found while resolving:** `resvg` draws text as *nothing* when no font
answers, and the dev box has no fonts installed at all. The renderer must pass
the font file by path, never rely on font discovery (spec §3.4).

## Done when, checked

- Default output size pinned and its configurability stated: §1.1-§1.3.
- Every clause is a number, a rule, or an explicit "not shown": §9 holds the
"not shown" list.
- Reference SVG exists, matches the spec, and renders as a readable asset:
`graph-reference.svg`, rendered to `graph-reference.png` at W=782 in 0.04 s.
- No clause is wind-shaped: §9.1.
