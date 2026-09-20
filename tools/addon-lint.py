#!/usr/bin/env python3
"""Local stand-in for what HA Supervisor does to an add-on repo: run the same
store scan (glob for config.* outside dot-dirs/rootfs, validate every hit with
Supervisor's own voluptuous schema) so a wrong filename or an invalid key is
caught before the operator ever installs anything.

Usage: python3 tools/addon-lint.py [repo-root]
Exit code is non-zero if the repo would not load as a valid app repository.
"""

import glob
import os
import re
import sys

try:
    import voluptuous as vol
except ImportError:  # pragma: no cover
    sys.exit("voluptuous is required: uv run --with voluptuous python tools/addon-lint.py")

# Supervisor's file suffixes for app configuration (supervisor/const.py)
FILE_SUFFIX_CONFIGURATION = [".yaml", ".yml", ".json"]
# Supervisor's slug field regex (supervisor/apps/const.py: RE_SLUG)
RE_SLUG = re.compile(r"^[-_.A-Za-z0-9]+$")
# supervisor/apps/validate.py: SCHEMA_REPOSITORY_CONFIG
SCHEMA_REPOSITORY_CONFIG = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("url"): str,
        vol.Required("maintainer"): str,
        vol.Optional("report_issues"): str,
    },
    extra=vol.REMOVE_EXTRA,
)
# The keys Supervisor's _SCHEMA_APP_CONFIG requires (supervisor/apps/validate.py)
REQUIRED_APP_KEYS = ("name", "version", "slug", "description", "arch")
BUILD_SUFFIXES = (".yaml", ".yml", ".json")


def _load(path):
    if path.endswith(".json"):
        import json

        with open(path) as fh:
            return json.load(fh)
    try:
        import yaml
    except ImportError:  # pragma: no cover
        sys.exit("pyyaml is required: uv run --with pyyaml --with voluptuous python tools/addon-lint.py")
    with open(path) as fh:
        return yaml.safe_load(fh)


def find_app_configs(root):
    found = []
    for path in glob.glob(os.path.join(root, "**", "config.*"), recursive=True):
        parts = os.path.relpath(path, root).split(os.sep)
        if any(p.startswith(".") or p == "rootfs" for p in parts):
            continue
        if os.path.splitext(path)[1] in FILE_SUFFIX_CONFIGURATION:
            found.append(path)
    return found


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    errors, notes = [], []

    # A file literally named config.yml would also be picked up by the Home
    # Assistant app store as an app config, so this one carries a prefixed name.
    repo_file = None
    for cand in ("repository.yaml", "repository.yml", "repository.json"):
        if os.path.exists(os.path.join(root, cand)):
            repo_file = os.path.join(root, cand)
            break
    if repo_file is None:
        errors.append("no repository.yaml/.yml/.json at repo root: HA cannot add this repo")
    else:
        try:
            SCHEMA_REPOSITORY_CONFIG(_load(repo_file))
            notes.append(f"{os.path.basename(repo_file)}: valid repository config")
        except Exception as exc:
            errors.append(f"{repo_file}: repository config invalid: {exc}")

    configs = find_app_configs(root)
    if not configs:
        errors.append("no config.* found: HA would load the repo but show no app")
    for path in configs:
        rel = os.path.relpath(path, root)
        if os.path.splitext(path)[1] not in BUILD_SUFFIXES:  # pragma: no cover
            continue
        try:
            cfg = _load(path)
        except Exception as exc:
            errors.append(f"{rel}: unreadable: {exc}")
            continue
        app_errors = []
        missing = [k for k in REQUIRED_APP_KEYS if k not in cfg]
        if missing:
            errors.append(f"{rel}: missing required keys {missing}")
            continue
        if not RE_SLUG.match(str(cfg["slug"])):
            app_errors.append(f"{rel}: slug {cfg['slug']!r} violates RE_SLUG ^[-_.A-Za-z0-9]+$")
        if not isinstance(cfg["arch"], list) or any(a not in ("aarch64", "amd64") for a in cfg["arch"]):
            app_errors.append(f"{rel}: arch must be a list drawn from aarch64/amd64, got {cfg['arch']!r}")
        for key in ("ports", "ports_description"):
            if key in cfg and not isinstance(cfg[key], dict):
                app_errors.append(f"{rel}: {key} must be a mapping, got {type(cfg[key]).__name__}")
        if "ingress" in cfg and not isinstance(cfg["ingress"], bool):
            app_errors.append(f"{rel}: ingress must be a bool")
        if "ingress_port" in cfg and not isinstance(cfg["ingress_port"], int):
            app_errors.append(f"{rel}: ingress_port must be an int")
        if not os.path.exists(os.path.join(os.path.dirname(path), "Dockerfile")) and "image" not in cfg:
            app_errors.append(f"{rel}: no Dockerfile next to it and no 'image' key: HA would have nothing to build")
        errors.extend(app_errors)
        if not app_errors:
            notes.append(f"{rel}: {cfg['name']} v{cfg['version']} slug={cfg['slug']} arch={cfg['arch']}")

    for note in notes:
        print(f"ok   {note}")
    for err in errors:
        print(f"FAIL {err}")
    if errors:
        print(f"\n{len(errors)} problem(s): this repo would not load cleanly on HA.")
        return 1
    print("\nadd-on repository looks loadable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
