# Map: The graph looks like the yr meteogram, without the wind

**Label:** `wayfinder:map`
**Destination:** the dashboard graph is a close clone of yr's meteogram - grid, rain bars, axis labels, hours, dates - minus the wind band and the header.
**Status:** charting done 2026-09-23; frontier open. Delivery shipped as 0.4.0.

> **This map carries execution.** Like the map before it, resolving a ticket here means producing working pieces of the widget, not only decisions. Done means the operator confirms the new look on the dashboard.

## Destination

`wettergraph/app/render.py` draws a graph that reads as the same picture as `.scratch/wettergraph-ha-widget/assets/meteogram-6325496.svg` with the wind band and the yr/NRK header removed: cell grid, day separators, gradient temperature curve, hourly blue rain bars on a fixed mm axis, °C axis left, mm axis right, hour labels every 2 h, day labels, legend row. Reached when the operator sees that graph on the HA dashboard.

## Notes

- **Tracker:** local markdown, same convention as the previous map. Tickets in `issues/NN-<slug>.md`; `Type:` and `Status:` near the top; `Blocked by:` lists ticket numbers; unblocked when every listed ticket is `resolved`. Frontier = open, unblocked, unclaimed, lowest number first. Claim by setting `Status: claimed`.
- **The previous map is the substrate, not a rerun.** `.scratch/wettergraph-ha-widget/map.md` holds the verified facts about HAOS, met.no, the icon set, `resvg`, fonts and delivery. Read it before re-deriving anything; this map only changes how the picture looks.
- **Verification loop is unchanged:** the agent produces the artifact plus exact install steps, the operator installs and reports back. No HA and no container in the agent's environment.
- **Skills:** `grilling` + `domain-modeling` for decisions; `prototype` for anything answering "how should it look".
- **The reference is the original SVG**, `.scratch/wettergraph-ha-widget/assets/meteogram-6325496.svg`, used as a layout source, not at runtime. Nothing fetches yr.no when the widget renders.

## Decisions settled while charting

These came out of the charting grill and are not tickets; every ticket may assume them.

- **Fidelity: clone the geometry.** yr's own numbers - 12.2373 px per hour, 24 px per 6 °C, `#c3d0d8` grid, `#56616c` day separators, 24 px icons - not merely "the same visual language".
- **No header.** No yr logo, no NRK/Met credit, no location line. (Also a licensing choice: this widget is private and unattributed.)
- **One plot band.** In the original the rain bars live *inside* the temperature band (right-hand mm axis); the second band is wind. Sans wind there is exactly one band, 120 px tall at design width.
- **Window: fixed 60 h, 61 hourly points**, always starting at the current hour. A short payload leaves the tail empty rather than stretching the grid.
- **Columns stay 12.2373 px/h; the design canvas widens** to fit 60 of them (~794 x ~210 instead of 782 x 391). The 2:1 aspect contract dies with this change. **`12.2373` is not a yr constant**: yr fixes the plot at 722 px and divides by `n-1`, so its step moves with the payload (`722/59 = 12.2373` light, `722/58 = 12.4483` dark). We are choosing to hold the *density* fixed and let the canvas follow, which is the opposite trade - so the renderer derives the plot width from the step, never the other way round.
- **Width knob survives**, same k-scaling mechanism against the new design canvas; its range gets re-measured, not guessed.
- **Rain axis is fixed 0..10 mm**, labels every 2 mm, an over-max bar clipped with its value printed (the original has a CSS class for exactly that).
- **Both themes stay.** yr publishes a dark meteogram too (`?mode=dark`), so dark is cloned from it rather than invented.
- **Labels are German, numeric dates:** `So 20.09.`, hours `08` every 2 h.
- **Icons: 24 px, every 2 h**, riding above the curve as in the original.
- **Replace in place.** `graph-spec.md` is rewritten and `render.py` redrawn. No `?style=` toggle, no second look to maintain.
- **States:** the age chip and `noch keine Daten` stay; `kein Niederschlag` goes (an empty rain row on a fixed axis already says it).

## Tickets

Open tickets are not listed here - they are the files in `issues/`, found by scanning for open + unblocked + unclaimed.

- [Does the graph survive as an SVG in the operator's card?](issues/00-svg-delivery-probe.md)
- [Wind-stripped layout reference](issues/01-layout-reference.md)
- [yr's dark meteogram palette](issues/02-yr-dark-palette.md)
## Decisions so far

<!-- one line per closed ticket: gist + link to where the detail lives -->

- [Wind-stripped layout reference](issues/01-layout-reference.md): the reference exists - `assets/graph-reference-v2.svg` (yr's own data, so it lays beside `meteogram-full.png` directly) plus a `-rain` variant that actually shows bar geometry, both from `assets/make-reference-v2.py`, which reads its constants and yr's symbol art out of the original file at build time. **Canvas `794.2373 x 210`**: `30 + 60 x 12.2373 + 30` wide, and yr's own row stack with the 84.86 px header replaced by an 8 px margin and the wind band cut out (`8 + 24 + 24 + 120 + 10 + 18 + 6`). The full cloned-constants table is in the ticket; the two that surprise are that **yr's font sizes are rem at a 15 px root** (13 / 16 / 12 px - only 15 makes all four rem values land on whole pixels) and that the **warm/cold curve is one gradient with two coincident stops** at `y(0 °C)/120`, not two paths. Three things the original does *not* pin down, each decided in the reference and flagged for ticket 03: the **symbol's vertical placement** (demonstrably not a function of the curve height, so a stated rule replaces it), the **over-max rain value** (no instance in either yr file; whole mm, white, on the clipped bar), and the **hour-label parity at the right edge** (60 intervals end on an even index where yr's end on an odd one, so the final label is dropped). The legend row also survived the render, which clears its fog patch.

- [yr's dark meteogram palette](issues/02-yr-dark-palette.md): `?mode=dark` on our own place id serves a dark meteogram whose **geometry is byte-identical** - only six `fill:` rules in the `<style>` block and the two curve-gradient stops change (`assets/dark-palette.md` holds the full light -> dark table; the file itself is `assets/meteogram-6325496-dark.svg`). Two traps for the spec: the dark **day separator is `#c3d0d8`**, the same hex the light mode uses for its *grid*, and the over-max rain label **inverts** because it is drawn on the bar. The only non-colour difference is the moon disc in `01n`/`03n` turning warm cream; icons are shipped art, not CSS-filtered.

- [Publish the graph as an SVG Home Assistant can serve](issues/07-local-svg-publish.md): shipped as **0.4.0**. `map: - homeassistant_config:rw`, which Supervisor mounts at **`/homeassistant`** (every map type lands at `/<type-name>`; `/config` is still the app's own folder), so the add-on writes `www/wettergraph/graph-{light,dark}.svg` and HA serves them at `/local/wettergraph/...` - same origin, no rotating token. **Both themes always**, for a `sun.sun` conditional. No `?v=` needed: HA caches `/local/` for 31 days but `refreshable-picture-card` appends its own `?currentTimeCache=<ms>` per refresh. Two traps recorded there: HA registers `/local/` at startup, so a newly created `www` 404s until HA restarts once; and an unmapped app would `mkdir -p` its way into the container and look green while HA saw nothing - `Publisher` now refuses to write when its mount is absent. The PNG routes stay, demoted to cameras. **Operator confirmed both themes on the dashboard** - after a reboot, which is the `/local/`-registered-at-startup trap biting for real. Refresh-over-time and phone/remote reach are still unreported, carried to ticket 06.

- [Does the graph survive as an SVG in the operator's card?](issues/00-svg-delivery-probe.md): the SVG is fine and the **font stack holds** - through ingress, on browser-resolved fonts, every label is legible and nothing clips, so the spec needs no DejaVu data URI (`render.FONT_STACK`, shipped as 0.3.1, PNG byte-identical). What fails is the **port**: the dashboard is HTTPS, `http://<ha-host>:8099/...` is blocked as mixed content, and that kills port 8099 for *any* browser-loaded card, PNG or SVG. The Generic Camera is unaffected because HA fetches it server-side. Delivery is therefore an **SVG on the HA origin at `/local/`** ([ticket 07](issues/07-local-svg-publish.md)); ingress renders but its token rotates, so it cannot be a card URL. 03 and 04 assume an SVG scaled to its tile with browser fonts.

- [Rewrite the graph visual specification](issues/03-rewrite-spec.md): the spec is rewritten **in place** at `.scratch/wettergraph-ha-widget/assets/graph-spec.md` (358 lines), so every citation in `render.py`, `config.yaml`, `tools/render-check.py` and the README still points at the one living contract. Sections `§1..§10` held, clauses renumbered, a `§0` cloned-constants table up front and an old-to-new **retired clauses** table at the end - all 48 old clause numbers are cited in code today, so 05 re-cites as it redraws. Two inputs broke while writing. **yr's °C axis is payload-derived, not `4 px/°C`**: light runs 3 °C per grid row, dark 2 °C, same 120 px and 10 rows, so §5.1 is a ladder fit (`r` in `1,2,3,5,10` °C per row, `bottom = floor(t_min/r)*r`, `>= 29` px icon headroom) that reproduces yr's dark sample exactly. And **the empty tail is the normal case**: met.no carries exactly 61 hourly entries from *its* first hour, our window starts at the *render* hour, so §4.8 interpolates the overrun from the 6-hourly entries and the plot reaches the right edge every render. Also decided: SVG as the published artifact with `H = round(W * 210/794.2373)` (§1), a bar-coloured chip behind the over-max value (two digits are 15.3 px of ink on an 11.2373 px bar), one `6.5` h day-label rule that drops the opening day's label for an 18:00-23:00 start **and** the closing day's for a 12:00-18:00 one (a right-edge clip nobody had spotted), the age chip moved to the legend row and resized to `94 x 18` (`vor 3 Tagen` is 71.9 px, the old 70 px chip never fitted its own worst case), and a full-chrome empty state.

## Not yet specified

<!-- in-scope fog: suspected questions not yet sharp enough to ticket -->

- **Icon art at 24 px.** The set is 83 codes, 7 vector from the meteogram and 76 wrapping the app's webp art, drawn so far at 28 px. Whether the webp-backed ones still read at 24 px, and what to do if they do not, is not answerable until the first render at the new size exists - [the layout reference](issues/01-layout-reference.md) sidesteps it by using yr's own art, so the question is untouched.
- **What the shape change does to the dashboard card.** Delivery is settled ([ticket 00](issues/00-svg-delivery-probe.md)): an SVG card with `rows: auto` scales to its tile, so the 2:1 -> ~3.8:1 jump mostly dissolves. What is left: how many `columns` the tile wants at the new aspect, and whether `image_width` still means anything as an option default once the card, not the renderer, decides the displayed size. Answerable once the operator sees it.
- **What the `/local/` SVG leaves behind.** The mapping, the writer and the caching are settled ([ticket 07](issues/07-local-svg-publish.md)). What stays fog: whether the Generic Camera and the `/share` PNG are worth keeping once the dashboard reads the SVG, or whether they become dead weight nobody looks at. Not answerable until the operator has lived with the SVG card. The operator's working card, against yr's own URL, was the pattern ticket 07 copied:

  ```yaml
  type: custom:vertical-stack-in-card
  cards:
    - type: conditional
      conditions:
        - condition: state
          entity: sun.sun
          state: above_horizon
      card:
        type: custom:refreshable-picture-card
        refresh_interval: 600
        url: https://www.yr.no/en/content/2-6325496/meteogram.svg
        attribute: ''
        noMargin: true
        tap_action:
          action: more-info
        grid_options:
          rows: auto
          columns: 18
  ```

- **The phone's text.** Ticket 00's legibility verdict is desktop only; a phone browser substitutes a different font again. Carried into [ticket 06](issues/06-ship-and-confirm.md) as a check, not yet a question of its own.

- **The "now" edge.** The original graph starts at a whole even hour; ours starts at the current hour. Whether the first column needs any marker at all is a question for after the first render.

## Out of scope

<!-- ruled beyond the destination; closed, never graduates -->

- **Wind, in any form.** Unchanged from the previous map: the point of the widget.
- **The yr/NRK header and branding** - logo, "Weather forecast for ...", the Met credit. Ruled out during charting, on both layout and licensing grounds.
- **The data layer.** `metno.py`, the cache, the poller, the icon extraction: all stay as they are. This map changes the picture only.
- **Delivery mechanics.** Generic Camera, the `/share` fallback file, the ingress status page: unchanged, except for whatever the shape change forces in ticket 06.
- **Publishing the widget** (HACS, store listing, public repo). Still out, still the thing that would make the dropped attribution a real problem.
- **A `lang` option.** German strings stay hard-coded; a second language is not on the route.
