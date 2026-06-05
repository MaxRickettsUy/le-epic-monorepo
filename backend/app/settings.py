from pydantic import PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from env vars (and an optional .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hc_archives_back"
    # The MusicBrainz dump Postgres (metabrainz/musicbrainz-docker). Used only
    # by the seed scripts, not the API.
    mb_database_url: str = (
        "postgresql+psycopg2://musicbrainz:musicbrainz@localhost:5433/musicbrainz_db"
    )
    # Genre tag the catalogue is scoped to.
    seed_tag: str = "hardcore punk"
    bands_per_page: PositiveInt = 10
    releases_per_page: PositiveInt = 10

    # Origins allowed by CORS. Comma-separated in the env var; "*" allows all.
    # Defaults to local-dev; set an explicit allowlist in deployed environments.
    cors_origins: str = "http://localhost:3000"

    # Contact email sent in the MusicBrainz API user-agent (their API etiquette).
    # No default: deployments must set MUSICBRAINZ_CONTACT_EMAIL.
    musicbrainz_contact_email: str = ""

    # Last.fm enrichment (seed.lastfm_tags). The seeder no-ops with a log line
    # if the key is unset, so leaving these blank is safe for local dev.
    lastfm_api_key: str | None = None
    lastfm_api_url: str = "https://ws.audioscrobbler.com/2.0/"


settings = Settings()
