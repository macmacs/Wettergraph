# Resolver session: Add-on packaging and install skeleton

Status: implementation done, awaiting the operator's install report.
Claim: `Status: claimed`, 2026-09-20.

## What is on `main` now

| Path | What it is |
| --- | --- |
| `repository.yaml` | Makes the repo addable: Settings -> Add-ons -> Repositories -> `https://github.com/macmacs/Wettergraph`. |
| `wettergraph/config.yaml` | The app: slug `wettergraph`, version `0.1.0`, arch `aarch64` + `amd64`, port `8099`, ingress on 8099, watchdog on `/health`, 5 options with a schema. |
| `wettergraph/Dockerfile` | `FROM ghcr.io/home-assistant/base:3.24-2026.08.0`, plus `python3 curl tzdata ca-certificates uv` from Alpine 3.24, then `COPY app/ /app/`. |
| `wettergraph/app/server.py` | Stdlib HTTP server: `/` status page, `/health`, `/image/graph` placeholder SVG, 404 otherwise. Redisplays options free of charge (read per request). |
| `wettergraph/app/pyproject.toml` | Declares `resvg-py==0.5.0` for the renderer ticket. Not imported yet. |
| `wettergraph/README.md` | The install steps and the start-here report. |
| `tools/addon-lint.py` | Re-runs Supervisor's own store scan locally (see below). |

## Verification evidence

Mechanical, run on this box:

- `uv run --with pyyaml --with voluptuous python tools/addon-lint.py` -> `add-on repository looks loadable.`
- `python3 wettergraph/app/server.py --self-test` -> 7/7 with a realistic options file; with an **unreadable** options file it correctly drops to 4/6 and exits 1.
- Route check by hand: `/health` 200 `ok`; `/` 200 HTML with one row per option; `/image/graph` 200 `image/svg+xml`, 803 B, `<svg width="782"`; `/nope` 404. Editing the options file then re-fetching changed the page with no restart.

Not verified, and deliberately so: **nothing was built or run as a container.** This box has Docker but no usable daemon (it lacks `CAP_SYS_ADMIN`, so `unshare` fails), so no `docker build` and no Supervisor could run here.

## Two findings worth keeping

- **`io.hass.base.image: alpine:3.24` is misleading.** The HA base image's apk repositories point at *Alpine 3.24* while the underlying Alpine image was 3.23, so `apk add` resolves newer packages than the tag suggests. 3.24 has all four packages; 3.23 does not have `uv`. Hence the explicit `3.24-2026.08.0` pin.
- **A repo-wide filename collision.** Supervisor finds apps by globbing `**/config.*`, skipping only dot-directories and `rootfs`. `fdroid/config.yml` (this repo's F-Droid repository config) therefore read as a malformed app and was skipped with a warning. Renamed to `fdroid/fdroid-config.yml`; `.github/workflows/fdroid.yml` updated. Any future `.yaml`/`.yml`/`.json` file literally named `config` must live under a dot-directory or `rootfs`.

## Operator checklist

1. Settings -> Add-ons -> Add-on Store -> three-dot menu -> **Repositories** -> add `https://github.com/macmacs/Wettergraph`.
2. Install **Wettergraph**, start it, open **Log**.
3. Report: the first line (`starting on :8099 ... present=True/False`) and the full `startup check N/N passed` block.
4. Open the sidebar panel (or "Open web UI"). Report whether the options table appears.
5. Change `page_note` in Configuration, save, reload the page. Report whether the new value appears without a restart.
6. Report anything that looks wrong or absent, plus the HAOS version.

If the panel does not appear, say so - ingress is a nicety, the port and the watchdog are the critical path. If the port is not reachable from where curl runs, say so too; that is what the delivery ticket will need to know.
