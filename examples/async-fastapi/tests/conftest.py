from fastapi.testclient import TestClient
from os import getenv

import pytest
from elefast import MetaDataBasedAsyncDatabaseServer, AsyncDatabaseServer, AsyncDatabase
from elefast.docker import postgres as start_and_get_postgres_container_url

from elefast_example_fastapi_async.database import Base
from elefast_example_fastapi_async.app import app


@pytest.fixture(scope="session")
def postgres():
    url = getenv("TESTING_DB_URL") or start_and_get_postgres_container_url(
        driver="asyncpg"
    )
    return MetaDataBasedAsyncDatabaseServer(url, Base.metadata)


@pytest.fixture
async def db(postgres: AsyncDatabaseServer, monkeypatch: pytest.MonkeyPatch):
    async with await postgres.create_database() as database:
        db_url = database.url.render_as_string(hide_password=False)
        monkeypatch.setenv("DB_URL", db_url)
        yield database


@pytest.fixture
async def db_connection(db: AsyncDatabase):
    async with db.engine.begin() as connection:
        yield connection


@pytest.fixture
async def db_session(db: AsyncDatabase):
    async with db.session() as session:
        yield session


@pytest.fixture
def backend(db):
    # NOTE: The db fixture is used here, so we have at least one database for the lifespan of the app
    with TestClient(app) as test_client:
        yield test_client
