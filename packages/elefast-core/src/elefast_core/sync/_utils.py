from elefast_core.errors import DatabaseNotReadyError
import time
from uuid import uuid4

from sqlalchemy import URL, Engine, NullPool, create_engine, text
from sqlalchemy.exc import OperationalError

type CanBeTurnedIntoEngine = Engine | URL | str


def build_engine(input: CanBeTurnedIntoEngine) -> Engine:
    if isinstance(input, Engine):
        return input
    if isinstance(input, URL | str):
        return create_engine(input, isolation_level="autocommit", poolclass=NullPool)
    raise TypeError()


def prepare_database(
    engine: Engine, encoding: str = "utf8", template: str | None = None
) -> Engine:
    database = f"pytest-elephantastic-{uuid4()}"
    with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"{database}\" ENCODING '{encoding}' TEMPLATE template0"
            if template is None
            else f'CREATE DATABASE "{database}" WITH TEMPLATE "{template}"'
        )
        connection.execute(text(statement))
        connection.commit()
    return create_engine(engine.url.set(database=database))


def drop_database(engine: Engine, name: str) -> None:
    with engine.begin() as connection:
        statement = f'DROP DATABASE "{name}"'
        connection.execute(text(statement))


def wait_for_db(engine: Engine, timeout: int | float = 30, interval: int | float = 0.5):
    deadline = time.monotonic() + timeout
    attempts = 0

    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as error:
            attempts += 1
            if time.monotonic() >= deadline:
                raise DatabaseNotReadyError(
                    f"Reached the configured timeout of {timeout} seconds after {attempts} attempts connecting to the datbase."
                ) from error
            time.sleep(interval)
