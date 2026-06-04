"""Unit tests for the source-controlled genre allowlist + split-rule helper."""

from __future__ import annotations

import json

import pytest

from seed.genre_allowlist import core_votes, decide_auto_flag, load_allowlist


def test_load_allowlist_lowercases_tag_names(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["Hardcore Punk", "D-Beat"], "ignore": ["USA"]}))

    al = load_allowlist(path)

    assert al.core == {"hardcore punk", "d-beat"}
    assert al.ignore == {"usa"}


def test_load_allowlist_tolerates_missing_keys(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["hardcore punk"]}))

    al = load_allowlist(path)

    assert al.core == {"hardcore punk"}
    assert al.ignore == frozenset()


def test_load_allowlist_rejects_non_object(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps(["hardcore punk"]))

    with pytest.raises(ValueError, match="expected a JSON object"):
        load_allowlist(path)


def test_core_votes_sums_only_allowlisted_positive_votes(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["hardcore punk", "d-beat"], "ignore": ["usa"]}))
    al = load_allowlist(path)

    tags = [
        ("hardcore punk", 5),
        ("d-beat", 3),
        ("usa", 4),           # ignore-listed — not counted as core
        ("nu metal", 7),      # off-genre — not counted as core
        ("hardcore punk", 0), # non-positive — community refutation, not counted
    ]

    assert core_votes(tags, al) == 8


def test_core_votes_returns_zero_when_no_tags(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["hardcore punk"]}))
    al = load_allowlist(path)

    assert core_votes([], al) == 0


def test_core_votes_is_case_insensitive(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["hardcore punk"]}))
    al = load_allowlist(path)

    assert core_votes([("Hardcore Punk", 4)], al) == 4


def test_core_votes_excludes_seed_tag(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["hardcore punk", "d-beat"]}))
    al = load_allowlist(path)

    tags = [("hardcore punk", 5), ("d-beat", 3)]

    # Without exclude, both core tags count.
    assert core_votes(tags, al) == 8
    # Excluding the seed tag leaves only the corroborating d-beat votes.
    assert core_votes(tags, al, exclude={"hardcore punk"}) == 3
    # Case-insensitive on the exclude set too.
    assert core_votes(tags, al, exclude={"Hardcore Punk"}) == 3
    # A band tagged only with the seed tag has zero corroborating evidence.
    assert core_votes([("hardcore punk", 5)], al, exclude={"hardcore punk"}) == 0


def _allowlist(tmp_path):
    path = tmp_path / "al.json"
    path.write_text(json.dumps({"core": ["hardcore punk", "d-beat"], "ignore": []}))
    return load_allowlist(path)


def test_decide_auto_flag_no_mb_tags_is_unflagged(tmp_path):
    # No MB signal at all → "no signal", not an off-genre verdict.
    al = _allowlist(tmp_path)
    assert decide_auto_flag([], al, seed_tag="hardcore punk") is False


def test_decide_auto_flag_only_seed_tag_is_flagged(tmp_path):
    # MB tagged it, but the only signal is the seed tag itself → off-genre.
    al = _allowlist(tmp_path)
    assert decide_auto_flag([("hardcore punk", 5)], al, seed_tag="hardcore punk") is True


def test_decide_auto_flag_core_corroboration_is_unflagged(tmp_path):
    # A core tag beyond the seed tag corroborates scope.
    al = _allowlist(tmp_path)
    tags = [("hardcore punk", 5), ("d-beat", 3)]
    assert decide_auto_flag(tags, al, seed_tag="hardcore punk") is False


def test_decide_auto_flag_enrichment_rescues_off_genre_band(tmp_path):
    # MB only has the seed tag (would be flagged), but enrichment placed the
    # band in a curated genre → rescued. This is the 2010s-coverage case.
    al = _allowlist(tmp_path)
    tags = [("hardcore punk", 5)]
    assert (
        decide_auto_flag(tags, al, seed_tag="hardcore punk", has_enrichment_core=True)
        is False
    )


def test_decide_auto_flag_enrichment_does_not_rescue_no_signal(tmp_path):
    # has_enrichment_core is moot when MB never tagged the band — still unflagged
    # via the no-signal branch, not the enrichment branch.
    al = _allowlist(tmp_path)
    assert decide_auto_flag([], al, seed_tag="hardcore punk", has_enrichment_core=True) is False
