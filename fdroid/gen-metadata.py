#!/usr/bin/env python3
"""Generate the fdroidserver metadata file for a binary-only repo.

fdroidserver only attaches changelogs (whatsNew) to a version if the app
metadata lists a matching entry under Builds, and it decides which version is
"current" from CurrentVersionCode. For a repo that publishes prebuilt APKs
there is nothing to derive that from, so both are generated here by reading
every APK already in the repo directory.

Usage: gen-metadata.py <package-id> <base-yml> <repo-dir> <out-yml>
"""

import re
import subprocess
import sys
from pathlib import Path

PACKAGE_LINE = re.compile(
    r"package: name='(?P<name>[^']+)'"
    r" versionCode='(?P<code>\d+)'"
    r" versionName='(?P<version>[^']*)'"
)


def badging(apk):
    out = subprocess.run(
        ["aapt2", "dump", "badging", str(apk)],
        check=True, capture_output=True, text=True,
    ).stdout
    for line in out.splitlines():
        match = PACKAGE_LINE.match(line)
        if match:
            return match.group("name"), int(match.group("code")), match.group("version")
    raise SystemExit(f"{apk}: no package line in aapt2 badging output")


def main():
    package_id, base_yml, repo_dir, out_yml = sys.argv[1:5]

    builds = {}
    for apk in sorted(Path(repo_dir).glob("*.apk")):
        name, code, version = badging(apk)
        if name == package_id:
            builds[code] = version

    if not builds:
        raise SystemExit(f"No {package_id} APKs found in {repo_dir}")

    lines = [Path(base_yml).read_text().rstrip("\n"), ""]
    lines.append(f"CurrentVersionCode: {max(builds)}")
    lines.append(f"CurrentVersion: \"{builds[max(builds)]}\"")
    lines.append("Builds:")
    for code in sorted(builds):
        lines.append(f"  - versionCode: {code}")
        lines.append(f"    versionName: \"{builds[code]}\"")
    lines.append("")

    Path(out_yml).write_text("\n".join(lines))
    print(f"{out_yml}: {len(builds)} version(s), current {max(builds)}")


if __name__ == "__main__":
    main()
