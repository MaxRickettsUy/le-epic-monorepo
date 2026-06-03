"""Source-controlled genre allowlist used to compute `Band.auto_flagged`.

`genre_allowlist.json` partitions MB tag names into two sets:
    - `core`   — tags that count as in-scope hardcore-punk signal.
    - `ignore` — tags that aren't genre signal at all (country, region, era,
                 MB cruft like "_edit", curator opinions). Listed for future
                 share-based rules; the bare `core_votes == 0` rule used today
                 doesn't consult it.

The seed reads this file once per run and uses the `core` set to decide
whether a band has any in-scope MB tag votes. Tag names are normalized to
lowercase on both sides of the comparison so the JSON can stay human-readable
without forcing a specific casing on MB.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ALLOWLIST_PATH = Path(__file__).with_name("genre_allowlist.json")


@dataclass(frozen=True)
class GenreAllowlist:
    core: frozenset[str]
    ignore: frozenset[str]


def load_allowlist(path: Path | None = None) -> GenreAllowlist:
    """Read the checked-in allowlist file. Tag names are lowercased."""
    if path is None:
        path = ALLOWLIST_PATH
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(data).__name__}")
    return GenreAllowlist(
        core=frozenset(t.lower() for t in data.get("core", [])),
        ignore=frozenset(t.lower() for t in data.get("ignore", [])),
    )


def core_votes(tags: list[tuple[str, int]], allowlist: GenreAllowlist) -> int:
    """Sum positive vote counts for tags that fall in the `core` set."""
    return sum(votes for name, votes in tags if votes > 0 and name.lower() in allowlist.core)
