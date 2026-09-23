# Ship the new look and confirm it on the dashboard

Type: task
Status: claimed
Blocked by: 05, 07

## Question

Get the redesigned graph onto the operator's HAOS and confirm it looks like the reference there - including whatever the 2:1 -> ~3.8:1 shape change does to the card.

## Done when

- `wettergraph/config.yaml` version is bumped (the app store only offers an update when it changes) and the startup check passes in the log.
- The operator is handed exact steps: update the app, reload, look at the panel and the dashboard card, and report back with a screenshot of each theme.
- The card is made to fit the new aspect: whatever the operator has to change (`columns` on the tile, `image_width` / `image_theme` defaults) is recorded here, not rediscovered later. The card is the `/local/` SVG pair settled in [ticket 07](07-local-svg-publish.md) - `custom:refreshable-picture-card` on `/local/wettergraph/graph-{light,dark}.svg` in a `sun.sun` conditional - not a camera.
- The operator confirms: the graph matches the reference, it still refreshes on its own, and it is legible **on the phone** (ticket 00's verdict was desktop-only).

## Constraints

- Nothing in the agent's environment can run HA or a container. Every verification step is the operator's, and a step they cannot perform is a defect in this ticket.
- Do not change delivery mechanics beyond what the shape change forces.

## Answer must record

The shipped version, the operator's confirmation, and the final card configuration.

## Answer

**Shipping as 0.5.0.** Version bumped in `config.yaml`, `metno.APP_VERSION`
and the README's expected log lines. Before shipping: `tools/addon-lint.py`
accepts `Wettergraph v0.5.0`; `render-check.py` 89/91, the two FAILs both the
dev box's missing DejaVu (same known gap as ticket 07), everything the redraw
touches passes. No delivery change: same `/local/` SVG pair, same card.

### Operator checklist (HITL)

1. Settings -> Add-ons -> Wettergraph -> **Update** to 0.5.0.
2. **Log tab.** Expect `build=0.5.0` and `startup check 19/19 passed`. The
   line to look at: `renderer draws the curve, 30 icons and the bars`.
3. **Panel** (the Wettergraph sidebar page): the embedded graph is the new
   wide one, ~794 x 210.
4. **Dashboard card, current theme.** Reload the dashboard. The card needs no
   YAML change to show the new look - the URL is the same, the card's own
   `?currentTimeCache=` defeats the 31-day `/local/` cache. Screenshot it.
5. **The other theme.** The conditional only shows one at a time, so open the
   other file directly: `https://<ha>/local/wettergraph/graph-dark.svg` (or
   `-light`). Screenshot it.
6. **Card fit.** At `columns: 18`, `rows: auto`, the tile is now ~3.8:1
   instead of 2:1 - same width, about half the height. Report whether that is
   right or the tile should change (`columns`), and if so to what.
7. **Phone.** Open the same dashboard in the companion app: are hour labels,
   day labels and both axes legible?
8. **Refresh over time.** The window starts at the current hour, so the
   first hour label moves every hour. Note it now; after an hour or two it
   should have moved on its own without a reload.

**Report:** the two screenshots, the fit verdict (and any `columns` change),
phone yes/no, refresh yes/no.
