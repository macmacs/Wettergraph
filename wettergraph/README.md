# Wettergraph (Home Assistant app)

Data stage. It starts, polls met.no's `locationforecast/2.0/compact` on the
schedule met.no itself asks for, caches the last good forecast under `/data`,
and serves a status page, the normalised forecast as JSON, and a placeholder
image. Rendering is not implemented yet; no wind anywhere - see the map in
`.scratch/wettergraph-ha-widget/map.md`.

## Install

Home Assistant OS only (native container installs have no app store).

1. Settings -> Add-ons -> Add-on Store -> three-dot menu top right ->
   **Repositories**.
2. Add `https://github.com/macmacs/Wettergraph` (the repo root holds
   `repository.yaml`; the app itself is in `wettergraph/`).
3. Reload the store page if needed, then install **Wettergraph**.
4. **Start** it and open the **Log** tab. First lines:

   `wettergraph: starting on :8099; options=/data/options.json present=True build=0.1.2`
   `wettergraph: met.no UA='Wettergraph/0.1.2 (Home Assistant app; +https://github.com/macmacs/Wettergraph)' cache=/data/forecast-cache.json`

   Then the poller's first line - `metno: 200 OK, 88 samples cached to
   /data/forecast-cache.json`, or a named error instead (`403 Forbidden`,
   `429 Too Many Requests`, `unreachable`) - and a startup check that exercises
   the real routes in-process (HAOS gives you no shell inside the container, so
   this is the self-test):

   ```
   wettergraph: PASS  /health returns 200 ok  (200 'ok')
   wettergraph: PASS  / serves an HTML page  (200 text/html; charset=utf-8)
   wettergraph: PASS  page lists every option  (5 rows for 5 options)
   wettergraph: PASS  option values reach the page  (latitude=48.1746)
   wettergraph: PASS  /image/graph serves an SVG  (200 image/svg+xml; charset=utf-8 803B)
   wettergraph: PASS  unknown paths 404  (404)
   wettergraph: PASS  options file is readable  (/data/options.json)
   wettergraph: PASS  /forecast.json serves the normalised series  (200 88 samples)
   wettergraph: PASS  met.no User-Agent is descriptive  (Wettergraph/0.1.2 (Home Assistant app; +https://github.com/macmacs/Wettergraph))
   wettergraph: startup check 9/9 passed
   ```

   `present=False`, or `options file is readable` showing FAIL, means options
   never reached the container - report that, it is the interesting failure.
   The same check can be re-run from the HA terminal with
   `docker exec $(docker ps -q -f name=wettergraph | head -1) python3 /app/server.py --self-test`.
5. Open the **Wettergraph** panel in the sidebar (or the "Open web UI" button).
   You should see the status page: a table of the options, one `forecast data:`
   line (samples, age, stale, last error), and the cache path. The sample count
   should be 80-90 within a minute of starting; 0 with a `last error` set means
   the fetch failed, and the error text says why.
6. Change `page_note` under **Configuration**, save, then reload the page.
   The new value must appear **without** restarting the app. Use this to prove
   options are re-read live before the real rendering lands.

Fallback if the sidebar panel does not appear: the app is still installed and
running, and `/health` on port 8099 is what the watchdog uses. Say so instead of
fighting ingress - ingress is not on the critical path.

## Forecast data (ticket 04)

One daemon thread inside the app is the only thing that talks to met.no. It
fetches `https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=&lon=`
(4 decimals, the precision met.no caches on), normalises the response, and
writes it to `/data/forecast-cache.json`.

- **User-Agent**, required by met.no:
  `Wettergraph/0.1.2 (Home Assistant app; +https://github.com/macmacs/Wettergraph)`.
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

- Container memory: a few tens of MB (bare `python3` + stdlib).
- Startup to a served page: a few seconds.
- `curl http://<ha-host>:8099/health` -> `ok`, if the port is reachable from
  where you run curl. The sidebar UI works over ingress regardless.

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
- `python3`, `curl`, `tzdata`, `ca-certificates` and `uv` from Alpine apk.
  No pip, no virtualenv, no interpreter download.
- `resvg-py` is declared in `wettergraph/app/pyproject.toml` for the renderer
  ticket; it is not imported by the skeleton.
- `init: false` in `config.yaml` is **required**, not optional: the base image's
  s6 must be PID 1. Supervisor's `init` defaults to true, which puts Docker's
  tini in as PID 1 and makes s6 exit with
  `s6-overlay-suexec: fatal: can only run as pid 1`.
- The Dockerfile needs a `CMD` for the same reason inverted: without one, s6 has
  nothing to supervise and the container exits as soon as it finishes starting.

## Local checks

    uv run --with pyyaml --with voluptuous python tools/addon-lint.py
    python3 wettergraph/app/server.py --self-test
    python3 wettergraph/app/server.py     # then open http://localhost:8099/
    python3 wettergraph/app/metno.py --cache-dir /tmp/wg --once   # one real fetch
    python3 wettergraph/app/metno.py --cache-dir /tmp/wg --watch  # poll until Ctrl-C

`tools/addon-lint.py` re-runs Supervisor's own store scan (glob `**/config.*`
outside dot-dirs and `rootfs`, validate against the same voluptuous schema) so a
misnamed or malformed config is caught before you install anything.
