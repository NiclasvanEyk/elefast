from __future__ import annotations

from typing import override

from sqlalchemy import URL

from elefast_core.asyncio._utils import (
    CanBeTurnedIntoAsyncEngine,
    build_engine,
    drop_async_database,
    prepare_async_database,
    wait_for_async_db,
)
from elefast_core.asyncio.abstract import AsyncDatabase, AsyncDatabaseServer


class BasicAsyncDatabaseServer(AsyncDatabaseServer):
    def __init__(self, engine: CanBeTurnedIntoAsyncEngine) -> None:
        self._engine = build_engine(engine)

    @override
    @property
    def url(self) -> URL:
        return self._engine.url

    @override
    async def ensure_is_ready(self) -> None:
        await wait_for_async_db(self._engine)

    @override
    async def create_database(self) -> AsyncDatabase:
        engine = await prepare_async_database(self._engine)
        return AsyncDatabase(engine=engine, server=self)

    @override
    async def drop_database(self, name: str) -> None:
        await drop_async_database(self._engine, name)
