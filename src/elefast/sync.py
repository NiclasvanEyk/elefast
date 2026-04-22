from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, Self, TypeAlias
from uuid import uuid4

from sqlalchemy import URL, Connection, Engine, MetaData, NullPool, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema

from elefast.errors import DatabaseNotReadyError

CanBeTurnedIntoEngine: TypeAlias = "Engine | URL | str"


class Migrator(Protocol):
    """
    Defines how the database schema is created.
    """

    def migrate(self, connection: Connection) -> None:
        """
        Creates the database schema for the passed `connection`.
        """


class MetadataMigrator(Migrator):
    """
    Creates the database schema based on `sqlalchemy.MetaData`.
    """

    def __init__(self, metadata: MetaData) -> None:
        self._metadata = metadata

    def migrate(self, connection: Connection) -> None:
        """
        Drops and creates all tables specified in the `metadata` object passed via the constructor.
        """
        schemas = {
            table.schema
            for table in self._metadata.tables.values()
            if table.schema is not None and table.schema != "public"
        }
        for schema in schemas:
            connection.execute(CreateSchema(schema, if_not_exists=True))
        self._metadata.drop_all(bind=connection)
        self._metadata.create_all(bind=connection)


class Database(AbstractContextManager):
    """
    A Postgres database.
    """

    def __init__(
        self,
        engine: Engine,
        server: DatabaseServer,
        sessionmaker_factory: Callable[[Engine], Callable[[], Session]] = sessionmaker,
    ) -> None:
        """
        Note that this is usually obtained from [`DatabaseServer.create_database()`][DatabaseServer.create_database]
        and you should not need to construct it yourself.

        Params:
            engine: the engine holding the connections to the specific database.
            server: a reference to the database server that created the database.
            sessionmaker_factory: allows you to set custom options for the [`Database.session()`][Database.session] utility.
        """
        self.engine = engine
        self.server = server
        self.sessionmaker = sessionmaker_factory(self.engine)
        assert self.engine.url.database
        self._name = self.engine.url.database

    def __exit__(self, exc_type, exc, tb):
        self.drop()

    @property
    def url(self) -> URL:
        """
        The engine URL, allowing you to create your own engines with custom options.
        """
        return self.engine.url

    @property
    def name(self) -> str:
        """
        The name of the database.
        """
        return self._name

    def drop(self) -> None:
        """
        Disposes the engine and drops the database.

        If you for some reason do not use this class as a context manager, use this to clean up
        when you don't need it anymore.
        """
        self.engine.dispose()
        self.server.drop_database(self.name)

    def session(self) -> Session:
        """
        Creates a new ORM session.

        You can use the `sessionmaker_factory` parameter of the constructor to customize options.
        """
        return self.sessionmaker()


class DatabaseServer:
    def __init__(
        self,
        engine: CanBeTurnedIntoEngine,
        schema: Migrator | None = None,
        debug=False,
    ) -> None:
        self._migrator = schema
        self._engine = _build_engine(engine)
        self._template_db_name: str | None = None

    @property
    def url(self) -> URL:
        return self._engine.url

    def ensure_is_ready(
        self, timeout: float = 30, interval: float = 0.5
    ) -> Self:
        deadline = time.monotonic() + timeout
        attempts = 0

        while True:
            try:
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return self
            except Exception as error:
                attempts += 1
                if time.monotonic() >= deadline:
                    raise DatabaseNotReadyError(
                        f"Reached the configured timeout of {timeout} seconds after {attempts} attempts connecting to the database."
                    ) from error
                time.sleep(interval)

    def create_database(
        self,
        prefix: str = "elefast",
        encoding: str = "utf8",
    ) -> Database:
        template_db = self._template_db_name
        if template_db is None:
            engine = _prepare_database(
                self._engine, encoding=encoding, prefix="elefast-template-db"
            )
            if self._migrator:
                with engine.begin() as connection:
                    self._migrator.migrate(connection)
                    connection.commit()
            engine.dispose()
            template_db = engine.url.database
            assert isinstance(template_db, str)
            self._template_db_name = template_db

        engine = _prepare_database(
            self._engine, encoding=encoding, prefix=prefix, template=template_db
        )
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
    engine: Engine,
    prefix: str = "elefast",
    encoding: str = "utf8",
    template: str | None = None,
) -> Engine:
    database = f"{prefix}-{uuid4()}"
    with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"{database}\" ENCODING '{encoding}' TEMPLATE template0"
            if template is None
            else f'CREATE DATABASE "{database}" WITH TEMPLATE "{template}" ENCODING \'{encoding}\''
        )
        connection.execute(text(statement))
        connection.commit()
    return create_engine(engine.url.set(database=database))
