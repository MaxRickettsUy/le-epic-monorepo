"""Source-controlled MBID blacklist applied before each seed run.

`band_blacklist` is a database table, so curator decisions made via
`DELETE /band/{id}/delete` only live in whichever DB the call hit. Without a
checked-in source of truth, a fresh DB (or a second environment) would
re-import every off-genre band the curator already removed.

`blacklist.json` is that source of truth: a list of `{mbid, reason}` records
that `seed.mb_dump` upserts into `band_blacklist` at the top of every run.
The DB table is still the runtime authority (and what the seeder filters
against), but the JSON guarantees the table is at least as broad as the
checked-in decisions whenever a re-seed happens.

Workflow:
    1. Curator calls DELETE /band/{id}/delete. The endpoint writes the row to
       band_blacklist AND appends to seed/blacklist.json (via `append_entry`).
    2. Curator `git commit`s the file diff to make the decision durable for
       teammates / fresh DBs / prod.
    3. Next `python -m seed.mb_dump` re-applies the JSON; deletions stay sticky
       across re-seeds.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import BandBlacklist

logger = logging.getLogger("seed.blacklist")

BLACKLIST_PATH = Path(__file__).with_name("blacklist.json")


def load_blacklist(path: Path | None = None) -> list[dict]:
    """Read the checked-in blacklist file. Returns [] if missing."""
    # Resolved per-call (not as a default-arg) so tests that monkeypatch the
    # module-level BLACKLIST_PATH actually take effect.
    if path is None:
        path = BLACKLIST_PATH
    if not path.exists():
        return []
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list, got {type(data).__name__}")
    for entry in data:
        if not isinstance(entry, dict) or "mbid" not in entry:
            raise ValueError(f"{path}: each entry needs an 'mbid' key, got {entry!r}")
    return data


def apply_blacklist(session: Session, path: Path | None = None) -> dict:
    """Upsert the checked-in blacklist into `band_blacklist`.

    Idempotent: existing rows have their `reason` refreshed from the file
    (file wins on conflict, since it's the source of truth); new rows are
    inserted. Does NOT delete rows the file no longer mentions — entries
    added directly via the delete endpoint stay put.
    """
    entries = load_blacklist(path)
    inserted = 0
    updated = 0
    for entry in entries:
        mbid = entry["mbid"]
        reason = entry.get("reason")
        row = session.get(BandBlacklist, mbid)
        if row is None:
            session.add(BandBlacklist(mbid=mbid, reason=reason))
            inserted += 1
        elif row.reason != reason:
            row.reason = reason
            updated += 1
    session.flush()
    stats = {"inserted": inserted, "updated": updated, "total_in_file": len(entries)}
    if inserted or updated:
        logger.info("blacklist applied: %s", stats)
    return stats


def append_entry(mbid: str, reason: str | None, path: Path | None = None) -> str:
    """Add (or refresh) one entry in `blacklist.json`. Returns the action taken.

    - `"added"`     — mbid was new; appended at the end.
    - `"updated"`   — mbid was present with a different reason; reason replaced.
    - `"unchanged"` — mbid was present with the same reason; file untouched.

    Writes are atomic (temp file + rename) so a crash mid-write can't leave
    the JSON half-flushed. Callers should treat this as a best-effort hook
    from the API layer — failures to write the file (read-only FS, etc.) bubble
    up and should be handled by the caller, since the DB row is the runtime
    authority and a missing file write is a "commit me later" reminder, not a
    correctness issue.
    """
    if path is None:
        path = BLACKLIST_PATH
    entries = load_blacklist(path)
    action = "added"
    for entry in entries:
        if entry["mbid"] == mbid:
            if entry.get("reason") == reason:
                return "unchanged"
            entry["reason"] = reason
            action = "updated"
            break
    else:
        new = {"mbid": mbid}
        if reason is not None:
            new["reason"] = reason
        entries.append(new)

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".blacklist.", suffix=".json.tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(entries, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return action
