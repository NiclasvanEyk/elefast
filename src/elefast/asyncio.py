from __future__ import annotations

import time
from asyncio import sleep
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import uuid4

from sqlalchemy import URL, MetaData, NullPool, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from elefast.errors import DatabaseNotReadyError

type CanBeTurnedIntoAsyncEngine = AsyncEngine | URL | str


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
        self.name = self.engine.url.database

    async def __aexit__(self, exc_type, exc, tb):
        await self.drop()

    @property
    def url(self) -> URL:
        return self.engine.url

    async def drop(self) -> None:
        await self.engine.dispose()
        await self.server.drop_database(self.name)

    def session(self) -> AsyncSession:
        return self.sessionmaker()


class AsyncDatabaseServer:
    def __init__(
        self, engine: CanBeTurnedIntoAsyncEngine, metadata: MetaData | None = None
    ) -> None:
        self._metadata = metadata
        self._engine = _build_engine(engine)
        self._template_db_name: str | None = None

    @property
    def url(self) -> URL:
        return self._engine.url

    async def ensure_is_ready(
        self, timeout: int | float = 30, interval: int | float = 0.5
    ) -> None:
        deadline = time.monotonic() + timeout
        attempts = 0

        while True:
            try:
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return
            except Exception as error:
                attempts += 1
                if time.monotonic() >= deadline:
                    raise DatabaseNotReadyError(
                        f"Reached the configured timeout of {timeout} seconds after {attempts} attempts connecting to the database."
                    ) from error
                await sleep(interval)

    async def create_database(self) -> AsyncDatabase:
        template_db = self._template_db_name
        if template_db is None:
            engine = await _prepare_async_database(self._engine)
            if self._metadata:
                async with engine.begin() as connection:
                    await connection.run_sync(self._metadata.drop_all)
                    await connection.run_sync(self._metadata.create_all)
            await engine.dispose()
            template_db = engine.url.database
            assert isinstance(template_db, str)
            self._template_db_name = template_db

        engine = await _prepare_async_database(self._engine, template=template_db)
        return AsyncDatabase(engine=engine, server=self)

    async def drop_database(self, name: str) -> None:
        async with self._engine.begin() as connection:
            statement = f'DROP DATABASE "{name}"'
            await connection.execute(text(statement))


async def _prepare_async_database(
    engine: AsyncEngine, encoding: str = "utf8", template: str | None = None
) -> AsyncEngine:
    database = f"pytest-elephantastic-{uuid4()}"
    async with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"{database}\" ENCODING '{encoding}' TEMPLATE template0"
            if template is None
            else f'CREATE DATABASE "{database}" WITH TEMPLATE "{template}"'
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
