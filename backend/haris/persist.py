"""Keep Haris's SQLite files across restarts on a host whose disk is wiped (Render's free plan).

When DATABASE_URL points at a Postgres database, each SQLite file (reports, alert subscribers,
campaign radar) is copied there whenever it changes, checked every few seconds and once more when
the server stops. When the server starts, the saved copies are written back before anything opens
them. The app keeps using SQLite exactly as on a laptop; Postgres only holds the latest copy of
each file. Without DATABASE_URL this module does nothing.
"""
from __future__ import annotations

import atexit
import logging
import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

log = logging.getLogger("haris.persist")

INTERVAL = float(os.getenv("HARIS_PERSIST_SECONDS", "5"))
_lock = threading.Lock()
_saved: dict[str, float] = {}


def _files() -> dict[str, Path]:
    from . import alerts, inbox, radar  # the same paths the modules use
    return {"inbox": inbox._settings()["db"], "alerts": alerts._settings()["db"], "radar": radar._settings()["db"]}


def _connect():
    import psycopg  # only needed on the host, where requirements.txt installs it

    con = psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=15, autocommit=True)
    con.execute("CREATE TABLE IF NOT EXISTS haris_files "
                "(name TEXT PRIMARY KEY, data BYTEA NOT NULL, saved_at DOUBLE PRECISION NOT NULL)")
    return con


def _snapshot(path: Path) -> bytes:
    """A consistent copy of a live SQLite file, including anything still in its write-ahead log."""
    src = sqlite3.connect(path)
    try:
        if hasattr(src, "serialize"):
            return src.serialize()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "copy.db"
            src.execute("VACUUM INTO ?", (str(out),))
            return out.read_bytes()
    finally:
        src.close()


def restore() -> int:
    """Write the saved copies back to disk. Returns how many files were restored."""
    restored = 0
    with _connect() as con:
        for name, path in _files().items():
            row = con.execute("SELECT data FROM haris_files WHERE name = %s", (name,)).fetchone()
            if not row:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            for extra in (Path(f"{path}-wal"), Path(f"{path}-shm")):
                extra.unlink(missing_ok=True)
            path.write_bytes(bytes(row[0]))
            os.chmod(path, 0o600)
            _saved[name] = path.stat().st_mtime
            restored += 1
    return restored


def save(force: bool = False) -> int:
    """Copy every file that changed since it was last saved. Returns how many were saved."""
    with _lock:
        changed = {}
        for name, path in _files().items():
            if not path.exists():
                continue
            stamp = max(p.stat().st_mtime for p in (path, Path(f"{path}-wal")) if p.exists())
            if force or _saved.get(name) != stamp:
                changed[name] = (path, stamp)
        if not changed:
            return 0
        with _connect() as con:
            for name, (path, stamp) in changed.items():
                con.execute("INSERT INTO haris_files (name, data, saved_at) VALUES (%s, %s, %s) "
                            "ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data, saved_at = EXCLUDED.saved_at",
                            (name, _snapshot(path), time.time()))
                _saved[name] = stamp
        return len(changed)


def _loop() -> None:
    while True:
        time.sleep(INTERVAL)
        try:
            save()
        except Exception as err:  # noqa: BLE001  the next round tries again
            log.warning("saving the data to Postgres failed: %s", type(err).__name__)


def _at_exit() -> None:
    try:
        save()
    except Exception as err:  # noqa: BLE001
        log.warning("final save to Postgres failed: %s", type(err).__name__)


def start() -> None:
    if not os.getenv("DATABASE_URL"):
        return
    try:
        n = restore()
        log.warning("restored %d data file(s) from Postgres", n)  # warning level, so it shows in the host's log
        save()  # the first deploy: keep the demo set that the build made
    except Exception as err:  # noqa: BLE001  the app still runs, on its fresh disk
        log.warning("Postgres persistence is off: %s", type(err).__name__)
        return
    threading.Thread(target=_loop, name="persist", daemon=True).start()
    atexit.register(_at_exit)
