# Wind-stripped layout reference

Type: prototype
Status: open
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
