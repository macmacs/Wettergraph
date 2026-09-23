# yr's dark meteogram palette

Type: research
Status: resolved
Blocked by: -

## Question

yr serves a dark variant of the same meteogram (`https://www.yr.no/en/content/2-6325496/meteogram.svg?mode=dark`). What is its palette, and does anything but colour change?

## Done when

- The dark SVG is fetched and kept as `../assets/meteogram-6325496-dark.svg`.
- A colour table maps every element we clone - background, cell grid, day separator, temperature curve (both gradient stops), rain bar, axis text, day/hour label text, legend text and swatches - from the light value to the dark one.
- It is stated explicitly whether geometry, font sizes, opacity or the icon art differ between the two variants, or whether only fills and strokes change.
- If the URL does not serve a dark variant for this place id, that is the finding: record what it does return, and the palette question goes back to the map as fog.

## Constraints

- Read-only research. Touch no renderer code.
- Respect the same rule as the light one: this is a layout/palette source, never a runtime dependency.

## Answer must record

The fetched file path, the light -> dark colour table, and any non-colour difference.

## Answer

Fetched from `https://www.yr.no/en/content/2-6325496/meteogram.svg?mode=dark` - HTTP 200, 141 472 B,
2026-09-23. The map's place id worked; the `2-2867714` fallback was not needed.

Saved as **`../assets/meteogram-6325496-dark.svg`**.
Full findings: **`../assets/dark-palette.md`**.

Caveat: the light reference is from 2026-09-20 and the dark one from 2026-09-23, so they hold
different forecasts (60 vs 59 hourly points). Every numeric difference traced back to that, not to
`mode=dark`.

### Colour table

| Element | Light | Dark |
|---|---|---|
| Background (`<svg>` style + full-canvas rect) | `#ffffff` | `#020a14` |
| Cell grid lines | `#c3d0d8` | `#374759` |
| Day separator lines | `#56616c` | `#c3d0d8` |
| Temperature curve, above 0 °C (gradient stop 1) | `#c60000` | `#ff2d3f` |
| Temperature curve, below 0 °C (gradient stops 2-3) | `#006edb` | `#00b8f1` |
| Rain bars | `#006edb` | `#00b8f1` |
| Default text fill / day labels | `#21292b` | `#ffffff` |
| Hour labels | `#56616c` | `#a2a5b3` |
| °C and mm axis labels | `#56616c` | `#a2a5b3` |
| Legend text | `#56616c` | `#a2a5b3` |
| Over-max rain value (drawn on the bar) | `#ffffff` | `#21292b` |
| Legend swatch - temperature | `#c60000` | `#ff2d3f` |
| Legend swatch - precipitation | `#006edb` | `#00b8f1` |

Two traps: the dark **day separator is `#c3d0d8`**, which is the light mode's *grid* colour - the
same hex does a different job in each file. And the over-max label **inverts**, because it sits on
top of a clipped rain bar rather than on the background.

### Non-colour differences

Only one, and it is still a recolour rather than a layout change:

- **Night symbols swap the moon gradient.** `01n` and `03n` keep every `d=` path byte-identical but
  move the moon disc from grey `#686E73 -> #6A7075` to warm cream `#C7B789 -> #E1C578`. Cloud fills
  in those same icons are unchanged. Day icons (`01d`, `02d`, `03d`, `04`) are byte-identical once
  Figma's per-build filter ids are normalised away. The weather icons are **shipped art, not
  filtered art** - the only CSS `filter:` recolours are on the monochrome axis-unit glyphs and the
  wind arrows.

Everything else is identical: canvas `782x391`; all font sizes, weights, line-heights and the font
stack (only the six `fill:` rules in the `<style>` block differ); every group transform (`30 0`,
`30 24`, `30 48`, `30 168`, `30 180`, `30 252`, legend at `translate(30, 278)` with `0/126/258`
offsets); the 120 px band and its `x1=0 x2=722` grid at matching y values; axis label positions
(`x="-5"`); stroke widths (`1.5` x3, `2` x2, curve at `2`); and opacity (only `0`, `.3`, `.6`, all
inside icon art - no mode-level overlay).

### Flag for ticket 03

`12.2373 px/h` is **derived, not fixed**: the plot is always 722 px wide and yr divides by `n - 1`.
Light's 60 points give `722/59 = 12.2373`; dark's 59 points give `722/58 = 12.4483`. The fixed
60 h / 61-point window already decided in the map computes its own step, so treat `12.2373` as "what
yr emitted for a 60-point payload", not as a column width to hard-code.
