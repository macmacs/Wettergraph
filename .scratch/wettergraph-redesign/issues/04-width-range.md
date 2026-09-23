# Width range for the new layout

Type: task
Status: resolved
Blocked by: 00, 01

## Question

At which rendered widths does the new layout still hold together, and what replaces the current `480..1564` clamp?

## Done when

- The lower bound is measured, not guessed: render the reference at descending widths and find where the 2 h hour labels first collide, where the °C / mm axis labels first touch the plot, and where 24 px icons first overlap at 2 h spacing.
- The upper bound is stated with a reason (font rasterisation, PNG size, or simply nothing gained).
- The numbers are given as a small table of width -> first failure, so ticket 03 can write the clamp into the spec and ticket 05 can implement it.

## Constraints

- Measure with the same font the container uses (`/usr/share/fonts/dejavu/DejaVuSans.ttf`, `WG_FONT` on this box), by file path. `resvg` draws text as nothing when no font answers and reports no error.
- No label-thinning rule: the decision was a hard clamp range, so this ticket measures bounds, it does not invent adaptive cadence.

## Answer must record

The width -> first failure table and the two bounds the spec should carry.

## Answer

**Bounds: `560 .. 1588`, default `794`** (replacing `480 .. 1564`, default `782`).

Artifacts: `../assets/measure-width-range.py` (the harness, rerunnable) and
`../assets/width-range.json` (its output). It rasterises
`graph-reference-v2.svg` through `resvg` at each width with
`/tmp/DejaVuSans.ttf` and measures the **pixels**, not the design numbers.

### The premise the measurement broke

The ticket asked where hour labels *collide*. **They never do.** The renderer
scales every number - font sizes included - by `k = W / W0`, so the layout is
self-similar: the 30 hour labels are all present with a clean gap between them
at 320 px, and would be at 80. Nothing in this layout collides at any width.

What actually fails is **rasterisation**: glyph strokes and 1 px hairlines stop
covering whole pixels, so they grey out and merge. So the table below reads
"first failure" as first measured loss of ink, not of space.

### Width -> first failure

`hour ink` is the darkest pixel in an hour label (95 = the full `#56616c`, so
higher is greyer). `digit split` is how many of the 30 labels still have an
ink-free column between their two digits. `grid ink` is the median vertical
grid line (205 = full `#c3d0d8` on white, 255 = invisible).

| width | k | hour px | grid px | icon px | digit split | hour ink | grid ink | sep ink | PNG | first failure |
|---|---|---|---|---|---|---|---|---|---|---|
| 1588 | 2.00 | 26.0 | 2.00 | 48.0 | 30/30 | 95 | 205 | 95 | 84 kB | - (ceiling) |
| 1200 | 1.51 | 19.6 | 1.51 | 36.3 | 30/30 | 95 | 205 | 95 | 61 kB | - |
| 1000 | 1.26 | 16.4 | 1.26 | 30.2 | 30/30 | 95 | 217 | 95 | 50 kB | grid off full colour |
| **794** | **1.00** | **13.0** | **1.00** | **24.0** | **30/30** | **95** | **212** | **119** | **44 kB** | **design width; day separator already greys** |
| 720 | 0.91 | 11.8 | 0.91 | 21.8 | 30/30 | 95 | 220 | 139 | 39 kB | separator at 60 % contrast |
| 640 | 0.81 | 10.5 | 0.81 | 19.3 | 30/30 | 95 | 225 | 130 | 36 kB | grid at 60 % contrast |
| **560** | **0.71** | **9.2** | **0.71** | **16.9** | **30/30** | **95** | **229** | **170** | **30 kB** | **floor: last width with every digit split and full-colour text** |
| 520 | 0.65 | 8.5 | 0.65 | 15.7 | 29/30 | 95 | 229 | 179 | 29 kB | **first digits merge** |
| 480 | 0.60 | 7.9 | 0.60 | 14.5 | 28/30 | 104 | 225 | 159 | 27 kB | **text leaves full colour**; grid under half contrast |
| 440 | 0.55 | 7.2 | 0.55 | 13.3 | 28/30 | 95 | 235 | 175 | 24 kB | grid at 40 % |
| 400 | 0.50 | 6.5 | 0.50 | 12.1 | 26/30 | 114 | 236 | 185 | 21 kB | 4 labels merged, text clearly grey |
| 320 | 0.40 | 5.2 | 0.40 | 9.7 | 26/30 | 135 | 236 | 200 | 18 kB | separator indistinguishable from grid |

The two axis checks the ticket named never fire: the °C labels keep **5 px** of
clearance to the plot at design width and still 2 px at 320 (`x=-5` is a design
constant, so it scales like everything else, and `27` fits the 30 px gutter with
10 px to spare); the mm labels use 12 of their 30 px gutter. **Neither axis ever
touches the plot.** Nor do the 24 px icons ever overlap - but see below.

### The two bounds

**Lower: 560.** The last measured width where all 30 hour labels keep their
digit split, the text is still at full `#56616c`, and the cell grid holds above
half its contrast. 520 loses the first digit split, 480 the colour. Chosen on
ink, because space never runs out.

**Upper: 1588 = 2 x 794.** Nothing fails upward - 4000 px renders in 720 ms for
253 kB, no resvg limit in sight - so the ceiling is "nothing gained": the source
carries no detail past 2x (13 px text, 24 px icons, 1 px lines), the dashboard
card gets the **SVG** and scales it losslessly anyway ([ticket 00](00-svg-delivery-probe.md),
[ticket 07](07-local-svg-publish.md)), and 2x is exactly what a HiDPI tile wants
of the PNG routes. This is the same rule the old clamp used (`1564 = 2 x 782`),
re-applied to the new design width. Cost of the ceiling: 199 ms and 84 kB
against 87 ms and 44 kB at design width.

### Two things this measurement turned up that belong to ticket 03

1. **24 px icons clear each other by 0.47 px.** The 2 h step is `2 x 12.2373 =
   24.4746` design px and the icon box is 24. That gap is fixed by the cloned
   density, not by width, so **24 px is the largest icon this layout admits** -
   any bigger and they overlap at every width. yr has the same 0.47 px, so this
   is cloned, not a mistake. Worth a spec clause so nobody rounds 24 up.
2. **The day label can collide with the next day's.** Measured ink width of
   `So 20.09.` at 16 px / weight 600: **69.4 to 76.1 design px**, so a day
   boundary needs about **6.3 hours** of clearance. The reference is safe
   because yr's window starts at 07:00, but *ours starts at the current hour*
   (a map decision), so a render between roughly 18:00 and 23:00 puts the first
   two day labels 1 to 6 columns apart and they overlap - by up to 61 px in the
   worst case. This is width-invariant, so it is not a clamp question; it is a
   missing spec clause. Recorded in [ticket 03](03-rewrite-spec.md).

### What the clamp still governs

Delivery is the `/local/` SVG, which the card scales to its tile, so `width` no
longer decides what the dashboard shows. The clamp now governs the **PNG
routes** (Generic Camera, the `/share` fallback), which HA fetches server-side
and which really are rasterised at `width`, plus the SVG's intrinsic size. The
table applies to the browser-displayed size too - the failures are font
rasterisation, which a browser does the same way - so it doubles as the answer
to "how small a tile can this card sit in".
