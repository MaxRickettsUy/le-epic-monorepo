"""Last.fm web-API access, isolated from the rest of the app.

Used by the enrichment seeder (`seed.lastfm_tags`) to fetch tag signal for
bands MusicBrainz seeded but tagged thinly. Mirrors the shape of
`services/musicbrainz.py`: one tight surface, all HTTP confined here so the
seeder can be unit-tested with a fake `fetch`.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable

from app.settings import settings

logger = logging.getLogger("services.lastfm")

USER_AGENT = "Hardchives/0.1"


class LastfmError(RuntimeError):
    """Raised when the Last.fm API returns an error payload."""


Fetch = Callable[[str], dict]


def _default_fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def top_tags(
    mbid: str,
    *,
    api_key: str | None = None,
    api_url: str | None = None,
    fetch: Fetch = _default_fetch,
) -> list[tuple[str, int]]:
    """Return Last.fm's top tags for an artist as `(name, weight)` pairs.

    Weights are Last.fm's 0–100 scores. Returns `[]` on a missing artist or a
    transient network error (the seeder logs and moves on rather than failing
    a long enrichment pass for one bad MBID).
    """
    key = api_key if api_key is not None else settings.lastfm_api_key
    if not key:
        raise LastfmError("LASTFM_API_KEY is unset")
    base = api_url or settings.lastfm_api_url
    params = urllib.parse.urlencode(
        {
            "method": "artist.getTopTags",
            "mbid": mbid,
            "api_key": key,
            "format": "json",
        }
    )
    url = f"{base}?{params}"
    try:
        data = fetch(url)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        logger.warning("Last.fm fetch failed for %s: %s", mbid, e)
        return []
    # Last.fm error payloads carry a top-level "error" int + "message".
    if isinstance(data, dict) and "error" in data:
        # Code 6 = "The artist you supplied could not be found" — quiet.
        if data.get("error") != 6:
            logger.warning("Last.fm error for %s: %s", mbid, data.get("message"))
        return []
    tags_node = (data.get("toptags") or {}).get("tag") or []
    out: list[tuple[str, int]] = []
    for t in tags_node:
        name = (t.get("name") or "").strip()
        if not name:
            continue
        try:
            weight = int(t.get("count") or 0)
        except (TypeError, ValueError):
            continue
        out.append((name, weight))
    return out
