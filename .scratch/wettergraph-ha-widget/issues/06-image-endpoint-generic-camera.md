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

## Verification (operator installs, then reports)

Operator adds the camera config, restarts, sees the graph on the dashboard, and confirms it is still current after the cadence has passed.
