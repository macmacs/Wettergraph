# Wettergraph (Home Assistant app)

The widget. It starts, polls met.no's `locationforecast/2.0/compact` on the
schedule met.no itself asks for, caches the last good forecast under `/data`,
and serves a status page, the normalised forecast as JSON, and the graph itself
as a PNG: temperature curve, weather icons, precipitation band, no wind
anywhere. See the map in `.scratch/wettergraph-ha-widget/map.md`.

## Install

Home Assistant OS only (native container installs have no app store).

1. Settings -> Add-ons -> Add-on Store -> three-dot menu top right ->
   **Repositories**.
2. Add `https://github.com/macmacs/Wettergraph` (the repo root holds
   `repository.yaml`; the app itself is in `wettergraph/`).
3. Reload the store page if needed, then install **Wettergraph**.
4. **Start** it and open the **Log** tab. First lines:

   `wettergraph: starting on :8099; options=/data/options.json present=True build=0.2.0`
   `wettergraph: met.no UA='Wettergraph/0.2.0 (Home Assistant app; +https://github.com/macmacs/Wettergraph)' cache=/data/forecast-cache.json`
   `wettergraph: render font /usr/share/fonts/dejavu/DejaVuSans.ttf present, icons /app/icons`

   Then the poller's first line - `metno: 200 OK, 88 samples cached to
   /data/forecast-cache.json`, or a named error instead (`403 Forbidden`,
   `429 Too Many Requests`, `unreachable`) - and a startup check that exercises
   the real routes in-process (HAOS gives you no shell inside the container, so
   this is the self-test):

   ```
   wettergraph: PASS  /health returns 200 ok  (200 b'ok\n')
   wettergraph: PASS  / serves an HTML page  (200 text/html; charset=utf-8)
   wettergraph: PASS  page lists every option  (5 rows for 5 options)
   wettergraph: PASS  option values reach the page  (latitude=48.1746)
   wettergraph: PASS  /image/graph serves a 782x391 PNG  (200 image/png 24875B 782x391)
   wettergraph: PASS  /image/graph honours ?width (clamped) and ?theme  (200 480px)
   wettergraph: PASS  /image/graph.svg serves the intermediate SVG, no wind  (200 image/svg+xml; charset=utf-8 43632B)
   wettergraph: PASS  render font is readable (graph-spec §3.4)  (/usr/share/fonts/dejavu/DejaVuSans.ttf)
   wettergraph: PASS  renderer draws the curve, 16 icons and the band (fixture)  (43613B SVG, 16 icons)
   wettergraph: PASS  unknown paths 404  (404)
   wettergraph: PASS  options file is readable  (/data/options.json)
   wettergraph: PASS  /forecast.json serves the normalised series  (200 88 samples)
   wettergraph: PASS  met.no User-Agent is descriptive  (Wettergraph/0.2.0 (Home Assistant app; +https://github.com/macmacs/Wettergraph))
   wettergraph: startup check 13/13 passed
   ```

   `render font is readable` FAILing means the image will render with every
   text node missing (resvg draws nothing when no font answers) - report it.

   `present=False`, or `options file is readable` showing FAIL, means options
   never reached the container - report that, it is the interesting failure.
   The same check can be re-run from the HA terminal with
   `docker exec $(docker ps -q -f name=wettergraph | head -1) /app/.venv/bin/python /app/server.py --self-test`.
5. Open the **Wettergraph** panel in the sidebar (or the "Open web UI" button).
   You should see the status page: a table of the options, one `forecast data:`
   line (samples, age, stale, last error), the cache path, and at the bottom
   **the graph**. The sample count should be 80-90 within a minute of starting;
   0 with a `last error` set means the fetch failed, and the error text says why.
   Until the first fetch lands the graph is the `noch keine Daten` frame, not a
   fake curve.
6. Change `page_note` under **Configuration**, save, then reload the page.
   The new value must appear **without** restarting the app. Use this to prove
   options are re-read live.

Fallback if the sidebar panel does not appear: the app is still installed and
running, and `/health` on port 8099 is what the watchdog uses. Say so instead of
fighting ingress - ingress is not on the critical path.

## Forecast data (ticket 04)

One daemon thread inside the app is the only thing that talks to met.no. It
fetches `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=&lon=`
(4 decimals, the precision met.no caches on), normalises the response, and
writes it to `/data/forecast-cache.json`.

- **User-Agent**, required by met.no:
  `Wettergraph/0.2.0 (Home Assistant app; +https://github.com/macmacs/Wettergraph)`
  (`BUILD_VERSION`, so a version bump changes it).
- **Polling follows met.no's `Expires` header**: the next request is not sent
  before it. Once it has passed, the request carries `If-Modified-Since`, and a
  `304 Not Modified` means the series is still current (still counted as a
  successful fetch).
- **No API key.** `locationforecast/2.0/compact` is open.
- **The cache survives a restart.** After a restart the log says
  `metno: restored 88 samples ...`, and no request goes out while `Expires` still
  holds.
- **A failed fetch keeps the last good series.** The app never shows an empty
  graph because the network blinked; after 6 h without a successful fetch the
  series counts as stale and the rendered image will carry the age chip
  (`assets/graph-spec.md` §8.1, §8.2).
- **`403` and `429` are named in the log** and backed off (60 s, doubling to
  30 min; `Retry-After` is honoured). The poller cannot crash-loop: errors are
  caught and the app keeps serving.

Where to look:

- status page - the `forecast data:` line (samples, age, state, last error)
- `http://<ha-host>:8099/forecast.json` - the raw view: `samples`, `fetched_at`,
  `age_seconds`, `stale`, `last_error`, `expires_at`, `cache_path`
- log - one `metno:` line per poll, roughly every 30-60 min, `304 Not Modified`
  when the model has not changed

The series shape the renderer consumes, one entry per met.no timeseries entry:

```json
{"time": "2026-09-22T18:00:00Z",     "temperature": 11.7,
 "precipitation": 0.0,                  "symbol_code": "clearsky_night"}
```

`temperature` is °C and `precipitation` is mm/h; there is no unit conversion
anywhere (`assets/graph-spec.md` §5.7 is Celsius only). `precipitation` comes
from the finest hook the entry carries: `next_1_hours` as is, `next_6_hours` and
`next_12_hours` divided back to an hourly rate. `symbol_code` is met.no's own
code (`<condition>_<timeofday>`), so day/night art follows from the string.

Expected measurements:

- Container memory: a few tens of MB (python3 + resvg, no browser).
- Startup to a served page: a few seconds.
- One render: ~70 ms at 782 px with 16 icons, so a polled camera is cheap.
- `curl http://<ha-host>:8099/health` -> `ok`, if the port is reachable from
  where you run curl. The sidebar UI works over ingress regardless.

## The graph (ticket 05)

`GET /image/graph` is the artifact: a PNG of `width x round(width/2)` (782x391
by default) drawn from the cached series to `assets/graph-spec.md` clause for
clause. Two per-request knobs, both validated by the renderer:

- `?width=` - clamped to 480..1564 (`assets/graph-spec.md` §1.2); junk falls
  back to 782.
- `?theme=light|dark` - anything unknown is light (§2.2).

What the image holds: a 48 h window from the hour of the last fetch, a
Catmull-Rom temperature curve (2.5 px) on an axis fitted in 5 °C steps with one
reserved step at the top, one icon every 3 h from `wettergraph/app/icons/`
(ticket 03's 83 MET codes, chosen by `symbol_code`, riding 3 px above the
curve), a precipitation band whose scale top is the smallest of
`{0.5, 1, 2, 5, 10, 20}` mm/h that fits, and German weekday names on the local
midnights. No wind of any kind, no attribution text - both are on purpose.

Degrading honestly: over 6 h since the last successful fetch the last good
graph is served plus the age chip (`vor 7 h`, `vor 3 Tagen`); with no cache at
all the frame plus `noch keine Daten` and the last error.

- Renderer: `wettergraph/app/render.py` - Python + `resvg-py`, no browser, no
  headless Chrome.
- Font: DejaVu Sans (`font-dejavu` in the image) loaded **by file path**, per
  spec §3.4; resvg draws no text at all when no font answers, so the startup
  check asserts the file is readable.
- The intermediate SVG stays at `/image/graph.svg` (same knobs) for debugging;
  the PNG is the published artifact.
- Samples: `assets/render-sample-light.png`, `render-sample-dark.png`,
  `render-sample-dry-stale.png`, rendered from the committed snapshot
  `assets/render-sample-cache.json`. `tools/render-check.py` proves all 56
  clause checks, including geometry parity against
  `assets/graph-reference.svg`.

## Configuration

| Option | Default | Meaning |
| --- | --- | --- |
| `page_note` | `setup probe` | Free text, shown on the status page. Proves live option reads. |
| `place_id` | `2-6325496` | met.no/yr place id, Olympia Tower by default. |
| `latitude` | `48.1746` | 4 decimals on purpose: met.no caches on ~4 decimals. |
| `longitude` | `11.5538` | Same reason. |
| `update_interval` | `15` | Minutes between refreshes. Used when met.no serves no `Expires` header; `Expires` wins when present. |

## How it is built

- Base image `ghcr.io/home-assistant/base:3.24-2026.08.0` (Alpine 3.24, s6
  overlay init, bashio), pinned rather than floating.
- `python3`, `curl`, `tzdata`, `font-dejavu`, `ca-certificates` and `uv` from
  Alpine apk. No pip, no virtualenv tooling, no interpreter download.
- `resvg-py` (the renderer's Rust extension) is installed at build time by
  `uv sync --frozen` from the committed `wettergraph/app/uv.lock` into
  `/app/.venv`; the container's `CMD` is that venv's python
  (`/app/.venv/bin/python`). musllinux wheels exist for both target arches, so
  no compiler is needed.
- `init: false` in `config.yaml` is **required**, not optional: the base image's
  s6 must be PID 1. Supervisor's `init` defaults to true, which puts Docker's
  tini in as PID 1 and makes s6 exit with
  `s6-overlay-suexec: fatal: can only run as pid 1`.
- The Dockerfile needs a `CMD` for the same reason inverted: without one, s6 has
  nothing to supervise and the container exits as soon as it finishes starting.

## Local checks

    uv run --with pyyaml --with voluptuous python tools/addon-lint.py
    uv run --with resvg-py --with pillow python tools/render-check.py   # every graph-spec clause
    uv sync --project wettergraph/app       # resvg-py into wettergraph/app/.venv

    # the renderer alone; --now makes a fixture render reproducible
    uv run --project wettergraph/app python wettergraph/app/render.py --dry --now 1758456000 --out /tmp/dry.png
    uv run --project wettergraph/app python wettergraph/app/render.py --cache /tmp/wg/forecast-cache.json --out /tmp/sample.png

    # the whole app; needs an options file, and WG_FONT on a box with no DejaVu
    # at the container's path (this development box has no system fonts at all)
    WG_OPTIONS=/tmp/options.json WG_FONT=/tmp/DejaVuSans.ttf WG_DATA=/tmp/wg \
      uv run --project wettergraph/app python wettergraph/app/server.py --self-test
    WG_OPTIONS=/tmp/options.json WG_FONT=/tmp/DejaVuSans.ttf WG_DATA=/tmp/wg \
      uv run --project wettergraph/app python wettergraph/app/server.py   # then http://localhost:8099/

    python3 wettergraph/app/metno.py --cache-dir /tmp/wg --once   # one real fetch
    python3 wettergraph/app/metno.py --cache-dir /tmp/wg --watch  # poll until Ctrl-C

`tools/addon-lint.py` re-runs Supervisor's own store scan (glob `**/config.*`
outside dot-dirs and `rootfs`, validate against the same voluptuous schema) so a
misnamed or malformed config is caught before you install anything.
