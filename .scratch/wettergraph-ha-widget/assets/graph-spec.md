# Graph visual specification

Ticket 02. Every clause is a number, a rule, or an explicit "not shown", so
implementation tickets can cite it (`spec §4.2`).

**How to read the numbers.** Every length is stated at the design width
`W0 = 782`. At any other width `W`, multiply by `k = W / 782` and round to
0.1 px. `H = round(W / 2)`, so the design canvas is `782 x 391`. Text is
scaled by `k` too; label density never changes with width.

Reference: `assets/graph-reference.svg` draws this spec with real numbers.
Preview render of it: `assets/graph-reference.png` (the box that drew it had no
DejaVu, so the labels there are Liberation Sans metrics, a hair narrower).

## §1 Output surface and size

- **§1.1** The renderer takes a width `W` and emits a PNG of `W x round(W/2)`.
  `W = 782` unless set.
- **§1.2** `W` is clamped to `480 <= W <= 1564`. A request outside the range is
  clamped, not refused. Below 480 the labels collide; above 1564 nothing is
  gained.
- **§1.3** The height is never set directly. The aspect ratio is always 2:1.
- **§1.4** The image is opaque. No transparency, no rounded corners, no border
  of its own: the dashboard card draws the frame.
- **§1.5** The PNG is the only published artifact. Any intermediate SVG stays
  inside the app.

## §2 Theme

- **§2.1** Two variants: `light` and `dark`. Same geometry, same layout, only
  the palette changes. `light` is the default.
- **§2.2** The variant is selected per request with `theme=light|dark`. An
  unknown value falls back to `light`.
- **§2.3** Palette:

| Element | light | dark |
| --- | --- | --- |
| Background | `#ffffff` | `#171a1f` |
| Grid line | `#dfe3e8` | `#333a42` |
| Zero line | `#b9c0c8` | `#5b6570` |
| Panel baseline | `#c8cfd7` | `#454d57` |
| Midnight line | `#aab2bb` | `#5b6570` |
| Text | `#4a5158` | `#c3c9d1` |
| Temperature curve | `#d81e05` | `#ff6a4d` |
| Precipitation fill | `#4a7fd4` | `#6fa8ff` |
| Stale marker | `#b45309` | `#fbbf24` |

## §3 Canvas layout

- **§3.1** Page padding `8` on all four sides.
- **§3.2** A label gutter `36` wide runs down the left of the content area.
  Content spans `x = 44` to `x = 774`, width `730`.
- **§3.3** Two stacked panels inside the content area:
  - temperature panel: `y = 8` to `y = 283`, height `275`
  - gap: `8`
  - precipitation panel: `y = 291` to `y = 383`, height `92`
- **§3.4** Text is `DejaVu Sans, Verdana, sans-serif` (Alpine package
  `font-dejavu`), size `11` for axis values and `12` for weekday names. The
  renderer loads `/usr/share/fonts/dejavu/DejaVuSans.ttf` by path, not by font
  discovery, and resvg never reaches past the first family; the rest is for a
  browser shown the SVG itself. If that file cannot be read, the app logs an
  error at start and keeps rendering: resvg draws text as nothing when no font
  answers, so a missing font silently empties every number on the image.
- **§3.5** All axis values are right-aligned to `x = 38`, vertically centred on
  their grid line. The gutter is sized for its widest label, `15 °C`.

## §4 Time window and time axis

- **§4.1** The window is always `48` hours, step `1` hour, `49` samples. The
  window starts at the hour of the current fetch, in the app's local time zone.
- **§4.2** Hourly points are joined by a Catmull-Rom spline (§5.2). No
  resampling, no averaging.
- **§4.3** A vertical grid line every `6` hours: 1 px, at `t = 6, 12, ..., 42`.
  The content edges at `t = 0` and `t = 48` are panel borders, not grid lines.
- **§4.4** Each local midnight gets a thicker line, `1.5` px, with the short
  weekday name centred on it, baseline at `y = 280` (bottom of the temperature
  panel).
- **§4.5** Weekday labels are German two-letter forms: `Mo Di Mi Do Fr Sa So`.
  The `lang` option is deliberately not in this spec (§9).
- **§4.6** No hour numbers. No clock times anywhere on the image.

## §5 Temperature axis and curve

- **§5.1** The axis is fitted to the data in 5 °C steps:
  `min = floor(min_temp / 5) * 5`, `top = ceil(max_temp / 5) * 5`, and the axis
  top is `top + 5` - one extra step reserved for the icon row.
  Axis bottom is `min`. The grid holds `(axis_top - min) / 5` steps.
- **§5.2** The curve is a Catmull-Rom spline through the hourly points,
  converted to cubic Bézier segments, tension `0.5`. It is not clipped to the
  panel top: the axis fit plus the reserved step keeps it inside.
- **§5.3** Curve stroke is `2.5` px, round caps and joins, no fill, no point
  markers, no glow.
- **§5.4** A horizontal grid line at every 5 °C step, 1 px, drawn behind the
  curve. Every line carries its value, `-10`, `-5`, `0`, ...
- **§5.5** The 0 °C line, when it is inside the axis, is drawn in the zero-line
  colour at `1.5` px instead of the grid colour. It carries the same `0` label.
- **§5.6** The unit rides on the topmost axis label: `15 °C`. No separate unit
  text, no axis title.
- **§5.7** Celsius only. No conversion, no unit option, no `°F` path.

## §6 Icon row

- **§6.1** One icon every `3` hours, centred on the hour: `t = 0, 3, ..., 45`.
  `16` icons in a 48 h window.
- **§6.2** The icon box is `28 x 28`, centred horizontally on its hour.
- **§6.3** Vertical rule: the icon sits above the highest curve point inside its
  own box width, with `3` px of clearance. It is clamped to the temperature
  panel top (`y = 8`) and never crosses into the precipitation panel.
- **§6.4** The icon is chosen by the `symbol_code` (§ symbols are
  `<condition>_<timeofday>`), so day and night art comes from the code itself.
- **§6.5** No icon label, no legend, no icon borders.
- **§6.6** The icon set itself is out of this spec: ticket 03 extracts it from
  `assets/meteogram-6325496.svg`.

## §7 Precipitation band

- **§7.1** The band plots the hourly precipitation rate in `mm/h`. One filled
  area from the zero baseline up to the value.
- **§7.2** Baseline is the panel bottom, `y = 383`, drawn at 1 px in the panel
  baseline colour.
- **§7.3** The scale top is the smallest value in `{0.5, 1, 2, 5, 10, 20}`
  mm/h that is `>=` the largest rate in the window. The band is rescaled every
  render; it is not a fixed scale.
- **§7.4** The top value is printed inside the band at its top left, at `x = 48`,
  baseline `y = 299`, as `<value> mm/h` (e.g. `2 mm/h`). It is drawn over the
  fill, which is why the fill is 55 % opaque.
- **§7.5** The fill is the precipitation colour at `55%` opacity, with a `1.5`
  px stroke in the same colour on its top edge. No grid lines inside the band.
- **§7.6** When every hourly rate in the window is `0`, the band area is
  dropped: no fill, no stroke, no scale label, and the text `kein Niederschlag`
  is centred in the band instead.
- **§7.7** Sub-zero temperatures do not turn the precipitation into snow here:
  the rate is drawn as precipitation, whatever the temperature reads.
- **§7.8** The top edge joins the hourly points with straight lines, unlike the
  temperature curve. Precipitation is intermittent; a smoothed edge would draw
  rain between hours that was never forecast.

## §8 Stale data

- **§8.1** Stale means the last successful fetch is more than `6` hours old.
- **§8.2** A stale image shows the last good graph, unchanged, plus a marker at
  the top right: a chip `70 x 18` at `(704, 8)`, rounded `3`, filled with the
  background at 85 % (so it covers whatever is under it), a `6` px dot at
  `(712, 17)`, and the age as `vor 7 h` (hours, rounded, up to 48; then
  `vor 3 Tagen`) at `x = 720`, baseline `y = 21`.
- **§8.3** No cache at all (first run, nothing ever fetched) shows the
  background, the axis frame, and the centred text `noch keine Daten`, plus the
  last error text at `11` px under it. No fake curve, no zero-filled graph.
- **§8.4** The age marker never changes the layout: no element moves, no panel
  resizes.

## §9 Not shown

Explicit omissions, so no ticket adds them back by accident:

- **§9.1** Wind: no wind band, no arrows, no speed, gust, or direction.
- **§9.2** Attribution: no met.no, NRK, or yr logo, no credit line. A private,
  unpublished widget; the operator ruled this out.
- **§9.3** Moon phases: not drawn. Night is carried by the icon art only.
- **§9.4** Hour numbers, clock times, "now" marker, mouse-over values.
- **§9.5** A `lang` option: weekday labels are German for now. Three strings
  do not earn an option yet; add it when a second language is actually needed.
- **§9.6** Any effect: shadows, gradients, glows, rounded panel corners.

## §10 Defaults

| Clause | Default |
| --- | --- |
| §1.1 width | `782` (clamped to `480..1564`) |
| §1.1 height | `round(W / 2)` |
| §2.1 theme | `light` |
| §3.2 gutter | `36` (content `44 .. 774`) |
| §4.1 window | `48 h`, step `1 h`, `49` samples |
| §4.3 time grid | every `6 h` |
| §5.1 temperature step | `5 °C` + one reserved step |
| §6.1 icon cadence | every `3 h` (`16` icons) |
| §6.2 icon box | `28 x 28` |
| §7.3 precipitation scale | smallest of `{0.5, 1, 2, 5, 10, 20}` mm/h that fits |
| §7.6 dry text | `kein Niederschlag` |
| §8.1 stale threshold | `6 h` |
