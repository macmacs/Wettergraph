# met.no client and forecast cache

Type: task
Status: claimed

## Question

Build the add-on's data side: fetch `locationforecast/2.0/compact` for the configured place with a proper `User-Agent`, honour `Expires` and `If-Modified-Since`, cache the last good JSON, expose a normalised series (time, temperature, precipitation, symbol_code) for the renderer, and degrade honestly when the network is down.

## Done when

- Configuration carries place id plus lat/lon at 4 decimals (met.no caches on ~4 decimals); default `2-6325496` / `48.1746` / `11.5538`.
- Polling respects `Expires`; a repeat request sends `If-Modified-Since` and tolerates `304`.
- Cached JSON survives a restart; a failed fetch still renders last-good data with the age chip `assets/graph-spec.md` §8.2 defines (no clock times on the image, §4.6).
- `403` and `429` are recognised and logged as such (met.no's documented failure modes) and never crash-loop.
- The normalised series has a documented shape the renderer consumes: time, temperature, precipitation rate, `symbol_code`.
- The normalised series is Celsius throughout, and there is no unit conversion: `assets/graph-spec.md` §5.7 is Celsius only, so the renderer labels the axis `°C` unconditionally.

## Constraints

- Server-side only, inside the add-on container. No browser/CORS reliance.
- No API key: this endpoint is open. Send a descriptive `User-Agent` naming the instance.

## Answer must record

Module path, the series shape, cache location under `/data`, and the exact UA string used.

## Answer

**Module path.** `wettergraph/app/metno.py` - stdlib only (`urllib`), no new
dependency. `wettergraph/app/server.py` wires it in: one daemon thread
(`metno-poller`) runs `ForecastCache.run_forever`, and `ForecastCache.view()`
feeds the status page and the new `/forecast.json` endpoint. The renderer ticket
consumes that same view; nothing in the dashboard ever calls met.no.

**The series shape.** One entry per met.no timeseries entry:

```json
{"time": "2026-09-22T18:00:00Z", "temperature": 11.7,
 "precipitation": 0.0, "symbol_code": "clearsky_night"}
```

`temperature` is °C, `precipitation` is mm/h, both parsed from
`instant.details.air_temperature` and the finest hook the entry carries
(`next_1_hours` as is; `next_6_hours` / `next_12_hours` divided back to an hourly
rate; no hook at all gives `None`). `symbol_code` is met.no's own code. An entry
with no temperature is skipped. The live response has 88 entries; a 48 h / 49
sample window (`assets/graph-spec.md` §4.1) is fully covered, because the first
61 entries are hourly and only then does the series step to 6-hourly.

**Cache location.** `/data/forecast-cache.json`, schema 1: place, `fetched_at`,
`expires_at`, `last_modified`, `samples`. Atomic write (temp file + `os.replace`).
A restart restores it (`metno: restored 88 samples ...`) and no request goes out
while `Expires` holds. A place change in the options discards it and polls at once.

**Exact User-Agent.**
`Wettergraph/0.1.2 (Home Assistant app; +https://github.com/macmacs/Wettergraph)`,
built from `BUILD_VERSION` (fallback `0.1.2`). met.no's documented 403 is a
rejected User-Agent; no API key is used because the endpoint needs none.

**Polling.** `Expires` is respected: no request before it. Once it has passed,
the request carries `If-Modified-Since` (the stored `Last-Modified` verbatim), and
`304 Not Modified` is a success - `fetched_at` is refreshed and the new `Expires`
adopted, samples untouched. Live `Expires` was ~32 min.

**Degrading honestly.** A failed fetch keeps the last good series and records
`last_error` in the view. `view()["stale"]` is true once the last successful
fetch is over 6 h old (`assets/graph-spec.md` §8.1); with no cache at all the
samples are empty and `last_error` carries the text for the §8.3 rendering.

**`403` and `429`.** Raised as `MetnoForbidden` / `MetnoRateLimited` (the latter
keeps `Retry-After`), logged with the status in the message, and backed off 60 s
doubling to 30 min. The poll loop swallows every exception, so a crash-loop is
not possible; the app keeps serving whatever it has.

**Evidence on this box** (no container can be built here - see map "Verified
facts"):

- `python3 wettergraph/app/metno.py --cache-dir /tmp/wg --once` -> `metno: 200 OK,
  88 samples cached to .../forecast-cache.json`.
- A throwaway fake met.no server proved the rest deterministically: 200 stores and
  writes the cache; an immediate re-poll makes **no request** (`Expires`); after
  expiry the request carries the exact `If-Modified-Since` and a 304 is treated as
  success; 403 and 429 are named, and `Retry-After: 120` is honoured; a restart
  restores the cache and does not re-fetch; a place change drops the series; the
  unreachable case keeps 88 samples with `last_error` set.
- `python3 wettergraph/app/server.py --self-test` -> 9/9 (two new checks:
  `/forecast.json` shape, descriptive User-Agent).
- `uv run --with pyyaml --with voluptuous python tools/addon-lint.py` -> loadable,
  `v0.1.2`.

**Version.** `wettergraph/config.yaml` 0.1.1 -> 0.1.2 so the store offers the
update (the convention from the packaging ticket).

## Verification (operator installs, then reports)

Install step: Settings -> Add-ons -> Add-on Store -> refresh -> **Wettergraph**
0.1.2 -> Update (it restarts). Log tab, after the two `wettergraph: starting`
lines: the first `metno:` line, then the `startup check N/N` block. The panel
should show one `forecast data:` line.

- [x] Local: live fetch, fake-server suite, self-test, linter - all pass.
- [ ] `metno: 200 OK, N samples cached to /data/forecast-cache.json` in the log.
- [ ] `startup check 9/9 passed`, and `forecast data: N samples ... (fresh)` on the status page.

## Refs

map.md "Verified facts" - endpoint behaviour, units, expiry headers.
