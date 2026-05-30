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
    bands_per_page: int = 10
    releases_per_page: int = 10

    # Origins allowed by CORS. Comma-separated in the env var; "*" allows all.
    # Defaults to local-dev; set an explicit allowlist in deployed environments.
    cors_origins: str = "http://localhost:3000"

    # Contact email sent in the MusicBrainz API user-agent (their API etiquette).
    # No default: deployments must set MUSICBRAINZ_CONTACT_EMAIL.
    musicbrainz_contact_email: str = ""


settings = Settings()
