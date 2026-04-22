from __future__ import annotations

import time
from asyncio import sleep
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Protocol, Self, TypeAlias
from uuid import uuid4

from sqlalchemy import URL, MetaData, NullPool, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.schema import CreateSchema

from elefast.errors import DatabaseNotReadyError

CanBeTurnedIntoAsyncEngine: TypeAlias = "AsyncEngine | URL | str"


class AsyncMigrator(Protocol):
    async def migrate_async(self, connection: AsyncConnection) -> None:
        pass


class AsyncMetadataMigrator(AsyncMigrator):
    def __init__(self, metadata: MetaData) -> None:
        self._metadata = metadata

    async def migrate_async(self, connection: AsyncConnection) -> None:
        schemas = {
            table.schema
            for table in self._metadata.tables.values()
            if table.schema is not None and table.schema != "public"
        }
        for schema in schemas:
            await connection.execute(CreateSchema(schema, if_not_exists=True))
        await connection.run_sync(self._metadata.drop_all)
        await connection.run_sync(self._metadata.create_all)


class AsyncDatabase(AbstractAsyncContextManager):
    def __init__(
        self,
        engine: AsyncEngine,
        server: AsyncDatabaseServer,
        sessionmaker_factory: Callable[
            [AsyncEngine], Callable[[], AsyncSession]
        ] = async_sessionmaker,
    ) -> None:
        self.engine = engine
        self.server = server
        self.sessionmaker = sessionmaker_factory(self.engine)
        assert self.engine.url.database
        self._name = self.engine.url.database

    async def __aexit__(self, exc_type, exc, tb):
        await self.drop()

    @property
    def url(self) -> URL:
        return self.engine.url

    @property
    def name(self) -> str:
        return self._name

    async def drop(self) -> None:
        await self.engine.dispose()
        await self.server.drop_database(self.name)

    def session(self) -> AsyncSession:
        return self.sessionmaker()


class AsyncDatabaseServer:
    def __init__(
        self, engine: CanBeTurnedIntoAsyncEngine, schema: AsyncMigrator | None = None
    ) -> None:
        self._migrator = schema
        self._engine = _build_engine(engine)
        self._template_db_name: str | None = None

    @property
    def url(self) -> URL:
        return self._engine.url

    async def ensure_is_ready(
        self, timeout: float = 30, interval: float = 0.5
    ) -> Self:
        deadline = time.monotonic() + timeout
        attempts = 0

        while True:
            try:
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return self
            except Exception as error:
                attempts += 1
                if time.monotonic() >= deadline:
                    raise DatabaseNotReadyError(
                        f"Reached the configured timeout of {timeout} seconds after {attempts} attempts connecting to the database."
                    ) from error
                await sleep(interval)

    async def create_database(
        self,
        prefix: str = "elefast",
        encoding: str = "utf8",
    ) -> AsyncDatabase:
        template_db = self._template_db_name
        if template_db is None:
            engine = await _prepare_async_database(
                self._engine, encoding=encoding, prefix="elefast-template-db"
            )
            if self._migrator:
                async with engine.begin() as connection:
                    await self._migrator.migrate_async(connection)
                    await connection.commit()
            await engine.dispose()
            template_db = engine.url.database
            assert isinstance(template_db, str)
            self._template_db_name = template_db

        engine = await _prepare_async_database(
            self._engine, encoding=encoding, prefix=prefix, template=template_db
        )
        return AsyncDatabase(engine=engine, server=self)

    async def drop_database(self, name: str) -> None:
        async with self._engine.begin() as connection:
            statement = f'DROP DATABASE "{name}"'
            await connection.execute(text(statement))


async def _prepare_async_database(
    engine: AsyncEngine,
    prefix: str = "elefast",
    encoding: str = "utf8",
    template: str | None = None,
) -> AsyncEngine:
    database = f"{prefix}-{uuid4()}"
    async with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"{database}\" ENCODING '{encoding}' TEMPLATE template0"
            if template is None
            else f'CREATE DATABASE "{database}" WITH TEMPLATE "{template}" ENCODING \'{encoding}\''
        )
        await connection.execute(text(statement))
        await connection.commit()
    return create_async_engine(engine.url.set(database=database))


def _build_engine(input: CanBeTurnedIntoAsyncEngine) -> AsyncEngine:
    if isinstance(input, AsyncEngine):
        return input
    if isinstance(input, URL | str):
        return create_async_engine(
            input, isolation_level="autocommit", poolclass=NullPool
        )
    raise TypeError()
