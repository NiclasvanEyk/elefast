from typing import override

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine

from elefast.asyncio._utils import prepare_async_database
from elefast.asyncio.abstract import AsyncDatabase, AsyncDatabaseServer


class MetaDataBasedAsyncDatabaseServer(AsyncDatabaseServer):
    def __init__(self, engine: AsyncEngine, metadata: MetaData) -> None:
        self._metadata = metadata
        self._engine = engine

    @override
    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @override
    async def create_database(self) -> AsyncDatabase:
        engine = await prepare_async_database(self.engine)
        async with engine.begin() as connection:
            await connection.run_sync(self._metadata.drop_all)
            await connection.run_sync(self._metadata.create_all)
        return AsyncDatabase(engine=engine, server=self)
