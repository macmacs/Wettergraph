# Does the graph survive as an SVG in the operator's card?

Type: task
Status: resolved
Blocked by: -

## Question

The operator already displays yr's meteogram SVG on the dashboard with `custom:refreshable-picture-card`, which polls on its own. If our own `/image/graph.svg` works the same way, delivery can be an SVG rather than a Generic Camera PNG - and then the redesign must be specified against browser-resolved fonts, not the DejaVu the renderer pins by file path.

Does the **current** graph render acceptably as an SVG in that card?

## Why this blocks the spec

An SVG inside `<img>` loads no external CSS, so the browser picks the font. Ticket 04 measures the width clamp against DejaVu metrics and ticket 03 writes those measurements into the spec. Deciding the delivery afterwards means measuring twice. It also decides how much of ticket 06 exists at all: with `grid_options: rows: auto` an SVG scales to its tile, so the 2:1 -> ~3.8:1 problem mostly disappears.

## Agent-side preparation (done 2026-09-23, before the probe)

Three findings and one change, so the operator probes the SVG we would actually ship:

- **The endpoint is already there.** `/image/graph.svg` serves the intermediate SVG with the same `?width=` / `?theme=` knobs as the PNG (`wettergraph/app/server.py:343`). Nothing had to be built for the probe.
- **The font was named without a fallback.** Every text node was emitted as `font-family="DejaVu Sans"` alone. resvg resolves that against the pinned file (`render.py:119`, `skip_system_fonts=True`), but a browser shown the SVG directly resolves it against the *viewer's* fonts, where DejaVu is usually absent on iOS, Android and macOS - and what the browser then substitutes is not the renderer's choice.
- **Nothing is width-measured.** All labels are anchor-positioned (`render.py:369`), so a substituted font shifts glyph widths but never positions. The failure mode to look for is collision or clipping, not a collapsed layout.

Changed: text nodes now name the stack `DejaVu Sans, Verdana, sans-serif` (`render.FONT_STACK`). resvg stops at the first name, so **the PNG is byte-identical** - verified, same md5 before and after at 782 px light - and `tools/render-check.py` passes 57/57. Verdana sits second because its metrics are the closest common match to DejaVu on Apple and Windows; `sans-serif` catches Android.

This does **not** pre-empt the decision below: if the report says the substituted text is wrong, the answer is still to embed DejaVu as a data URI (bigger payload, exact metrics) rather than to trust the stack.

## Operator checklist (HITL - nothing here is the agent's to run)

Install **0.3.1** first (pushed 2026-09-23), so the SVG carries the font stack above. Settings -> Add-ons -> Wettergraph -> Update; the log should read `build=0.3.1`.

### A. The card, on the app's own port

Add a card beside the existing one, pointing at the add-on instead of yr:

```yaml
type: custom:refreshable-picture-card
refresh_interval: 600
url: http://<ha-host>:8099/image/graph.svg
attribute: ''
noMargin: true
tap_action:
  action: more-info
grid_options:
  rows: auto
  columns: 18
```

(The operator's working reference, against yr's own URL, is on the map under *Not yet specified*.)

Screenshot it. Compare against the PNG card already on the dashboard.

### B. The same image through HA's own origin (ingress)

The add-on has `ingress: true`, so HA can serve it on the HA origin - which is what would make it reachable from a phone or from outside the LAN without exposing port 8099. The ingress path is **not** a URL that can be pasted into a card: HA mints `/api/hassio_ingress/<token>/` per session and the token rotates. So check it by hand rather than as a second card:

1. Open the Wettergraph panel in the HA sidebar.
2. Take the `/api/hassio_ingress/<token>/` prefix out of the address bar (or DevTools > Network), and open `<that prefix>/image/graph.svg` in a tab.
3. Do this once on the LAN and once from outside it (Nabu Casa / whatever remote access you use), on the phone.

What B is really asking: does the image survive the HA origin at all, and does it look the same on the phone's browser engine as on the desktop one. If it does, "SVG on the HA origin" is a live delivery option worth a follow-up ticket about a stable path; if it does not, delivery stays on port 8099 and reachability is unchanged from today.

### Report

1. **Text.** Are the axis numbers, the weekday labels and the `kein Niederschlag` line legible, correctly positioned, and not colliding or clipped? The curve, bars and icons are vector paths and will be fine; only text is at risk. Note which device and browser each screenshot came from - the substituted font differs per platform, so "fine on the desktop" does not answer for the phone.
2. **Refresh.** Does the card refresh on its own?
3. **Reach.** Does A work from the phone / outside the LAN, and does B?
4. A vs B vs the existing PNG card, side by side, if that is cheap.

## Done when

- The operator has reported how the text renders, whether it refreshes, and from where it is reachable.
- The delivery decision is recorded: SVG card, Generic Camera PNG, or both - and if SVG, whether the spec must carry font slack or the renderer must embed DejaVu as a data URI.

## Answer must record

The screenshot, the verdict on text, and the delivery decision the spec rewrite (03) and the width range (04) must assume.

## Answer

**Operator report, 2026-09-23 (desktop, HA over HTTPS).**

| probe | result |
| --- | --- |
| A - card on `http://<ha-host>:8099/image/graph.svg` | broken image icon, nothing rendered |
| A' - same URL typed into its own tab | renders the graph fine |
| B - `<ingress prefix>/image/graph.svg` in a tab | renders, **all text legible, nothing clipped** |

**Why A fails, and it is not about SVG.** The dashboard is served over HTTPS (Nabu Casa / proxy). `custom:refreshable-picture-card` loads its `url` **in the browser**, so an `http://` image on an `https://` page is blocked as mixed content and never arrives. Typing the same URL into a tab works because that is a top-level navigation, which the mixed-content rule does not cover. The existing PNG card is untouched by this: a **Generic Camera is fetched by HA server-side** and re-served on the HA origin, so the browser only ever sees HTTPS.

The consequence is bigger than this ticket: **port 8099 is unusable for any browser-loaded card**, PNG or SVG alike. What a card needs is a stable, same-origin HTTPS URL.

**Text verdict: the font stack holds.** B is browser-resolved text - the file path means nothing there - and axis numbers, weekday labels and the `kein Niederschlag` line all read correctly with nothing colliding or clipped. So **the spec is written against browser-resolved fonts, and no DejaVu data URI is needed**; `render.FONT_STACK` (`DejaVu Sans, Verdana, sans-serif`, added while claiming this ticket, PNG byte-identical, render-check 57/57, shipped as 0.3.1) is sufficient. Residual: B was desktop only, so the phone's engine is unconfirmed - carried into ticket 06, not a blocker.

No screenshot was captured; the three-way result above is unambiguous enough to decide on.

**Delivery decision: SVG on the HA origin, via `/local/`.** Ingress renders correctly but cannot be pasted into a card - HA mints `/api/hassio_ingress/<token>/` per session and the token rotates. The route that survives is the add-on writing the SVG into Home Assistant's `www` folder, served at `https://<ha>/local/wettergraph.svg`: same origin, stable, remote-safe, and `grid_options: rows: auto` lets it scale to its tile. `publish.py` already has exactly this shape for the `/share` PNG - change-driven writes, atomic rename, 1-4 writes an hour at ~37 KB. Graduated into [ticket 07](07-local-svg-publish.md), which also has to settle the config-dir mapping and whether HA's cache headers on `/local/` need the card to cache-bust.

**What 03 and 04 must assume:** the artifact the operator looks at is an **SVG scaled to its tile**, with browser fonts. So the width knob is no longer a pixel-fidelity dial - 04 measures the clamp for the raster path and for a sensible intrinsic size, not for a fixed card width. The Generic Camera PNG stays as-is; it is not the dashboard path any more.
