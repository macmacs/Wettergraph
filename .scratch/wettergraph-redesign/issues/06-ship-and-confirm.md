# Ship the new look and confirm it on the dashboard

Type: task
Status: open
Blocked by: 05, 07

## Question

Get the redesigned graph onto the operator's HAOS and confirm it looks like the reference there - including whatever the 2:1 -> ~3.8:1 shape change does to the card.

## Done when

- `wettergraph/config.yaml` version is bumped (the app store only offers an update when it changes) and the startup check passes in the log.
- The operator is handed exact steps: update the app, reload, look at the panel and the dashboard card, and report back with a screenshot of each theme.
- The card is made to fit the new aspect: whatever the operator has to change (`columns` on the tile, `image_width` / `image_theme` defaults) is recorded here, not rediscovered later. The card is the `/local/` SVG pair settled in [ticket 07](07-local-svg-publish.md) - `custom:refreshable-picture-card` on `/local/wettergraph/graph-{light,dark}.svg` in a `sun.sun` conditional - not a camera.
- The operator confirms: the graph matches the reference, it still refreshes on its own, and it is legible **on the phone** (ticket 00's verdict was desktop-only).

## Constraints

- Nothing in the agent's environment can run HA or a container. Every verification step is the operator's, and a step they cannot perform is a defect in this ticket.
- Do not change delivery mechanics beyond what the shape change forces.

## Answer must record

The shipped version, the operator's confirmation, and the final card configuration.

## Answer
