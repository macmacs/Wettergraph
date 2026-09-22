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

- [Add-on packaging and install skeleton](issues/01-addon-packaging-skeleton.md) - resolved
- [Graph visual specification](issues/02-graph-visual-spec.md) - resolved
- [Extract the yr weather icon set](issues/03-extract-yr-icon-set.md) - resolved
- [met.no client and forecast cache](issues/04-metno-client-cache.md) - resolved
- [Render the graph: temperature, icons, precipitation](issues/05-render-graph.md) - resolved
- [Auto-updating image endpoint and generic camera](issues/06-image-endpoint-generic-camera.md) - claimed; built, answer recorded in the ticket, waiting on the operator's install report

## Decisions so far

<!-- one line per closed ticket: gist + link to where the detail lives -->

- [Add-on packaging and install skeleton](issues/01-addon-packaging-skeleton.md): the repo is an app repository and the app installs and serves on HAOS - `repository.yaml` at the root, app in `wettergraph/`, pinned base `3.24-2026.08.0`, port 8099, and, on this base image, `init: false` plus an explicit `CMD` are mandatory (both are linter gates).
- [Graph visual specification](issues/02-graph-visual-spec.md): the graph is `assets/graph-spec.md` §1-§10 - a width-knob PNG (default 782x391, always 2:1, clamp 480..1564), light and dark by `theme=`, a 48 h hourly window, a 5 °C fitted axis with one reserved step for the icon row, a Catmull-Rom red curve at 2.5 px, icons every 3 h riding above the curve, one precipitation area with a snapped top, and the last good graph plus an age chip when the data is stale. Layout reference: `assets/graph-reference.svg`.
- [Extract the yr weather icon set](issues/03-extract-yr-icon-set.md): 83 met.no codes under `.scratch/wettergraph-ha-widget/assets/icons/` + `index.json`; 7 vector from the meteogram, 76 wrapping the app's webp art (the same MET art); contact sheet `assets/icon-contact-sheet.png`; extraction by `tools/extract-icons.py`.
- [met.no client and forecast cache](issues/04-metno-client-cache.md): the data side is `wettergraph/app/metno.py` (stdlib only) - an `Expires`-respecting poller with `If-Modified-Since`/304, last-good cache at `/data/forecast-cache.json`, series `{time, temperature, precipitation, symbol_code}` in °C and mm/h, `403`/`429` named and backed off; UA `Wettergraph/0.1.2 (Home Assistant app; +https://github.com/macmacs/Wettergraph)`; 88 samples live; operator confirmed `metno: 200 OK` and 9/9 on HAOS.
- [Render the graph: temperature, icons, precipitation](issues/05-render-graph.md): the renderer is `wettergraph/app/render.py` (Python + `resvg-py` pinned in `wettergraph/app/uv.lock`, no browser) - one SVG in design units, everything scaled by `k = W/782`, rasterised once; the font is loaded by file path (`/usr/share/fonts/dejavu/DejaVuSans.ttf`, spec §3.4; `font-dejavu` in the Dockerfile); `server.py` serves `/image/graph` as a PNG (plus `/image/graph.svg`) with `?width` (480..1564) and `?theme=light|dark`; `tools/render-check.py` checks the SVG against `assets/graph-reference.svg` clause for clause (57/57) and the committed samples live under `.scratch/wettergraph-ha-widget/assets/`; operator confirmed the log's `startup check 13/13 passed`, the panel graph and the dark variant on HAOS - 0.2.1 had to switch the status page to relative links because root-absolute paths 404 behind ingress.

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

- **The repo is an app repository now.** `repository.yaml` at the root, the app in `wettergraph/`, installed and serving on the operator's HAOS (ticket 01, resolved).
- **Supervisor finds apps by globbing `**/config.*`** across the whole repo, skipping only dot-directories and `rootfs`. `fdroid/config.yml` read as a malformed app until it was renamed to `fdroid/fdroid-config.yml`. Never name a file `config.yaml`/`config.yml`/`config.json` unless it is an app config or lives under a dot-directory.
- **`tools/addon-lint.py`** re-runs that scan plus Supervisor's own voluptuous schema locally, so a bad `config.yaml` is caught without installing anything. `uv run --with pyyaml --with voluptuous python tools/addon-lint.py`.
- **`ghcr.io/home-assistant/base` is Alpine 3.24** whose repositories point at Alpine 3.24 (its `io.hass.base.image` label says `alpine:3.24` while the layers came from 3.23 - the label is the accurate one). Ubuntu-style `ttf-dejavu` does not exist; the package is `font-dejavu` (main). `uv` is in community, currently 0.11.19-r0.
- **No container can be built or run in the agent's environment.** Docker is installed but the box lacks `CAP_SYS_ADMIN`, so `unshare` fails and no daemon can start. Verification is the operator's, by design.
- **The HA base images bring s6-overlay as their own init, so an app must set `init: false`.** Supervisor's `init` key defaults to `true` (supervisor/apps/model.py `default_init` -> `data["init"]`), which becomes Docker's `Init: true` - tini as PID 1 - and s6 then dies with `s6-overlay-suexec: fatal: can only run as pid 1`. Both halves are now linter gates in `tools/addon-lint.py`: s6 base without `init: false`, and s6 base with no `CMD`/`ENTRYPOINT` (the container would exit as soon as stage2 finishes).
- **A Dockerfile with no `CMD` is not "does nothing yet" - it is "container exits at once"** on an s6 base, because s6 has nothing to supervise.

- **met.no `locationforecast/2.0/compact`**: unauthenticated, `access-control-allow-origin: *`, sends `expires` + `last-modified`. 89 timeseries entries over ~223 h. `instant.details` carries `air_temperature`; `next_1_hours.details.precipitation_amount` and `next_1_hours.summary.symbol_code` are present; `next_6_hours` also present. Units come in `properties.meta.units`.
- **met.no browser-side fetching is forbidden** by met.no's own docs ("it is not possible to add your own User-Agent header... Do not use this in production environments") - so the fetch lives server-side in the add-on, never in a dashboard card.
- **`weathericon` API is dead**: `https://api.met.no/weatherapi/weathericon/2.0/` returns 404 for every variant tried (list, `.png`, `.svg`, legacy `1.1`). The only surviving icon source is this repo's `app/src/main/res/drawable/weather_icon_*.webp` (88 files, ~640K, MET's own art).
- **Two viable icon sources exist**: (a) the repo's webp files - verified to embed as a data URI and render via `resvg`; (b) yr's meteogram SVG, which contains cleanly extractable icon groups keyed by MET symbol (`01d__01d__a`, `03n__03n__*`, `04__04__*`...). Operator chose (b); ticket 03 used it for the 7 codes the meteogram holds and (a) for the remaining 76, because the art is the same.
- **met.no symbol codes** are plain `<condition>_<timeofday>`, e.g. `fair_day`, `partlycloudy_night`, `clearsky_night`, `lightrain`. Time-of-day suffix supplies day/night icon selection directly - no separate day/night calculation needed for icons.
- **yr SVG structure** (asset `assets/meteogram-6325496.svg`, kept only as icon-source reference): 782x391; temp band y≈145-253; precipitation band y≈289-337 (blue); wind band + `Wind m/s` legend below y≈253; all artwork in one `<g transform="translate(0, 84.86)">`.
- **Rendering toolchain**: no rasterizer was installed (no rsvg/inkscape/chromium/cairo), but `uv run --with resvg-py` works and renders a 782-wide SVG in ~0.07 s. Committed renders: `meteogram-full.png` (the source graph), `v3b-trim-noheader.png` (what "no wind" looks like in the temperature + icon region), `icon-embed-test.png` (webp-in-SVG embed check - the orange sun, renders correctly). Intermediate crop experiments were pruned; the map's git history holds them if ever needed.
- **`resvg` silently renders no text when no font answers**, and this dev box has no fonts at all (not even DejaVu). A render check must load the font by file path (spec §3.4, `/usr/share/fonts/dejavu/DejaVuSans.ttf` inside the container); otherwise the curve draws fine and the whole axis is blank with no error.
- **The layout reference exists**: `assets/graph-reference.svg` (hand-made at W=782) and `assets/graph-reference.png` (its resvg preview, drawn in Liberation Sans because the box has no DejaVu). It was drawn before any renderer existed, so ticket 05 has a fixed target to diff against.
- **yr place `2-6325496`** = Olympia Tower, lat `48.17459`, lon `11.5538` - the place the widget targets.
- **The icon set is 83 met.no symbol codes**: 21 base names with `_day` / `_night` / `_polartwilight` + 20 single names. MET keeps the extra-s typo in `lightssleetshowersandthunder` / `lightssnowshowersandthunder` and the API sends that spelling; the app's Java switch matches the single-s form and so misses those two conditions (latent app bug, out of scope).
- **The meteogram holds only 7 icon families** (`01d`, `01n`, `02d`, `03d`, `03n`, `04`, `46`); legacy id `46` is `lightrain`, not fog. Every icon file uses `viewBox="0 0 100 100"` and hangs its art on `<g id="<symbol_code>">`; the 7 vector files rename their defs ids to `<symbol_code>__<part>`.
- **`wettergraph/Dockerfile` installs `font-dejavu`** (ticket 05) and `render.py` loads it by file path (spec §3.4); resvg draws every text node as nothing when no font answers, with no error.
- **The icon set ships in the app image** at `wettergraph/app/icons/` (copied from `.scratch/.../assets/icons/` by ticket 05; `COPY app/ /app/` puts it at `/app/icons`); `index.json` is the `symbol_code` -> file table.
- **The data side is live in the app (ticket 04).** `wettergraph/app/metno.py` + a `metno-poller` daemon thread in `server.py`; the view is served at `/forecast.json` and on the status page. Ticket 05 reads `ForecastCache.view()`: `samples` (the 4-key dicts), `age_seconds`, `stale` (6 h, spec §8.1), `last_error`, `cache_path`; empty `samples` is the spec §8.3 case.
- **The live payload is 88 entries: hourly for the first 61 hours, then 6-hourly.** A 48 h / 49 sample window (spec §4.1) is fully inside the hourly run. `Expires` was ~32 min. Tail entries carry only `next_6_hours`; the very last one carries no precipitation hook at all (`precipitation: None`). Units are `celsius`; a non-celsius payload is refused rather than mislabelled (spec §5.7).
- **The app store only offers an update when `wettergraph/config.yaml` version changes** (now `0.2.1`). Any later ticket whose fix must reach the operator bumps it again.
- **A live 403 is not reproducible on demand**: met.no accepted a bare `python-urllib` User-Agent in a probe. The app sends the descriptive UA anyway; the 403 path is verified against a fake server.
- **HA's Generic Camera is config-flow only** (the YAML `camera: platform: generic` platform is gone) and has **no `frame_interval`**: *Frame rate* is only a floor on re-fetching an unchanged URL (`frame_interval = 1 / framerate`, default 2). The dashboard picks a new frame up about every 5 minutes because the camera access token rotates (`TOKEN_CHANGE_INTERVAL`) and that state write changes `entity_picture`. The integration sends no cache headers of its own.
- **Inside an app container `/config` is the app's own public config folder**, not Home Assistant's (app configuration docs). The one folder HA core and an app both see is `/share`, mapped with `map: - share:rw` - where the widget's fallback file lives.
