from __future__ import annotations
from uuid import uuid4
import time
from elefast.errors import DatabaseNotReadyError

from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy import URL, Engine, MetaData, text, create_engine, NullPool
from sqlalchemy.orm import Session, sessionmaker


type CanBeTurnedIntoEngine = Engine | URL | str


class Database(AbstractContextManager):
    def __init__(
        self,
        engine: Engine,
        server: DatabaseServer,
        sessionmaker_factory: Callable[[Engine], Callable[[], Session]] = sessionmaker,
    ) -> None:
        self.engine = engine
        self.server = server
        self.sessionmaker = sessionmaker_factory(self.engine)
        assert self.engine.url.database
        self.name = self.engine.url.database

    def __exit__(self, exc_type, exc, tb):
        self.drop()

    @property
    def url(self) -> URL:
        return self.engine.url

    def drop(self) -> None:
        self.engine.dispose()
        self.server.drop_database(self.name)

    def session(self) -> Session:
        return self.sessionmaker()


class DatabaseServer:
    def __init__(
        self,
        engine: CanBeTurnedIntoEngine,
        metadata: MetaData | None = None,
    ) -> None:
        self._metadata = metadata
        self._engine = _build_engine(engine)
        self._template_db_name: str | None = None

    @property
    def url(self) -> URL:
        return self._engine.url

    def ensure_is_ready(
        self, timeout: int | float = 30, interval: int | float = 0.5
    ) -> None:
        deadline = time.monotonic() + timeout
        attempts = 0

        while True:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return
            except Exception as error:
                attempts += 1
                if time.monotonic() >= deadline:
                    raise DatabaseNotReadyError(
                        f"Reached the configured timeout of {timeout} seconds after {attempts} attempts connecting to the database."
                    ) from error
                time.sleep(interval)

    def create_database(self) -> Database:
        template_db = self._template_db_name
        if template_db is None:
            engine = _prepare_database(self._engine)
            if self._metadata:
                with engine.begin() as connection:
                    self._metadata.drop_all(bind=connection)
                    self._metadata.create_all(bind=connection)
            engine.dispose()
            template_db = engine.url.database
            assert isinstance(template_db, str)
            self._template_db_name = template_db

        engine = _prepare_database(self._engine, template=template_db)
        return Database(engine=engine, server=self)

    def drop_database(self, name: str) -> None:
        with self._engine.begin() as connection:
            statement = f'DROP DATABASE "{name}"'
            connection.execute(text(statement))


def _build_engine(input: CanBeTurnedIntoEngine) -> Engine:
    if isinstance(input, Engine):
        return input
    if isinstance(input, URL | str):
        return create_engine(input, isolation_level="autocommit", poolclass=NullPool)
    raise TypeError()


def _prepare_database(
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
