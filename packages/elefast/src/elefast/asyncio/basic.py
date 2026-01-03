from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncEngine

from elefast.asyncio._utils import prepare_async_database
from elefast.asyncio.abstract import AsyncDatabase, AsyncDatabaseServer


class BasicAsyncDatabaseServer(AsyncDatabaseServer):
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @override
    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @override
    async def create_database(self) -> AsyncDatabase:
        engine = await prepare_async_database(self.engine)
        return AsyncDatabase(engine=engine, server=self)
