# Auto-updating image endpoint and generic camera

Type: task
Status: claimed
Blocked by: 05

## Question

Make the graph land on the dashboard and keep itself current: the add-on serves the PNG over its own reachable port, and HA's built-in **generic camera** polls it, so the card refreshes on its own.

## Done when

- Built-in generic camera (no HACS) is configured with the add-on's URL, `frame_interval` set from the add-on's `update_interval`, and it works.
- The served PNG is what the dashboard shows - verified by the operator seeing a fresh render at the expected cadence.
- Options decide the refresh cadence and the served dimensions, and a change takes effect without rebuilding the image. The URL carries `width` and `theme=light|dark`, clamped as `assets/graph-spec.md` §1.2 and §2.2 say, so a dashboard can pick its own variant without touching the app config.
- A documented fallback exists for the case where the HA instance cannot reach the add-on's port, and has been tried at least once.
- Cache-busting is correct: the card never shows a stale frame after an update.

## Constraints

- Prefer the built-in generic camera over a custom card, to keep HACS off the critical path.
- If the add-on serves over its own port, that port must be reachable from the HA instance, not only from a browser.
- `ingress` may additionally be enabled so the add-on has a clickable UI, but ingress must not be on the critical path - the camera polls the port, not the ingress path.

## Refs

- `assets/graph-spec.md` §1 (width, clamp) and §2 (theme param): the two knobs the
  served URL has to understand.

## Escalate rather than guess

If the documented fallback turns out to be the only workable path, stop and surface this to the operator: it changes both the install steps and the architecture. Do not silently switch delivery route.

## Answer must record

The working camera config block, the URL shape, the agreed cadence, and which fallback was tried and its result.

## Answer

**The camera config that works** (built-in Generic Camera, no HACS; the
integration is config-flow only now - the old YAML `camera: platform: generic`
platform does not exist any more, so the dialog is the only way in):

| Field | Value |
| --- | --- |
| Still Image URL | `http://<ha-host>:8099/image/graph?width=782&theme=light` |
| Stream Source | empty |
| Username / Password | empty |
| Advanced | defaults (Frame rate 2, Verify SSL true, Limit refetch off) |

`<ha-host>` is the address the operator uses for Home Assistant. The app's
status page prints the exact URL to paste when it is opened on port 8099, and a
`<HA-host>` template when it is opened through ingress (behind ingress the app
cannot see the address the camera has to dial). The dialog fetches the URL and
previews the image, so a wrong host or port fails during setup.

**URL shape.** `/image/graph` (alias `/image/graph.png`) plus, all optional:
`?width=480..1564` (clamped, not refused - graph-spec §1.2), `?theme=light|dark`
(unknown falls back to light - §2.2), `&age=1` (the freshness probe below).
Without `width`/`theme` the app's own options decide. The response is
`image/png` with `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`,
`Pragma: no-cache`, and `X-Wettergraph-Age` (seconds since the last successful
met.no fetch) for `curl`.

**`frame_interval` no longer exists in this integration.** The ticket assumed it
did. In core's `components/generic/`: `const.py` has `CONF_FRAMERATE` (UI: *Frame
rate*, default 2) and its only use in `camera.py` is
`self._attr_frame_interval = 1 / framerate`, checked as
`self._last_update + self._attr_frame_interval > time.time()` - a **floor on
re-fetching the same URL**, not a schedule. So there is nothing to copy
`update_interval` into, and no `frame_interval` to set from it.

**The agreed cadence, as two numbers.**

- *Data*: met.no's `Expires` (observed ~32 min), with `update_interval` as the
  floor, so the picture changes every ~30-60 min.
- *Pickup*: about 5 minutes, by Home Assistant itself. `Camera.async_update_token`
  runs on `TOKEN_CHANGE_INTERVAL` (5 min), which rotates the access token, then
  calls `async_write_ha_state()`; `entity_picture` is
  `/api/camera_proxy/camera.<name>?token=<token>` with the new token, so the
  dashboard asks for a new URL and a fresh frame. Nothing in the path caches -
  the integration adds no cache headers, and the app's own are no-store.

**The freshness probe** (`&age=1`): draws graph-spec §8.2's chip on *fresh* data
with minutes under an hour (`vor 4 min`). It is the only pixel on the image that
moves on its own, so a dashboard proves by itself that it re-reads the image.
Off by default: §9.4 keeps the clock off the image otherwise, and
`tools/render-check.py` still passes 57/57 with the switch unused.

**Options decide the served image.** Two new ones, both live (read fresh on
every request, no rebuild): `image_width` (default 782, `int(480,1564)`) and
`image_theme` (default `light`, `list(light|dark)`). They are the *defaults* for
`/image/graph` with no query, for the status page's own image and for the
`/share` copy; a dashboard URL still overrides both per request.

**The fallback, and why it is `/share`.** The app now writes the same PNG
(change-driven, atomic rename, options applied) to
`/share/wettergraph/graph.png`, and the fallback camera is the built-in **Local
file** camera pointed at that path - HA core reads the file, so no port, no
HTTP, nothing to reach. Allowed by `map: - share:rw` in `config.yaml`. `/config
/www` is **not** usable: inside an app container `/config` is the app's own
public config folder, not Home Assistant's (app configuration docs), so the
shared folder is the only one both sides see. Renders are byte-identical for the
same input, so "write only on change" is a real comparison: one render a minute,
no disk writes on a quiet hour. Tried on this box: first write, second call a
no-op, changed bytes rewritten, no leftover `.tmp`, and an unwritable path
reports once instead of every cycle.

**Evidence on this box.**

- `server.py --self-test` -> **17/17** (was 13), including the option-driven
  width, the no-store headers, the `?age=1` chip and the `/share` copy being in
  step with what is served.
- Option junk is clamped, not fatal: `image_width: "abc"` -> 782,
  `image_theme: navy` -> light; `?width=480` still beats an option of 1044.
- `tools/render-check.py` -> 57/57; `tools/addon-lint.py` -> loadable, v0.3.0,
  now also checking `map` entries and `options`/`schema` parity.
- Live probes: header dump, the age chip in the live SVG, the exact URL printed
  on a direct visit and the template behind an ingress-shaped Host.

**Escalation not needed**: the port route works and stays the primary; the file
route is additive.

## Verification (operator installs, then reports)

Operator adds the camera config, restarts, sees the graph on the dashboard, and confirms it is still current after the cadence has passed.

- [x] Local: self-test 17/17, render-check 57/57, addon-lint, the publisher's
  write/no-write/atomic behaviour, junk options clamped, `?age=1` chip.
- [ ] The store offers **0.3.0**; after the update the log shows
  `share target /share/wettergraph/graph.png`, `share wrote ...`, and
  `startup check 17/17 passed`.
- [ ] Generic Camera added with the URL above: the preview shows the graph, and
  the card on the dashboard shows it.
- [ ] The dialog has **no `frame_interval`** field (confirming the answer's
  cadence finding), and *Frame rate* is left at its default.
- [ ] It refreshes with nobody touching it: with `&age=1` in the URL the chip's
  minutes move within ~10 minutes, and the log shows a GET from HA's IP about
  every 5 minutes.
- [ ] The fallback was **tried once**: a Local file camera with
  `/share/wettergraph/graph.png` shows the same graph.
