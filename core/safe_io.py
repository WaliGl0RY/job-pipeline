"""Shared write/verify helpers for data folders on flaky storage.

Why this exists (two incidents on the same day): a scheduled search run hit
`sqlite3.OperationalError: disk I/O error` on jobs.db because a stale
-journal file had been left behind, and separately the published dashboard
went blank because dashboard_template.html had been silently truncated
mid-<script> by an earlier write that was never verified. Both happened on a
synced/network-mounted folder, where edits made by one tool can take a while
to become visible to another. Always re-read a file you just wrote, from the
same tool you'll use to run it, before trusting its contents. On that kind of
mount, files could also not be deleted or renamed once written, only
truncated/overwritten in place, which is why the helpers below never delete.

Use these helpers for every write to files under the data folder so a repeat
of either failure mode gets caught (and retried) instead of shipping silently
broken data or a blank dashboard.
"""
import hashlib
import os
import sqlite3
import time
from pathlib import Path


def safe_write_bytes(path: Path, data: bytes, retries: int = 3, delay: float = 1.0) -> None:
    """Write bytes to `path`, verifying via checksum and retrying on mismatch
    or OSError. Raises RuntimeError if it still doesn't match after `retries`
    attempts -- callers should treat that as a hard failure, not log-and-continue.
    """
    path = Path(path)
    expected = hashlib.sha256(data).hexdigest()
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual == expected:
                return
            last_err = RuntimeError(
                "checksum mismatch after write (attempt %d/%d): expected %s.., got %s.."
                % (attempt, retries, expected[:12], actual[:12])
            )
        except OSError as e:
            last_err = e
        time.sleep(delay)
    raise RuntimeError("safe_write_bytes failed for %s after %d attempts: %s" % (path, retries, last_err))


def safe_write_text(path: Path, text: str, encoding: str = "utf-8", **kw) -> None:
    safe_write_bytes(Path(path), text.encode(encoding), **kw)


def clear_stale_sqlite_journal(db_path: Path) -> None:
    """If db_path opens and passes integrity_check fine in read-only/immutable
    mode (which ignores any -journal file), but a non-empty -journal is still
    sitting next to it, that journal is leftover cruft from a prior
    interrupted run and can make the *next* normal (non-immutable) connect()
    fail with 'disk I/O error'. Truncate it to 0 bytes in place -- deleting or
    renaming may be blocked on some mounts, but overwriting is fine, and an
    empty -journal is treated by SQLite as "no hot journal".
    """
    db_path = Path(db_path)
    journal = db_path.with_name(db_path.name + "-journal")
    if not journal.exists() or journal.stat().st_size == 0:
        return
    if not verify_sqlite_ok(db_path):
        return  # db itself looks broken -- don't touch the journal, let sqlite try real recovery
    try:
        with open(journal, "wb"):
            pass
    except OSError:
        pass  # best-effort only; normal sqlite3.connect() will still attempt its own recovery


def verify_sqlite_ok(db_path: Path) -> bool:
    """Read-only, immutable-mode integrity check (bypasses any journal)."""
    try:
        con = sqlite3.connect("file:%s?mode=ro&immutable=1" % Path(db_path).as_posix(), uri=True)
        row = con.execute("PRAGMA integrity_check").fetchone()
        con.close()
        return bool(row) and row[0] == "ok"
    except Exception:
        return False


def safe_sqlite_connect(db_path: Path, retries: int = 3, delay: float = 1.0) -> sqlite3.Connection:
    """sqlite3.connect() with stale-journal cleanup + retry on 'disk I/O error'."""
    db_path = Path(db_path)
    last_err = None
    for attempt in range(1, retries + 1):
        clear_stale_sqlite_journal(db_path)
        try:
            con = sqlite3.connect(str(db_path))
            con.execute("PRAGMA quick_check").fetchone()
            return con
        except sqlite3.OperationalError as e:
            last_err = e
            time.sleep(delay)
    raise RuntimeError("safe_sqlite_connect failed for %s after %d attempts: %s" % (db_path, retries, last_err))
