# Wettergraph (Home Assistant app)

Skeleton stage. It starts, serves a status page and a placeholder image, and
shows the app options the way Supervisor passes them. No forecast data, no
rendering, no wind - see the map in `.scratch/wettergraph-ha-widget/map.md`.

## Install

Home Assistant OS only (native container installs have no app store).

1. Settings -> Add-ons -> Add-on Store -> three-dot menu top right ->
   **Repositories**.
2. Add `https://github.com/macmacs/Wettergraph` (the repo root holds
   `repository.yaml`; the app itself is in `wettergraph/`).
3. Reload the store page if needed, then install **Wettergraph**.
4. **Start** it and open the **Log** tab. First line:

   `wettergraph: starting on :8099; options=/data/options.json present=True build=0.1.1`

   Followed by a startup check that exercises the real routes in-process
   (HAOS gives you no shell inside the container, so this is the self-test):

   ```
   wettergraph: PASS  /health returns 200 ok  (200 'ok')
   wettergraph: PASS  / serves an HTML page  (200 text/html; charset=utf-8)
   wettergraph: PASS  page lists every option  (5 rows for 5 options)
   wettergraph: PASS  option values reach the page  (latitude=48.1746)
   wettergraph: PASS  /image/graph serves an SVG  (200 image/svg+xml; charset=utf-8 803B)
   wettergraph: PASS  unknown paths 404  (404)
   wettergraph: PASS  options file is readable  (/data/options.json)
   wettergraph: startup check 7/7 passed
   ```

   `present=False`, or `options file is readable` showing FAIL, means options
   never reached the container - report that, it is the interesting failure.
   The same check can be re-run from the HA terminal with
   `docker exec $(docker ps -q -f name=wettergraph | head -1) python3 /app/server.py --self-test`.
5. Open the **Wettergraph** panel in the sidebar (or the "Open web UI" button).
   You should see the status page with a table of the options.
6. Change `page_note` under **Configuration**, save, then reload the page.
   The new value must appear **without** restarting the app. Use this to prove
   options are re-read live before the real rendering lands.

Fallback if the sidebar panel does not appear: the app is still installed and
running, and `/health` on port 8099 is what the watchdog uses. Say so instead of
fighting ingress - ingress is not on the critical path.

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
| `update_interval` | `15` | Minutes between refreshes, 5-180. Not yet driving anything. |

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

`tools/addon-lint.py` re-runs Supervisor's own store scan (glob `**/config.*`
outside dot-dirs and `rootfs`, validate against the same voluptuous schema) so a
misnamed or malformed config is caught before you install anything.
