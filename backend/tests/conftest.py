import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app as app_pkg
from app.database import Base, get_db

# The FastAPI instance shares its name with the package; access it explicitly
# to avoid `from app import app` resolving to the package under pytest.
fastapi_app = app_pkg.app

# In-memory SQLite shared across the test session via StaticPool.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _enable_sqlite_fks(dbapi_connection, _record):
    # SQLite ignores FK constraints unless told otherwise.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture()
def client():
    # Models are imported via app import chain; build a fresh schema per test.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _isolate_blacklist_file(tmp_path, monkeypatch):
    # The delete endpoint and seed.mb_dump both consult seed/blacklist.json.
    # Redirect every test to a per-test tmp path by default so nothing here
    # mutates the checked-in file; tests that want to exercise file behavior
    # override it locally with their own monkeypatch.setattr.
    import seed.blacklist as bl

    monkeypatch.setattr(bl, "BLACKLIST_PATH", tmp_path / "no-real-blacklist.json")


@pytest.fixture()
def db(client):
    # A session on the same in-memory engine for tests that need to seed rows
    # the API has no write endpoint for (e.g. Members). Depends on `client` so
    # the schema is already created. StaticPool means it shares the request
    # sessions' connection, so committed rows are visible to API calls.
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
