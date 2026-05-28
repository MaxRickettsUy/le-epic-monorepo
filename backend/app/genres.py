"""Curated hardcore sub-genre vocabulary.

This module is the **single source of truth** for the sub-genre list. The `genre`
table is seeded from it (a queryable cache), not the other way around. MusicBrainz
`artist_tag` values are free-form and noisy, so each curated genre carries the set of
lowercased MB tag aliases that should map onto it; the seed funnels raw tags through
`ALIAS_TO_SLUG` and drops anything not curated.

See `plans/subgenres.md`. The draft list is not yet locked — extend before seeding.
"""

# slug -> (display name, {lowercased MB tag aliases that map to this genre})
CURATED_GENRES: dict[str, tuple[str, set[str]]] = {
    "nyhc": ("NYHC", {"nyhc", "new york hardcore", "n.y.h.c."}),
    "youth-crew": ("Youth Crew", {"youth crew", "youthcrew"}),
    "melodic-hardcore": ("Melodic Hardcore", {"melodic hardcore"}),
    "beatdown": ("Beatdown", {"beatdown", "beatdown hardcore"}),
    "powerviolence": ("Powerviolence", {"powerviolence", "power violence"}),
    "metalcore": ("Metalcore", {"metalcore"}),
    "post-hardcore": ("Post-Hardcore", {"post-hardcore", "post hardcore"}),
    "d-beat": ("D-beat", {"d-beat", "dbeat", "d beat"}),
    "crust": ("Crust Punk", {"crust", "crust punk", "crustcore"}),
    "straight-edge": ("Straight Edge", {"straight edge", "sxe", "straightedge"}),
    "grindcore": ("Grindcore", {"grindcore", "grind"}),
    "thrashcore": ("Thrashcore", {"thrashcore", "fastcore"}),
    "crossover-thrash": ("Crossover Thrash", {"crossover thrash", "crossover"}),
    "screamo": ("Screamo", {"screamo", "emoviolence", "emo violence", "emo-violence"}),
    "emo": ("Emo", {"emo", "emocore"}),
    "skate-punk": ("Skate Punk", {"skate punk", "skatepunk"}),
    "oi": ("Oi!", {"oi", "oi!", "street punk", "streetpunk"}),
    "mathcore": ("Mathcore", {"mathcore", "math core"}),
    "deathcore": ("Deathcore", {"deathcore"}),
    "metallic-hardcore": ("Metallic Hardcore", {"metallic hardcore"}),
    "anarcho-punk": ("Anarcho-Punk", {"anarcho-punk", "anarcho punk", "anarchopunk"}),
    "ska-punk": ("Ska Punk", {"ska punk", "ska-core", "skacore"}),
    "sludge": ("Sludge", {"sludge", "sludge metal", "sludgecore"}),
    "chaotic-hardcore": ("Chaotic Hardcore", {"chaotic hardcore"}),
}

# Reverse lookup: lowercased MB tag alias (and the slug itself) -> curated slug.
# Built once at import; mapping the slug to itself lets slug forms resolve too.
ALIAS_TO_SLUG: dict[str, str] = {
    key: slug
    for slug, (_name, aliases) in CURATED_GENRES.items()
    for key in (slug, *aliases)
}


def slug_for_tag(tag: str) -> str | None:
    """Map a raw MusicBrainz tag to a curated genre slug, or None if not curated."""
    return ALIAS_TO_SLUG.get(tag.strip().lower())
