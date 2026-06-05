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
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object, got {type(data).__name__}")

    def _tag_set(key: str) -> frozenset[str]:
        values = data.get(key, [])
        if not isinstance(values, list) or not all(isinstance(t, str) for t in values):
            raise ValueError(f"{path}: '{key}' must be a list of strings")
        return frozenset(t.lower() for t in values)

    return GenreAllowlist(core=_tag_set("core"), ignore=_tag_set("ignore"))


def core_votes(
    tags: list[tuple[str, int]],
    allowlist: GenreAllowlist,
    exclude: frozenset[str] | set[str] | None = None,
) -> int:
    """Sum positive vote counts for tags that fall in the `core` set.

    `exclude` is a set of lowercased tag names to skip — the seed scope tag
    is passed here so it doesn't count as corroborating evidence of itself
    (otherwise every seeded band trivially has core_votes > 0).
    """
    skip = {t.lower() for t in (exclude or ())}
    return sum(
        votes
        for name, votes in tags
        if votes > 0 and name.lower() in allowlist.core and name.lower() not in skip
    )


def decide_auto_flag(
    tags: list[tuple[str, int]],
    allowlist: GenreAllowlist,
    *,
    seed_tag: str,
    has_enrichment_core: bool = False,
) -> bool:
    """Decide whether a band looks off-genre and should be auto-flagged.

    Flag iff MB tagged the band (so we have *some* signal to judge) but none of
    that signal corroborates the catalogue's scope. A band is in-scope — and so
    NOT flagged — when any of:

    - MB never tagged it at all (``total == 0``): "no signal" is a different
      review surface, not an off-genre verdict.
    - It carries core MB tag votes beyond the seed tag itself.
    - An enrichment provider has placed it in a curated genre
      (``has_enrichment_core``): enrichment only ever links in-scope genres, so
      e.g. a 2010s band MusicBrainz never tagged "hardcore punk" but Last.fm
      tags "metalcore" is rescued rather than flagged.

    The seed tag is excluded from the core count because every seeded band has
    it by construction — counting it would make the off-genre branch unreachable.
    """
    total = sum(v for _, v in tags)
    if total == 0:
        return False
    if has_enrichment_core:
        return False
    return core_votes(tags, allowlist, exclude={seed_tag}) == 0
