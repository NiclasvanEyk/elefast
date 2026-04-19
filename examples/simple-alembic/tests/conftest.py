import os
from pathlib import Path

import pytest
from sqlalchemy import NullPool, create_engine, make_url

from elefast import Database, DatabaseServer
from elefast.extras import alembic, docker

alembic_config = Path(__file__).parent.parent / "alembic.ini"


@pytest.fixture(scope="session")
def db_server() -> DatabaseServer:
    explicit_url = os.getenv("TESTING_DB_URL")
    if explicit_url:
        db_url = make_url(explicit_url)
    else:
        db_url = docker.postgres("psycopg")
    os.environ["ELEFAST_ALEMBIC_EXAMPLE_TESTING_DB_URL"] = db_url.render_as_string(
        hide_password=False
    )
    engine = create_engine(
        db_url, isolation_level="autocommit", poolclass=NullPool, echo=True
    )
    server = DatabaseServer(engine, schema=alembic.AlembicMigrator(alembic_config))
    return server.ensure_is_ready()


@pytest.fixture
def db(db_server: DatabaseServer):
    with db_server.create_database() as database:
        yield database


@pytest.fixture
def db_connection(db: Database):
    with db.engine.begin() as connection:
        yield connection


@pytest.fixture
def db_session(db: Database):
    with db.session() as session:
        yield session
