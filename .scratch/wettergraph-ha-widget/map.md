# Map: Wettergraph in Home Assistant, without the wind

**Label:** `wayfinder:map`
**Destination:** the widget renders on the dashboard, updates on its own schedule, shows no wind band and no wind data.

> **This map carries execution.** Unlike the wayfinder default, resolving a ticket here means producing working pieces of the widget, not only decisions.

## Destination

A Home Assistant widget showing a Wettergraph-style forecast graph with **no wind**: temperature curve + weather icons + precipitation band. It renders on the dashboard and **updates on its own schedule**. Reached when the graph is visible on the dashboard and refreshes without manual action.

## Notes

- **Tracker:** local markdown. Tickets in `issues/NN-<slug>.md`; `Type:` and `Status:` lines near the top; `Blocked by:` lists ticket numbers; a ticket is unblocked when every file it lists is `resolved`. Frontier = open, unblocked, unclaimed, lowest number first. Claim by setting `Status: claimed`.
- **Issue tracker is NOT GitHub/Linear for this effort.** No tracker config has been scaffolded in this repo.
- **Home Assistant:** HAOS. Operator can install custom components/cards, edit YAML, and run a sidecar/add-on. **UI-only fallback is not needed.**
- **Verification loop (operator decision):** agent produces artifact + exact install steps; **the operator installs and reports back** (screenshot / errors). No HA runs in the agent's environment, no token is shared. An install step the operator can't perform is a defect.
- **met.no compliance, deliberately relaxed by operator.** The add-on sends a real custom `User-Agent` (met.no requires this and returns 403 otherwise). The operator chose **no attribution**: private use, not for publication. Recorded here so nobody "fixes" it later without knowing it was a choice.
- **No API key needed.** `locationforecast/2.0/compact` is unauthenticated; send a descriptive `User-Agent` and honour `Expires` / `If-Modified-Since`. `WETTERGRAPH_API_KEY` in this repo is for other endpoints and is unused here.
- **The Android app is a reference, not a base.** This widget is not an Android change; the app shares the input data (met.no), not the deliverable. Its icon art and symbol-mapping code are reusable references.

## Tickets

Open tickets are not listed here - they are the files in `issues/`, found by scanning for open + unblocked + unclaimed. What is wired today:

- [Add-on packaging and install skeleton](issues/01-addon-packaging-skeleton.md) - frontier
- [Graph visual specification](issues/02-graph-visual-spec.md) - frontier
- [Extract the yr weather icon set](issues/03-extract-yr-icon-set.md) - frontier
- [met.no client and forecast cache](issues/04-metno-client-cache.md) - frontier
- [Render the graph: temperature, icons, precipitation](issues/05-render-graph.md) - blocked by 02, 03, 04
- [Auto-updating image endpoint and generic camera](issues/06-image-endpoint-generic-camera.md) - blocked by 01, 05

## Decisions so far

<!-- one line per closed ticket: gist + link to where the detail lives -->

_(empty - no tickets resolved yet)_

## Not yet specified

<!-- in-scope fog: suspected questions not yet sharp enough to ticket -->

_(empty - the frontier is specifiable; anything newly surfaced lands here or becomes a ticket)_

## Out of scope

<!-- ruled beyond the destination; closed, never graduates -->

- **Changing the Android app / shipping the widget as an app feature.** The destination is a dashboard widget; the app is reference material only.
- **Cropping or scraping yr.no's `meteogram.svg`.** The delivered graph is rendered from met.no JSON; nothing at runtime depends on yr.no's SVG, its internal layout, or its CORS behaviour. (Ticket 02 was opened on the crop assumption and closed when the render decision landed.)
- **Wind data of any kind** - speed, gust, direction, arrows, wind axis. The point of the widget.
- **Publishing** the widget (HACS submission, store listing, public repo). That is what would make the dropped attribution a real problem; it is out of scope, not forgotten.

## Verified facts

Established during charting, so tickets don't re-derive them:

- **The repo is an app repository now.** `repository.yaml` at the root, the app in `wettergraph/` (ticket 01, awaiting the operator's install report).
- **Supervisor finds apps by globbing `**/config.*`** across the whole repo, skipping only dot-directories and `rootfs`. `fdroid/config.yml` read as a malformed app until it was renamed to `fdroid/fdroid-config.yml`. Never name a file `config.yaml`/`config.yml`/`config.json` unless it is an app config or lives under a dot-directory.
- **`tools/addon-lint.py`** re-runs that scan plus Supervisor's own voluptuous schema locally, so a bad `config.yaml` is caught without installing anything. `uv run --with pyyaml --with voluptuous python tools/addon-lint.py`.
- **`ghcr.io/home-assistant/base` is Alpine 3.24** whose repositories point at Alpine 3.24 (its `io.hass.base.image` label says `alpine:3.24` while the layers came from 3.23 - the label is the accurate one). Ubuntu-style `ttf-dejavu` does not exist; the package is `font-dejavu` (main). `uv` is in community, currently 0.11.19-r0.
- **No container can be built or run in the agent's environment.** Docker is installed but the box lacks `CAP_SYS_ADMIN`, so `unshare` fails and no daemon can start. Verification is the operator's, by design.
- **The HA base images bring s6-overlay as their own init, so an app must set `init: false`.** Supervisor's `init` key defaults to `true` (supervisor/apps/model.py `default_init` -> `data["init"]`), which becomes Docker's `Init: true` - tini as PID 1 - and s6 then dies with `s6-overlay-suexec: fatal: can only run as pid 1`. Both halves are now linter gates in `tools/addon-lint.py`: s6 base without `init: false`, and s6 base with no `CMD`/`ENTRYPOINT` (the container would exit as soon as stage2 finishes).
- **A Dockerfile with no `CMD` is not "does nothing yet" - it is "container exits at once"** on an s6 base, because s6 has nothing to supervise.

- **met.no `locationforecast/2.0/compact`**: unauthenticated, `access-control-allow-origin: *`, sends `expires` + `last-modified`. 89 timeseries entries over ~223 h. `instant.details` carries `air_temperature`; `next_1_hours.details.precipitation_amount` and `next_1_hours.summary.symbol_code` are present; `next_6_hours` also present. Units come in `properties.meta.units`.
- **met.no browser-side fetching is forbidden** by met.no's own docs ("it is not possible to add your own User-Agent header... Do not use this in production environments") - so the fetch lives server-side in the add-on, never in a dashboard card.
- **`weathericon` API is dead**: `https://api.met.no/weatherapi/weathericon/2.0/` returns 404 for every variant tried (list, `.png`, `.svg`, legacy `1.1`). The only surviving icon source is this repo's `app/src/main/res/drawable/weather_icon_*.webp` (88 files, ~640K, MET's own art).
- **Two viable icon sources exist**: (a) the repo's webp files - verified to embed as a data URI and render via `resvg`; (b) yr's meteogram SVG, which contains cleanly extractable icon groups keyed by MET symbol (`01d__01d__a`, `03n__03n__*`, `04__04__*`...). Operator chose (b).
- **met.no symbol codes** are plain `<condition>_<timeofday>`, e.g. `fair_day`, `partlycloudy_night`, `clearsky_night`, `lightrain`. Time-of-day suffix supplies day/night icon selection directly - no separate day/night calculation needed for icons.
- **yr SVG structure** (asset `assets/meteogram-6325496.svg`, kept only as icon-source reference): 782x391; temp band y≈145-253; precipitation band y≈289-337 (blue); wind band + `Wind m/s` legend below y≈253; all artwork in one `<g transform="translate(0, 84.86)">`.
- **Rendering toolchain**: no rasterizer was installed (no rsvg/inkscape/chromium/cairo), but `uv run --with resvg-py` works and renders a 782-wide SVG in ~0.07 s. Committed renders: `meteogram-full.png` (the source graph), `v3b-trim-noheader.png` (what "no wind" looks like in the temperature + icon region), `icon-embed-test.png` (webp-in-SVG embed check - the orange sun, renders correctly). Intermediate crop experiments were pruned; the map's git history holds them if ever needed.
- **yr place `2-6325496`** = Olympia Tower, lat `48.17459`, lon `11.5538` - the place the widget targets.
