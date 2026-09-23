# Rewrite the graph visual specification

Type: grilling
Status: resolved
Blocked by: 00, 01, 02

## Question

Rewrite `.scratch/wettergraph-ha-widget/assets/graph-spec.md` so it specifies the cloned layout instead of the current one, clause by clause, with the same "every length at design width, scaled by k" discipline.

## Done when

- Every §-clause that the redesign invalidates is rewritten, not patched: canvas and aspect (§1), palette for both themes (§2), layout bands (§3), the 60 h window and its hour/day labels (§4), the temperature axis and gradient curve (§5), 24 px icons every 2 h (§6), rain bars on the fixed 0..10 mm axis including the over-max case (§7), states (§8), not-shown (§9), defaults (§10).
- New clauses exist for what the current spec has no words for: the cell grid, the day separators, the two-sided axis labelling, the legend row, the bar width/gap rule.
- Each geometric clause cites the reference from ticket 01, so no number is invented.
- `§9 Not shown` is updated: `kein Niederschlag` moves out of the spec, wind and attribution stay out.
- The spec is still readable as a contract a render check can diff against clause by clause.

## Constraints

- The charting decisions on the map are settled input, not open questions: fixed 60 h window, 12.2373 px/h columns, fixed 0..10 mm rain axis, both themes, German numeric labels, icons every 2 h, age chip kept, `kein Niederschlag` dropped.
- Keep the clause numbering stable where a clause survives unchanged; renumbering costs every citation elsewhere.
- The clamp is measured, not open: **`560 .. 1588`, default `794`** ([ticket 04](04-width-range.md)); write those three numbers into §1.2 with the failure they came from, not as round guesses.
- Two geometry facts from [ticket 04](04-width-range.md) need clauses of their own:
  **24 px is the icon ceiling** (icons clear each other by 0.47 px at the 2 h step,
  at every width), and **a day label is 69-76 px of ink**, so two day boundaries
  closer than ~6.3 h overlap - which our current-hour window start makes real for
  any render between roughly 18:00 and 23:00. The spec must say what the first,
  partial day's label does.

## Answer must record

The rewritten spec's path, and a list of which clauses changed, which are new, and which were deleted.

## Answer

**Path: `.scratch/wettergraph-ha-widget/assets/graph-spec.md`, rewritten in place** (358 lines).
Every existing citation site - `render.py`, `config.yaml`, `tools/render-check.py`, the README -
keeps pointing at the one living contract; the redesign folder stays references and measurements.

### Two facts found while writing, both of which broke an input

1. **yr's °C axis is payload-derived, not `4 px/°C`.** Ticket 01's constants table froze the light
   sample's number. The dark file proves otherwise: light labels `27/21/15/9/3` (3 °C per grid row,
   band `3..33`, data `7.2..23.0`), dark labels `20/16/12/8/4` (2 °C per row, band `4..24`, data
   `4.4..16.8`). Same 120 px, same 10 rows, different degrees. §5.1 is therefore a **ladder fit**:
   `r` = first of `1, 2, 3, 5, 10` °C per row where `bottom = floor(t_min/r)*r`,
   `top = bottom + 10r` leaves `>= 29` px of headroom over `t_max`; scale `12/r` px per °C. The rule
   reproduces yr's dark sample exactly and yr's step for the light one.
2. **The empty tail is the normal case, not an edge case.** met.no's compact payload carries exactly
   61 hourly entries from *its* first hour, then 6-hourly ones (verified in
   `render-sample-cache.json`: 88 entries, hourly run of 60 h, then 6 h gaps). Our window starts at
   the *render* hour, so any render an hour or more after the poll runs past the hourly data. §4.8
   fills those slots by linear interpolation from the entries the payload does carry, so the plot
   reaches the right edge every render.

### Decided in the grill

- **§1** SVG is the published artifact; `H = round(W * 210/794.2373)`; clamp `560..1588`, default
  `794`, with ticket 04's rasterisation failure written into §1.2. The 2:1 aspect contract is gone.
- **§7.5 over-max**: a rect in the bar colour behind the 12 px whole-mm label. Two digits are 15.3 px
  of ink on an 11.2373 px bar (measured off DejaVu), so the overflow lands on the background
  whenever the neighbouring hours are dry - the reference render only reads because its neighbours
  happen to be blue.
- **§4.6 day labels**: drawn only if `>= 6.5` h of window remain before the next boundary or the
  window end. One threshold covers both edges: a label is 69-76 px of ink, 6.5 h is 79.5 px. Drops
  the opening day's label for a window starting 18:00-23:00 (ticket 04's overlap) and the closing
  day's for one starting 12:00-18:00, where it would run off the canvas - the right-edge case was
  not known before; it fell out of the same measurement.
- **§6.3** icon bottom 5 px above the curve's highest point across its own 24 px, clamped; §5.1
  reserves `24 + 5 = 29` px for it. **§6.5** one icon set for both themes (76 of 83 wrap raster art;
  yr's dark moon tint is not clonable) - recorded as §9.3.
- **§8.2** age chip moved to the legend row, right-aligned to the plot's right edge, and resized to
  `94 x 18`: `vor 3 Tagen` is 71.9 px of ink at 12 px, so the old 70 px chip never fitted its own
  worst case. **§8.3** empty state draws the full chrome (all of it is derivable from the clock),
  with a `0..30` fallback band.

### Clauses: changed, new, retired

**New** (no words existed for these): §0 cloned-constants table, §3.6 (the °C label's degree sign is
dropped when the band bottom is `<= -10 °C`, because `-10°` is 27.7 px against a 30 px gutter and
would be clipped), §3.7 legend row, §4.3 cell grid, §4.4 day separators, §4.6 day-label threshold,
§4.7 hour labels, §4.8 tail interpolation, §5.2 label values, §7.3 bar-per-interval, §7.4 bar
geometry, §7.5 over-max, §7.6 missing value, §9.3 dark moon tint, §9.7 `kein Niederschlag` dropped.

**Held, same meaning** (citations in code stay valid): §1.2, §1.4, §2.1, §2.2, §2.3, §3.4, §4.1,
§4.2, §5.7, §8.1, §8.2, §8.3, §8.4, §9.1, §9.2, §9.5.

**Retired or repurposed** - the spec ends with the full old-to-new table: §1.3, §1.5, §3.1, §3.2,
§3.3, §3.5, §4.3, §4.4, §4.5, §4.6, §5.1, §5.4, §5.5, §5.6, §6.1, §6.2, §6.3, §7.1, §7.2, §7.3,
§7.4, §7.5, §7.6, §9.4. Every one of the 48 clause numbers is cited somewhere in code today, so
ticket 05 re-cites as it redraws; the table is what makes an old citation traceable.

### Flagged

- **§9.4 keeps "no now marker"**, which is the old spec's wording, not a new decision. The map's fog
  patch *The "now" edge* stays open: if the operator wants a marker after the first render it is a
  spec change, not a gap.
- Nothing in the ticket's Done-when was dropped. The clamp numbers, the 24 px icon ceiling and the
  day-label ink from ticket 04 are all in the spec as §1.2, §6.2 and §4.6.
