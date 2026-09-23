# Width range for the new layout

Type: task
Status: open
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
