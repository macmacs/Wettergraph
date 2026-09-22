#!/usr/bin/env python3
"""Publish the graph into the shared folder (ticket 06).

The dashboard path is Home Assistant's Generic Camera polling this app's own
port. When the HA instance cannot reach that port, HA can still read a file: the
same PNG is kept in step at ``<share>/wettergraph/graph.png``, which HA core
sees as ``/share/wettergraph/graph.png``, so the Local file camera - or any
integration that reads a file - shows the same graph with no HTTP in between.
The app is allowed to write there because ``config.yaml`` maps ``share:rw``
(app configuration docs; unlike ``/config``, which inside an app container is
the app's *own* public config folder, not Home Assistant's).

Writes are change-driven. The loop renders every ``interval`` seconds but only
writes when the bytes differ, so the common case costs one render and no disk
write. Renders are byte-identical for the same input (``render.py``), which is
what makes that comparison meaningful.

A ``/share`` that is missing or read-only is reported **once**, in the app log
and on the status page, not every minute: on a box without the mapping the
fallback is simply unavailable, and the dashboard path does not use it.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

DEFAULT_SHARE_DIR = Path(os.environ.get("WG_SHARE", "/share"))
SUBDIR = "wettergraph"
FILENAME = "graph.png"


class Publisher:
    """Keep one PNG in step with the served image. Never raises."""

    def __init__(self, share_dir: Path | str | None = None) -> None:
        self.root = Path(share_dir) if share_dir is not None else DEFAULT_SHARE_DIR
        self.path = self.root / SUBDIR / FILENAME
        self.writes = 0
        self.last_write: float | None = None
        self.last_error: str | None = None
        self._reported: str | None = None

    # ------------------------------------------------------------------ state

    def status(self) -> dict:
        """The file's own state, plus what this run has written.

        The age comes from the file's mtime, not from this process: after a
        restart the copy is usually already current, and "written 3 minutes ago"
        should then describe the file, not the restart.
        """
        try:
            info = self.path.stat()
            exists, size, mtime = True, info.st_size, info.st_mtime
        except OSError:
            exists, size, mtime = False, 0, None
        return {
            "path": str(self.path),
            "exists": exists,
            "bytes": size,
            "mtime": mtime,
            "age_seconds": None if mtime is None else max(0.0, time.time() - mtime),
            "writes": self.writes,
            "last_error": self.last_error,
        }

    def _note(self, message: str) -> None:
        """Log a problem the first time it happens; stay quiet afterwards."""
        self.last_error = message
        if message != self._reported:
            print(f"wettergraph: share {message}", flush=True)
            self._reported = message

    # ---------------------------------------------------------------- writing

    def publish(self, png: bytes) -> bool:
        """Write ``png`` when the file on disk differs. True when a write happened."""
        try:
            if self.path.read_bytes() == png:
                self.last_error = None
                return False
        except OSError:
            pass  # missing (the normal first run) or unreadable: try to write

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Write beside the target and rename: a reader must never see half a
            # PNG. HA may read the file at any moment.
            scratch = self.path.with_name(self.path.name + ".tmp")
            scratch.write_bytes(png)
            scratch.replace(self.path)
        except OSError as exc:
            self._note(f"cannot write {self.path}: {type(exc).__name__}: {exc}")
            return False

        self.writes += 1
        self.last_write = time.time()
        if self.last_error is not None:
            print(f"wettergraph: share recovered, writing {self.path}", flush=True)
            self.last_error = None
        self._reported = None
        print(f"wettergraph: share wrote {self.path} ({len(png)}B, write #{self.writes})", flush=True)
        return True

    def run_forever(self, render, stop, interval: float = 60.0) -> None:
        """Publish immediately, then whenever the render changes.

        ``render()`` returns PNG bytes; the caller keeps the options and the
        cached series, so this module stays unaware of both.
        """
        while True:
            try:
                self.publish(render())
            except Exception as exc:  # noqa: BLE001 - a broken render must not kill the loop
                self._note(f"render failed: {type(exc).__name__}: {exc}")
            if stop.wait(interval):
                return


if __name__ == "__main__":  # pragma: no cover - manual probe on a dev box
    import sys

    if len(sys.argv) != 2:
        sys.exit("usage: publish.py <png>   # copies a file into the share folder")
    source = Path(sys.argv[1])
    publisher = Publisher()
    changed = publisher.publish(source.read_bytes())
    print(f"{'wrote' if changed else 'unchanged'}: {publisher.path}")
    print(publisher.status())
