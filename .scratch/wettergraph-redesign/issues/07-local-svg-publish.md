# Publish the graph as an SVG Home Assistant can serve

Type: task
Status: resolved
Blocked by: -

## Question

[Ticket 00](00-svg-delivery-probe.md) proved that port 8099 cannot be used by a browser-loaded card: the dashboard is HTTPS, the port is HTTP, and the image is blocked as mixed content. Ingress renders the same SVG correctly but its path carries a per-session token that rotates, so it cannot be a card's `url`.

How does the add-on put the SVG on the HA origin at a stable path?

The intended shape is `https://<ha>/local/wettergraph.svg`, i.e. the add-on writing into Home Assistant's `www` folder the way `publish.py` already writes `/share/wettergraph/graph.png`.

## What this has to settle

- **The mapping.** `config.yaml` maps `share:rw` only, and inside an app container `/config` is the app's own folder, not HA's - the existing comment says so. Which mapping exposes HA's config dir on this base image (`homeassistant_config:rw` and its mount path), and does adding it force a reinstall rather than an update?
- **The writer.** `publish.py` extended to a second artifact, or a second Publisher instance? Same change-driven rule: render, compare, write only on difference, atomic rename. The age chip stays off the file copy, for the same reason it is off the PNG copy.
- **Caching.** HA serves `/local/` static files with cache headers. Does `custom:refreshable-picture-card` cache-bust on its own (it re-fetches every `refresh_interval`), or does the card need a `?v=` the publisher changes? A stale graph that never visibly updates is the failure to avoid.
- **What happens to the PNG paths.** The Generic Camera and `/share/wettergraph/graph.png` stay (map: *Out of scope*, delivery mechanics unchanged) - but the dashboard card the operator actually looks at becomes the `/local/` SVG. Say so explicitly so ticket 06 ships the right card.

## Done when

- The add-on writes the SVG where HA serves it, and the operator has a card pointing at a URL that does not rotate.
- The refresh behaviour is confirmed: the graph on the dashboard visibly follows the data, not a cached copy.

## Answer must record

The mapping used, the path written, the card YAML that works, and the cache-busting verdict.

## Answer

**Shipped as 0.4.0.** The add-on writes both themes into Home Assistant's own
`www` folder; HA serves them at `/local/`, same origin, no rotating token.

### The mapping

`map: - homeassistant_config:rw`. **Mount point is `/homeassistant`, not
`/config`**: Supervisor mounts every map type at `/<type-name>`, and inside an
app container `/config` is the app's own public config folder. There is no
www-only mapping, so this grants rw on HA's whole config dir (`secrets.yaml`,
`.storage` included) - accepted deliberately; the app only ever writes two
files. `tools/addon-lint.py` runs Supervisor's own voluptuous schema and
accepts the key (`Wettergraph v0.4.0`), so it is valid, not merely documented.

**Update, not reinstall.** `config.yaml` is read live by Supervisor and the
container is recreated on update, so the mapping arrives with a normal store
update. If it somehow does not, the check below names it and reinstalling is
the fallback.

**The failure that looks like success, and the guard against it.** Without the
mapping, `mkdir(parents=True)` would cheerfully create `/homeassistant/www/...`
*inside the container*, write there, and report every check green while HA
served nothing. `Publisher` now takes a `mount` - the directory Supervisor
bind-mounts - and refuses to write when it is absent. Verified: pointed at an
absent mount, the app logs `... is not mapped into this app`, writes nothing,
and both startup checks FAIL.

### The path written

    /homeassistant/www/wettergraph/graph-light.svg  ->  /local/wettergraph/graph-light.svg
    /homeassistant/www/wettergraph/graph-dark.svg   ->  /local/wettergraph/graph-dark.svg

Subdir mirrors `/share/wettergraph/graph.png`. **Both themes always**, ignoring
`image_theme`, so the card can switch on `sun.sun` the way the operator's yr
card already does; `image_width` still applies, as the SVG's intrinsic size.

### The writer

One mechanism, three destinations. `Publisher` took a `root`, `subdir`,
`filename`, `label` and `mount`; `publish.run_forever` moved out of the class
to a module function driving `(publisher, render)` pairs, so one thread keeps
the PNG and both SVGs on one cadence and a broken render on one never stalls
the others. Same change-driven rule as the PNG: render every 60 s, compare,
write only on difference, write-beside-and-rename. **No age chip on the file
copies** - it moves every minute and would rewrite the files every minute.

Verified in-process with `WG_SHARE` / `WG_WWW` pointed at fake mounts: first
run writes all three, a second run writes **zero** (`www light wrote` count 0),
startup check 18/19 - the one FAIL is the dev box's missing DejaVu, which is a
known property of this environment, not a regression. `render-check.py` 57/57:
the renderer is untouched.

### Caching: no `?v=` needed

HA serves `/local/` with `Cache-Control: public, max-age=2678400` - **31 days**.
That would be fatal on its own. But `custom:refreshable-picture-card` builds
its URL through `_getTimestampedUrl`, appending `?currentTimeCache=<ms>` (or
`&`) on every refresh, so each poll is a fresh fetch and the publisher needs no
version query of its own. Read off the card's `dist/refreshable-picture-card.js`,
not the README, which says nothing about it.

**The other `/local/` trap:** HA registers the `/local/` static path *at
startup*. On an install where `www` did not exist, the files 404 until HA is
restarted once. The app logs `NOTE created ... restart Home Assistant once` when
it creates the folder.

### What happens to the PNG paths

Both stay, both demoted to camera routes: the Generic Camera on port 8099 (HA
fetches it server-side, so mixed content never applies) and the
`/share/wettergraph/graph.png` Local file fallback. **The card the operator
looks at is the `/local/` SVG** - that is what ticket 06 ships. Whether the two
PNG routes are still worth their keep is the map's fog, not this ticket's.

### Operator checklist (HITL)

Install **0.4.0**; the log should read `build=0.4.0`.

1. Settings -> Add-ons -> Wettergraph -> **Update**. (A normal update; the new
   mapping rides along with the container recreation.)
2. **Log tab.** Expect:
   - `wettergraph: www target /homeassistant/www/wettergraph/graph-light.svg -> /local/wettergraph/graph-light.svg` (and the dark one)
   - `wettergraph: PASS  the light dashboard SVG is in step (...)`, same for dark
   - `startup check 19/19 passed`
   - If instead you see `WARNING /homeassistant is not mapped`: the mapping did
     not arrive. Uninstall and reinstall the app, then re-check.
   - If you see `NOTE created /homeassistant/www ... restart Home Assistant
     once`: do that before step 4, or the URLs 404.
3. **Sanity-check the URL** in a tab: `https://<ha>/local/wettergraph/graph-light.svg`.
4. **The card.** Replace the yr card (or add beside it):

   ```yaml
   type: custom:vertical-stack-in-card
   cards:
     - type: conditional
       conditions:
         - condition: state
           entity: sun.sun
           state: above_horizon
       card:
         type: custom:refreshable-picture-card
         refresh_interval: 600
         url: /local/wettergraph/graph-light.svg
         attribute: ''
         noMargin: true
         tap_action:
           action: more-info
         grid_options:
           rows: auto
           columns: 18
     - type: conditional
       conditions:
         - condition: state
           entity: sun.sun
           state: below_horizon
       card:
         type: custom:refreshable-picture-card
         refresh_interval: 600
         url: /local/wettergraph/graph-dark.svg
         attribute: ''
         noMargin: true
         tap_action:
           action: more-info
         grid_options:
           rows: auto
           columns: 18
   ```

5. **Report:** does the card show the graph; does it still show it **from the
   phone / outside the LAN** (the thing port 8099 could never do); and does the
   picture visibly follow the data rather than sticking - easiest read is the
   status page's `written N min ago` line against what the card shows after an
   hour.

Note this ships **today's** graph, not the redesign. That is deliberate: the
delivery plumbing is proved end-to-end now, so ticket 05's redraw only changes
pixels.
