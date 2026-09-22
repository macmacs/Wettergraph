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

## Refs

map.md "Verified facts" - endpoint behaviour, units, expiry headers.
