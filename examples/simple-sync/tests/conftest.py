import pytest
from elefast import DatabaseServer, Database, docker


@pytest.fixture(scope="session")
def db_server() -> DatabaseServer:
    return DatabaseServer(docker.postgres("psycopg2"))


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
