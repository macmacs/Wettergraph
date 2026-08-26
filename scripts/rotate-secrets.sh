#!/usr/bin/env bash
#
# rotate-secrets.sh - rotate the API credentials inherited from the upstream
# AF-Weather-Widget repo.
#
# The upstream values (met.no user agent "AF@gitsaibot.net" and GeoNames
# username "af_weather") are baked into git history, so every fork must
# replace them. This script:
#
#   1. rotates the met.no User-Agent in key.properties
#   2. rotates the GeoNames username in key.properties
#   3. updates the matching GitHub repository secrets used by
#      .github/workflows/fdroid.yml (AF_USER_AGENT, AF_USER_GEONAMES)
#
# Usage:
#   scripts/rotate-secrets.sh [--user-agent VALUE] [--geonames-user VALUE]
#                             [--contact EMAIL_OR_URL] [--dry-run] [--yes]
#
# If --user-agent is omitted, a fresh unique value is generated from a random
# token plus the contact (default contact: this repo's GitHub URL).
# If --geonames-user is omitted, you are prompted for it. The username must be
# an existing geonames.org account; this script does not create one.
#
# The met.no API host (apiKey=api.met.no) is not a secret and is left alone.

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
case "$SCRIPT_PATH" in /*) ;; *) SCRIPT_PATH="$(pwd)/$SCRIPT_PATH" ;; esac
ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
KEY_PROPERTIES="$ROOT/key.properties"

DRY_RUN=0
YES=0
USER_AGENT=""
GEONAMES_USER=""
CONTACT="https://github.com/macmacs/AF-Weather-Widget"

usage() {
    sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --user-agent)     USER_AGENT="$2"; shift 2 ;;
        --geonames-user)  GEONAMES_USER="$2"; shift 2 ;;
        --contact)        CONTACT="$2"; shift 2 ;;
        --dry-run)        DRY_RUN=1; shift ;;
        --yes|-y)         YES=1; shift ;;
        -h|--help)        usage 0 ;;
        *) echo "Unknown option: $1" >&2; usage 1 ;;
    esac
done

random_token() {
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex 6
    else
        od -An -N6 -tx1 /dev/urandom | tr -d ' \n'
    fi
}

get_key() { # get_key <name>  -> value from key.properties ("" if absent)
    [ -f "$KEY_PROPERTIES" ] && sed -n "s/^$1=//p" "$KEY_PROPERTIES" | tail -1 || true
}

OLD_USER_AGENT="$(get_key user_agent)"
OLD_GEONAMES="$(get_key user_geonames)"

if [ -z "$USER_AGENT" ]; then
    USER_AGENT="af-weather-widget-fork-$(random_token) ($CONTACT)"
fi
if [ -z "$CONTACT" ] && [ -z "${USER_AGENT##*()}" ]; then
    echo "error: empty contact" >&2; exit 1
fi

if [ -z "$GEONAMES_USER" ]; then
    read -r -p "GeoNames username (must be an existing geonames.org account): " GEONAMES_USER
fi
if ! printf '%s' "$GEONAMES_USER" | grep -Eq '^[A-Za-z0-9_]{2,40}$'; then
    echo "error: GeoNames username must be 2-40 chars of letters, digits or _" >&2
    exit 1
fi

echo "Current: user_agent     = ${OLD_USER_AGENT:-<unset>}"
echo "         user_geonames  = ${OLD_GEONAMES:-<unset>}"
echo "New:     user_agent     = $USER_AGENT"
echo "         user_geonames  = $GEONAMES_USER"
echo

if [ "$DRY_RUN" = 1 ]; then
    echo "dry run: no files written, no secrets set."
    exit 0
fi

if [ "$YES" != 1 ]; then
    read -r -p "Write key.properties and set GitHub secrets? [y/N] " reply
    case "$reply" in [yY]*) ;; *) echo "aborted."; exit 1 ;; esac
fi

# 1. Update the local, gitignored key.properties.
if [ -f "$KEY_PROPERTIES" ]; then
    cp -p "$KEY_PROPERTIES" "$KEY_PROPERTIES.bak"
    echo "Backed up old values to $KEY_PROPERTIES.bak (delete it once verified)."
else
    if [ -f "$ROOT/key.properties.example" ]; then
        cp "$ROOT/key.properties.example" "$KEY_PROPERTIES"
    else
        : > "$KEY_PROPERTIES"
    fi
fi
UA_ESC="${USER_AGENT//|/\\|}"
GEO_ESC="${GEONAMES_USER//|/\\|}"
sed -e "s|^user_agent=.*|user_agent=$UA_ESC|" \
    -e "s|^user_geonames=.*|user_geonames=$GEO_ESC|" \
    "$KEY_PROPERTIES" > "$KEY_PROPERTIES.tmp" && mv "$KEY_PROPERTIES.tmp" "$KEY_PROPERTIES"
if ! grep -q '^user_agent=' "$KEY_PROPERTIES"; then echo "user_agent=$USER_AGENT" >> "$KEY_PROPERTIES"; fi
if ! grep -q '^user_geonames=' "$KEY_PROPERTIES"; then echo "user_geonames=$GEONAMES_USER" >> "$KEY_PROPERTIES"; fi

# 2. Update the GitHub repository secrets used by the workflow.
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    gh secret set AF_USER_AGENT --body "$USER_AGENT"
    gh secret set AF_USER_GEONAMES --body "$GEONAMES_USER"
else
    echo "warning: gh CLI not available or not authenticated; skipping GitHub secrets."
    echo "         Set them manually: AF_USER_AGENT, AF_USER_GEONAMES"
fi

echo
echo "Done. Reminders:"
echo "  - GeoNames username '$GEONAMES_USER' must be a real account on geonames.org."
echo "  - Other worktrees/clones keep their own untracked key.properties; update them too."
echo "  - Old values still exist in git history; rotation invalidates them for API use."
