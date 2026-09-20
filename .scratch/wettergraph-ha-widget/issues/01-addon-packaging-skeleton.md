# Add-on packaging and install skeleton

Type: task
Status: open

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

Operator adds the repo, installs the add-on, opens it, sees the placeholder.

## Refs

map.md "Verified facts" - add-on config keys, ingress, base image.
