# Wind-stripped layout reference

Type: prototype
Status: resolved
Blocked by: -

## Question

What exactly does the original meteogram look like with the wind band and the header removed, the window stretched to 60 hourly columns, and nothing else changed? Produce the SVG that answers it: `../assets/graph-reference-v2.svg`, the artifact ticket 03 writes its numbers from and ticket 05 diffs against.

## Done when

- `assets/graph-reference-v2.svg` renders (via `resvg`) to a PNG a human can put beside `.scratch/wettergraph-ha-widget/assets/meteogram-full.png` and call the same picture minus wind.
- It is derived from `meteogram-6325496.svg`, not redrawn by eye: the grid lines, day separators, curve gradient, bar geometry, label positions and font sizes carry over as numbers.
- The design canvas is stated and justified: plot width `60 x 12.2373 = 734.2`, plus the left °C gutter and the right mm gutter, giving roughly `794 x 210`.
- Every element sits where the original puts it: hour labels every 2 h above the plot, day labels at midnight boundaries, °C axis right-aligned left of the plot, mm axis left-aligned right of it, legend row under the plot.
- A short table in the Answer lists each cloned constant (px/hour, px per °C, grid colours, bar width and gap, stroke widths, font sizes) so ticket 03 can cite them.

## Constraints

- Layout source only. Nothing at runtime may fetch or depend on yr.no.
- Light theme only here; dark is ticket 02.
- Sample data may be the original's own values - this reference is about geometry, not about our forecast.
- German labels (`So 20.09.`, hours `08`) so the label widths in the reference are the real ones.

## Answer must record

The path of the reference SVG and its PNG preview, the design canvas size, and the cloned-constants table.

## Answer

**Artifacts** (all under `.scratch/wettergraph-redesign/assets/`):

| | |
|---|---|
| `graph-reference-v2.svg` / `.png` | the reference. yr's **own** forecast (its 60 hourly temperatures read back out of its curve path, one extrapolated to reach 61 points, its own single 0.1 mm rain hour), so it can be laid beside `meteogram-full.png` directly |
| `graph-reference-v2-rain.svg` / `.png` | same geometry, a rain sample injected, incl. one 13.4 mm bar so the clipped over-max case is visible. yr's own file is dry and shows no bar geometry at all |
| `make-reference-v2.py` | the generator. Every constant is lifted from the original file; the symbol art and the two axis glyphs are read out of it at build time |

PNGs rendered with `resvg` at `zoom=2` and `/tmp/DejaVuSans.ttf` (no fonts are installed in this box).
Nothing in the SVG references yr.no: the only URLs are the two XML namespaces.

**Design canvas: `794.2373 x 210`.** Width is `30 + 60 x 12.2373 + 30` - yr's own left and right
gutters around a plot re-derived from the step, exactly the trade the map chose (hold the density,
let the canvas follow). Height is yr's own row stack with the 84.86 px header block replaced by an
8 px top margin, and the wind band (`+168` to `+268`) cut out so the legend follows the plot at the
same 10 px gap it used after the wind arrows: `8 + 24 + 24 + 120 + 10 + 18 + 6 = 210`.

### Cloned constants

Every number below is verbatim from `meteogram-6325496.svg` unless the note says otherwise.

| | Value | Where it comes from |
|---|---|---|
| px per hour | `12.237288135593220` | `722 / 59`. Held fixed; the plot width follows |
| plot | `734.2373 x 120` | `60 x step` wide; the 120 px band height is yr's |
| gutters | left `30`, right `30` | yr's plot group is at `x=30` in a 782 px canvas |
| row offsets | day `8`, hour `32`, plot `56`, legend `186` | yr's inner offsets `+0 / +24 / +48`, header replaced by an 8 px margin |
| horizontal grid | every `12` px, 11 lines incl. `y=0` and `y=120` | `#c3d0d8`, 1 px |
| vertical grid | every `12.2373` px, 61 lines | `#c3d0d8`, 1 px, full height |
| day separator | same x, `#56616c`, 1 px | at local midnight |
| °C scale | `4` px/°C - grid row `3` °C, band `30` °C | axis labels `27/21/15/9/3` at `y=24..120` |
| °C axis | `x=-5`, `text-anchor="end"`, every `24` px, `y=0` unlabelled | |
| mm scale | `12` px/mm, `0` at `y=120`, `10` mm at `y=0` | labels `8/6/4/2/0` at the same y |
| mm axis | `x=plot+5` (`739.2373`), `text-anchor="start"` | |
| rain bar | `x = i*step + 0.5`, `width = step - 1 = 11.2373`, `y = 120 - 12*mm` | fill `#006edb` |
| over-max bar | clipped to `height=120`, value printed on it | see the caveat below |
| curve | stroke `2`, no fill | Catmull-Rom to cubic Bezier, tension `1/6`, both ends duplicated - verified against yr's first two segments to the 4th decimal |
| curve gradient | `userSpaceOnUse`, `y1=0 y2=120`, `spreadMethod="pad"` | two **coincident** stops at `offset = y(0 °C) / 120` (`110%` in this sample), `#c60000` above, `#006edb` below, plus a trailing `#006edb` at `100%`. That is yr's whole warm/cold mechanism |
| symbols | `24` px, every 2 h, centred on the **odd** point index (`x = i*step - 12`) | so a symbol sits mid-cell, half a 2-h step off the hour labels |
| axis glyphs | yr's 24 px thermometer and droplet at `scale(0.5)`, `translate(-17,-6)` and `translate(plot+5,-6)` | yr tints them with a CSS `filter:`; we set `#56616c` directly, `resvg` does not do filter functions |
| day label | `16` px, weight `600`, `#21292b`, `x` = the boundary, anchor start, `y=12 dy=0.35em` | |
| hour label | `13` px, `#56616c`, anchor middle, `y=9 dy=0.35em` | |
| legend | entries at `x=0` and `x=126`; swatch `10x10` at `y=4` (temperature: inner `rect y="40%" height="20%"`; rain: full); text `x=14 y=9 dy=0.35em`, `13` px `#56616c` | wind entry (`x=258`) dropped |
| over-max label | `12` px, `#ffffff`, anchor middle, `y=6 dy=0.35em` | |
| colours | bg `#ffffff`, grid `#c3d0d8`, separator `#56616c`, text `#21292b`, muted `#56616c`, warm `#c60000`, cold + rain `#006edb` | |

**Font sizes are yr's rem values at a 15 px root**: `0.8666667rem` -> **13 px** (hour, axis, legend),
`1.0666667rem` -> **16 px** (day), `0.8rem` -> **12 px** (over-max). All four rem values in the file
land on whole pixels at 15 and at no other plausible root, which is what fixes it. The reference uses
`render.FONT_STACK` (`DejaVu Sans, Verdana, sans-serif`), so its label widths are the real ones.

### Three things the original does not pin down

1. **The symbol's vertical placement is not recoverable.** It is not a function of the curve height
   at that point: two symbols in yr's own file sit over a curve at `y=70.0` and `y=69.6` but at
   `y=33.44` and `y=39.12`. Measuring each symbol's bottom against the curve's highest point across
   its own 24 px gives gaps of `3.2` to `8.1` px, median `5.3`. The reference therefore **states a
   rule** rather than cloning one: *bottom sits 5 px above the curve's highest point across the
   symbol's own width, clamped into the plot.* It matches yr exactly where the curve is flat and is
   within ~3 px everywhere else. Symbols are drawn last, over the bars, as in the original - a tall
   rain bar can run through one, which is yr's behaviour too (visible in the rain variant at 17:00).
2. **The over-max rain value has no instance in either yr file**, light or dark - only the CSS class.
   White on a 11.2373 px bar can only be legible where it sits on blue, and nothing longer than two
   digits fits, so the reference prints **whole millimetres** (`13`, not `13.4`). It still overflows
   the bar by ~1 px a side. Ticket 03 may want to reconsider the whole treatment.
3. **The hour-label parity collides at the right edge.** yr's window ends on an odd index, so its
   last label lands one step inside the plot. Ours ends on an even one, and a label there would sit
   on the mm axis. The reference labels every 2 h **except the final point** - 30 labels, the same
   count yr draws.

### Also settled here

The **legend row stays**, two entries, German: `Temperatur °C` and `Niederschlag mm` at yr's own
`x=0` / `x=126` offsets. On the real render it costs 24 of 210 px and still reads; that was fog
(*"whether the row earns its ~20 px"*), and the render answers it.
