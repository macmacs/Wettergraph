#!/usr/bin/env bash
#
# capture-screenshots.sh
#
# Regenerates the F-Droid screenshot set on an Android emulator, using the
# debug-only mock data hook (AfMockData). No real device and no network data
# source required. Intended to run in GitHub Actions (screenshots job of
# .github/workflows/fdroid.yml); local runs need KVM and are not supported.
#
# Usage:
#   scripts/capture-screenshots.sh                boot the emulator, capture, write PNGs
#   scripts/capture-screenshots.sh --no-boot      emulator is already running (CI)
#   scripts/capture-screenshots.sh --output DIR   write PNGs to DIR instead of fastlane/
#   scripts/capture-screenshots.sh --keep-apk     do not rebuild the debug APK
#
# Requirements: Android SDK (adb, emulator), an AVD named "wettergraph_pixel9"
# (provisioned by the CI workflow), python3, ./gradlew.

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
case "$SCRIPT_PATH" in /*) ;; *) SCRIPT_PATH="$(pwd)/$SCRIPT_PATH" ;; esac
ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"

AVD_NAME="${AVD_NAME:-wettergraph_pixel9}"
PACKAGE="io.github.macmacs.af.debug"
# Java namespace; component classes live here even though the debug
# applicationId carries the .debug suffix.
NS_PACKAGE="io.github.macmacs.af"
PREFS_FILE="${PACKAGE}_preferences.xml"
PREFS_DIR="/data/data/${PACKAGE}/shared_prefs"
FREEZE_TIME_MS="${FREEZE_TIME_MS:-1768464000000}" # 2026-01-15 09:00:00 CET
TIMEZONE="Europe/Berlin"
WIDGET_MARKER="wettergraph_widget"

NO_BOOT=0
KEEP_APK=0
OUT_DIR="${OUT_DIR:-$ROOT/fastlane/metadata/android/en-US/images/phoneScreenshots}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-boot) NO_BOOT=1 ;;
        --keep-apk) KEEP_APK=1 ;;
        --output) OUT_DIR="$2"; shift ;;
        --help) sed -n '2,20p' "$SCRIPT_PATH"; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
    shift
done

ANDROID_HOME="${ANDROID_HOME:-$HOME/Android}"
ADB="${ADB:-$ANDROID_HOME/platform-tools/adb}"
EMULATOR="${EMULATOR:-$ANDROID_HOME/emulator/emulator}"

if [[ ! -x "$ADB" ]] && ! command -v adb >/dev/null; then
    echo "adb not found. Set ANDROID_HOME or put adb on PATH." >&2
    exit 1
fi
ADB="$(command -v adb || true)"
[[ -z "$ADB" ]] && ADB="$ANDROID_HOME/platform-tools/adb"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

log() { echo "[capture] $*"; }

adb_shell() { "$ADB" shell "$@"; }

python_parse() {
    python3 - "$@" <<'PYEOF'
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1]
mode = sys.argv[2]

if mode == "center":
    b = sys.argv[3]
    x1, y1, x2, y2 = [int(v) for v in b.strip("[]").replace("][", ",").split(",")]
    print((x1 + x2) // 2, (y1 + y2) // 2)
    sys.exit(0)

tree = ET.parse(path)
nodes = tree.getroot().iter("node")

def attrs(n):
    return n.attrib

if mode == "text":
    want = sys.argv[3]
    for n in nodes:
        if n.attrib.get("text") == want:
            b = n.attrib.get("bounds", "")
            print(b)
            sys.exit(0)
    sys.exit(1)
elif mode == "desc":
    want = sys.argv[3]
    for n in nodes:
        if n.attrib.get("content-desc") == want:
            print(n.attrib.get("bounds", ""))
            sys.exit(0)
    sys.exit(1)
elif mode == "contains":
    want = sys.argv[3]
    attr = sys.argv[4]
    for n in nodes:
        if want in n.attrib.get(attr, ""):
            print(n.attrib.get("bounds", ""))
            sys.exit(0)
    sys.exit(1)
else:
    sys.exit(1)
PYEOF
}

dump_ui() {
    local out="$WORK_DIR/ui.xml"
    adb_shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1 || true
    "$ADB" exec-out cat /sdcard/ui.xml > "$out" 2>/dev/null || true
    if ! grep -q "hierarchy" "$out" 2>/dev/null; then
        return 1
    fi
    echo "$out"
}

wait_for_ui() {
    local timeout="${1:-60}"
    local deadline=$((SECONDS + timeout))
    local out=""
    while (( SECONDS < deadline )); do
        out="$(dump_ui)" || { sleep 2; continue; }
        break
    done
    echo "$out"
}

bounds_of_text() {
    local ui="$1" want="$2"
    python_parse "$ui" text "$want" 2>/dev/null
}

bounds_of_desc() {
    local ui="$1" want="$2"
    python_parse "$ui" desc "$want" 2>/dev/null
}

center_of_bounds() {
    python_parse /dev/null center "$1" 2>/dev/null
}

# "[x1,y1][x2,y2]" -> "x1 y1 x2 y2"
parse_bounds() {
    echo "$1" | sed 's/\]\[/ /; s/[][]//g; s/,/ /g'
}

tap_bounds() {
    local bounds="$1"
    local center
    center="$(center_of_bounds "$bounds")"
    [[ -z "$center" ]] && return 1
    adb_shell input tap $center
}

wait_for_text() {
    local want="$1" timeout="${2:-90}"
    local deadline=$((SECONDS + timeout))
    local ui bounds
    while (( SECONDS < deadline )); do
        ui="$(wait_for_ui 10)"
        [[ -z "$ui" ]] && continue
        bounds="$(bounds_of_text "$ui" "$want")" && { echo "$bounds"; return 0; }
        sleep 2
    done
    return 1
}

wait_for_desc() {
    local want="$1" timeout="${2:-120}"
    local deadline=$((SECONDS + timeout))
    local ui bounds
    while (( SECONDS < deadline )); do
        ui="$(wait_for_ui 10)"
        [[ -z "$ui" ]] && continue
        bounds="$(bounds_of_desc "$ui" "$want")" && { echo "$bounds"; return 0; }
        sleep 3
    done
    return 1
}

freeze_clock() {
    adb_shell cmd alarm set-timezone "$TIMEZONE" || true
    adb_shell "cmd alarm set-time $FREEZE_TIME_MS" || true
}

skip_setup_wizard() {
    adb_shell settings put global device_provisioned 1 || true
    adb_shell settings put secure user_setup_complete 1 || true
    adb_shell am force-stop com.google.android.setupwizard 2>/dev/null || true
}

dump_ui_debug() {
    local out
    out="$(dump_ui)" || { log "uiautomator dump failed" >&2; return 0; }
    log "current UI text/desc nodes:" >&2
    python3 - "$out" >&2 <<'PYEOF'
import sys
import xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
for n in tree.getroot().iter("node"):
    t = n.attrib.get("text", "")
    d = n.attrib.get("content-desc", "")
    if t or d:
        print(f"  text={t!r} desc={d!r}")
PYEOF
    log "recent logcat:" >&2
    adb_shell logcat -d -t 300 2>/dev/null \
        | grep -iE 'AfWidget|AppWidget|AndroidRuntime|FATAL|wettergraph|macmacs' \
        | tail -40 >&2 || true
}

write_prefs() {
    local theme="$1"
    local xml="$WORK_DIR/prefs.xml"

    {
        echo "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>"
        echo "<map>"
        echo "    <string name=\"global_mock_weather\">$theme</string>"
        case "$theme" in
            cold)
                echo '    <int name="backup_background_color_int" value="-15061430" />'
                echo '    <int name="backup_day_color_int" value="-5714704" />'
                echo '    <int name="backup_night_color_int" value="-15061430" />'
                ;;
            warm)
                echo '    <int name="backup_background_color_int" value="-11916262" />'
                echo '    <int name="backup_day_color_int" value="-993112" />'
                echo '    <int name="backup_night_color_int" value="-11916262" />'
                ;;
            black)
                echo '    <int name="backup_background_color_int" value="-16777216" />'
                echo '    <int name="backup_day_color_int" value="-16777216" />'
                echo '    <int name="backup_night_color_int" value="-16777216" />'
                ;;
            round)
                echo '    <int name="backup_background_color_int" value="-16777216" />'
                echo '    <int name="backup_day_color_int" value="-16777216" />'
                echo '    <int name="backup_night_color_int" value="-16777216" />'
                echo '    <string name="backup_border_rounding_string">18</string>'
                ;;
        esac
        echo "</map>"
    } > "$xml"

    adb_shell am force-stop "$PACKAGE"
    sleep 2
    adb_shell mkdir -p "$PREFS_DIR" || true
    "$ADB" push "$xml" "$PREFS_DIR/$PREFS_FILE" >/dev/null
    local owner
    owner="$(adb_shell stat -c '%u:%g' "/data/data/$PACKAGE" | tr -d '\r')"
    adb_shell chown "$owner" "$PREFS_DIR/$PREFS_FILE"
}

pin_widget() {
    adb_shell am start -n "$PACKAGE/$NS_PACKAGE.AfWidgetPinActivity" >/dev/null 2>&1 || true

    # The launcher may show an "Add to home screen" confirmation dialog,
    # or add the widget directly and open the configuration screen.
    local deadline=$((SECONDS + 40))
    local ui bounds
    while (( SECONDS < deadline )); do
        ui="$(wait_for_ui 5)"
        [[ -z "$ui" ]] && { sleep 2; continue; }
        bounds="$(python_parse "$ui" contains "Add to" "text" 2>/dev/null)" && {
            tap_bounds "$bounds"
            break
        }
        if python_parse "$ui" text "Add Widget" >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
}

# Long-press the widget, drag its right resize handle to the target width.
resize_widget() {
    local target_width="$1"
    local ui bounds center x y w cur_w

    bounds="$(wait_for_desc "$WIDGET_MARKER" 120)" || { log "widget not found for resize"; return 1; }
    center="$(center_of_bounds "$bounds")"
    x="${center% *}"; y="${center#* }"

    read -r x1 y1 x2 y2 <<< "$(parse_bounds "$bounds")"
    cur_w=$((x2 - x1))

    if (( cur_w >= target_width - 40 )); then
        return 0
    fi

    adb_shell input swipe "$x" "$y" "$x" "$y" 800
    sleep 3

    local drag_x=$((x2 - 12))
    local delta=$((target_width - cur_w + 40))
    adb_shell input swipe "$drag_x" "$y" $((drag_x + delta)) "$y" 600
    sleep 3
    adb_shell input keyevent KEYCODE_BACK
    sleep 2
}

remove_widget() {
    local ui bounds center x y

    bounds="$(wait_for_desc "$WIDGET_MARKER" 60)" || return 0
    center="$(center_of_bounds "$bounds")"
    x="${center% *}"; y="${center#* }"

    adb_shell input swipe "$x" "$y" "$x" "$y" 800
    sleep 3

    ui="$(wait_for_ui 10)"
    bounds="$(python_parse "$ui" contains "Remove" "text" 2>/dev/null)" || {
        adb_shell input keyevent KEYCODE_BACK
        return 0
    }
    tap_bounds "$bounds"
    sleep 2
    adb_shell input keyevent KEYCODE_BACK
}

capture_screen() {
    local png="$1"
    "$ADB" exec-out screencap -p > "$png"
}

crop_bounds() {
    local src="$1" bounds="$2" dst="$3"
    BOUNDS="$bounds" SRC="$src" DST="$dst" python3 - <<'PYEOF'
import os
from PIL import Image

b = os.environ["BOUNDS"].strip("[]").replace("][", ",")
x1, y1, x2, y2 = [int(v) for v in b.split(",")]
im = Image.open(os.environ["SRC"]).convert("RGBA")
im.crop((x1, y1, x2, y2)).save(os.environ["DST"])
PYEOF
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

command -v python3 >/dev/null || { echo "python3 required" >&2; exit 1; }
python3 -c "import PIL" 2>/dev/null || { echo "Pillow required: pip install Pillow" >&2; exit 1; }

if [[ "$NO_BOOT" -ne 1 ]]; then
    if ! adb_shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
        log "booting emulator $AVD_NAME..."
        "$EMULATOR" -avd "$AVD_NAME" -no-window -no-audio -no-boot-anim \
            -no-snapshot -gpu swiftshader_indirect > "$WORK_DIR/emulator.log" 2>&1 &
        EMULATOR_PID=$!
        trap 'kill $EMULATOR_PID 2>/dev/null; rm -rf "$WORK_DIR"' EXIT

        deadline=$((SECONDS + 1800))
        while (( SECONDS < deadline )); do
            if adb_shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
                break
            fi
            if ! kill -0 "$EMULATOR_PID" 2>/dev/null; then
                log "emulator process exited unexpectedly; last log lines:" >&2
                tail -40 "$WORK_DIR/emulator.log" >&2 || true
                "$ADB" devices >&2 || true
                exit 1
            fi
            sleep 10
        done
        if ! adb_shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
            log "emulator did not boot in time; last log lines:" >&2
            tail -40 "$WORK_DIR/emulator.log" >&2 || true
            "$ADB" devices >&2 || true
            exit 1
        fi
    fi
else
    adb_shell getprop sys.boot_completed 2>/dev/null | grep -q "1" || {
        echo "No booted emulator found. Drop --no-boot or boot one first." >&2
        exit 1
    }
fi

"$ADB" root >/dev/null 2>&1 || true
sleep 3
"$ADB" wait-for-device

skip_setup_wizard

if [[ "$KEEP_APK" -ne 1 ]]; then
    log "building debug APK"
    ( cd "$ROOT" && ./gradlew assembleDebug -q )
fi

log "installing APK"
"$ADB" install -r "$ROOT/app/build/outputs/apk/debug/app-debug.apk" >/dev/null

log "granting widget bind permission"
adb_shell appwidget grantbind --package "$PACKAGE" --user 0 || true

freeze_clock

mkdir -p "$WORK_DIR/shots"

# ---------------------------------------------------------------------------
# widget captures: theme -> (output name, target width in px, resize?)
# ---------------------------------------------------------------------------
# narrow: pinned size (4 cells on the Pixel 9 profile); wide: 5 cells.
# The target widths are refined against the actual launcher grid below.

capture_widget_shot() {
    local theme="$1" name="$2" wide="$3"

    log "capturing $name ($theme)"
    write_prefs "$theme"
    sleep 2

    pin_widget

    local add_bounds
    add_bounds="$(wait_for_text "Add Widget" 120)" || {
        log "config screen did not appear for $name" >&2
        dump_ui_debug
        return 1
    }
    tap_bounds "$add_bounds"
    sleep 2

    local widget_bounds
    widget_bounds="$(wait_for_desc "$WIDGET_MARKER" 240)" || {
        log "widget did not render for $name" >&2
        return 1
    }
    sleep 5

    if [[ "$wide" -eq 1 ]]; then
        # Compute 5-cell width from the current bounds: pinned is 4 cells.
        local p x1 y1 x2 y2 cur_w cell target
        read -r x1 y1 x2 y2 <<< "$(parse_bounds "$widget_bounds")"
        cur_w=$((x2 - x1))
        cell=$((cur_w / 4))
        target=$((cur_w + cell))
        resize_widget "$target"
        widget_bounds="$(wait_for_desc "$WIDGET_MARKER" 120)" || true
        sleep 5
    fi

    freeze_clock
    capture_screen "$WORK_DIR/shots/${name}_screen.png"

    crop_bounds "$WORK_DIR/shots/${name}_screen.png" "$widget_bounds" "$WORK_DIR/shots/${name}.png"

    remove_widget
    sleep 2
}

capture_widget_shot cold wettergraph_cold 1
capture_widget_shot warm wettergraph_warm 1
capture_widget_shot black wettergraph_color_black 0
capture_widget_shot round wettergraph_round_corners 0

# ---------------------------------------------------------------------------
# settings capture
# ---------------------------------------------------------------------------

log "capturing wettergraph_settings"
write_prefs round
sleep 2
adb_shell cmd uimode night yes || true
sleep 2
freeze_clock

# Fresh appWidgetId forces the new-widget config path; the mock hook attaches
# the default location so the screen is fully populated.
adb_shell am start -a android.appwidget.action.APPWIDGET_CONFIGURE \
    -n "$PACKAGE/$NS_PACKAGE.AfPreferenceActivity" --ei appWidgetId 424242 >/dev/null 2>&1 || true

wait_for_text "Add Widget" 120 >/dev/null || log "config screen did not appear for settings shot"
sleep 8
capture_screen "$WORK_DIR/shots/wettergraph_settings.png"
adb_shell cmd uimode night no || true

# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------

mkdir -p "$OUT_DIR"
cp "$WORK_DIR/shots"/wettergraph_*.png "$OUT_DIR/"
rm -f "$OUT_DIR"/af_weather_*.png

log "wrote screenshots to $OUT_DIR"
ls -la "$OUT_DIR"
