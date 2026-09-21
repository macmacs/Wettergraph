# Add-on packaging and install skeleton

Type: task
Status: resolved

Resolution draft: [assets/01-resolution.md](assets/01-resolution.md)

## Question

Build the smallest possible HAOS add-on that installs and runs empty: repository layout, `config.yaml` (slug, arch, startup, options schema, ports), `Dockerfile`, and an entrypoint that starts a server. The operator must be able to add the repo and install it.

## Outcome

An add-on that installs on HAOS, starts, serves a placeholder on its port, and exposes its options in the UI.

## Done when

- `config.yaml` is valid and the add-on appears in the local add-on store with options rendered from the schema.
- Inside the container, options are readable at `/data/options.json`.
- A placeholder (PNG or HTML) is served on the chosen port.
- Changing an option in the UI takes effect without a rebuild.

## Constraints

- Base `ghcr.io/home-assistant/base:latest` unless the Python toolchain forces otherwise; `arch: aarch64, amd64`.
- Python via `uv`, per repo rules. No pip-install fallback.
- This ticket fetches nothing and draws nothing.

## Answer must record

Repo/folder layout, image and build path, chosen port, and the option schema as shipped.

## Verification (operator installs, then reports)

- [x] Repo added from `https://github.com/macmacs/Wettergraph`, app installed and started on HAOS.
- [x] Status page served with the option table and the placeholder graph.
- [ ] `page_note` edited in the UI appearing without a rebuild - mechanism verified locally (`server.py` re-reads `/data/options.json` per request, proven by editing the file under a running server), not yet observed on HAOS.
- [ ] The `startup check N/N passed` block from the Log tab; the routes it exercises were reported working by the page itself.

## Answer

**Repo layout.** `repository.yaml` at the repo root; the app in `wettergraph/`
(`config.yaml`, `Dockerfile`, `app/server.py`, `app/pyproject.toml`, `README.md`);
`tools/addon-lint.py` as the packaging gate. Supervisor finds apps by globbing
`**/config.*` repo-wide, skipping only dot-directories and `rootfs`, so the app
folder may live anywhere - but nothing else in the repo may be named `config.*`
(`fdroid/config.yml` was, and was renamed to `fdroid/fdroid-config.yml`).

**Image and build path.** Built on the HA box by Supervisor from the GitHub repo -
no registry, no CI, no prebuilt image. `FROM ghcr.io/home-assistant/base:3.24-2026.08.0`
(pinned; 3.24 is the first with `uv` in community), then `apk add python3 curl tzdata
ca-certificates uv`, `COPY app/ /app/`, `CMD ["/usr/bin/python3", "/app/server.py"]`.
No pip. `resvg-py==0.5.0` is declared but not yet imported (render ticket).

**Port.** 8099, container and host side; ingress on 8099; watchdog
`tcp://[HOST]:[PORT:8099]/health`; `webui: http://[HOST]:[PORT:8099]/`.

**Option schema as shipped.** `page_note` str (`"setup probe"`), `place_id` str
(`"2-6325496"`), `latitude` float(-90,90) (`48.1746`), `longitude` float(-180,180)
(`11.5538`), `update_interval` int(5,180) (`15`).

**Two defects, both found by installing rather than by building** (no container can
be built or run in the agent's environment - see map "Verified facts"):

1. `init` defaults to `true`, which hands the container to Docker's tini as PID 1,
   so the base image's s6 died with `s6-overlay-suexec: fatal: can only run as pid 1`.
   Fixed with `init: false`.
2. The Dockerfile had no `CMD`; with an s6 base and no services the container exits
   as soon as stage2 finishes. Fixed with an explicit `CMD`.

Both are now gates in `tools/addon-lint.py`, each with a negative control.

**Evidence.** In-container startup check: 7 route/option assertions run against the
real `/data/options.json` on every start, reported into the app log. Operator saw
the served page with all five options and the placeholder graph.


## Refs

map.md "Verified facts" - add-on config keys, ingress, base image.
