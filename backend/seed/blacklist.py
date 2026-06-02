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
    1. Curator calls DELETE /band/{id}/delete (writes to band_blacklist).
    2. Curator copies that MBID + reason into seed/blacklist.json and commits.
    3. Next `python -m seed.mb_dump` re-applies the JSON; deletions stay sticky
       across re-seeds and propagate to teammates / prod.
"""

from __future__ import annotations

import json
import logging
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
