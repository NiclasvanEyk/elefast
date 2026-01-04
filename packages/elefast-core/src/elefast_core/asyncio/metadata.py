from typing import override

from sqlalchemy import URL, MetaData

from elefast_core.asyncio._utils import (
    drop_async_database,
    prepare_async_database,
    CanBeTurnedIntoAsyncEngine,
    build_engine,
)
from elefast_core.asyncio.abstract import AsyncDatabase, AsyncDatabaseServer


class MetaDataBasedAsyncDatabaseServer(AsyncDatabaseServer):
    def __init__(self, engine: CanBeTurnedIntoAsyncEngine, metadata: MetaData) -> None:
        self._metadata = metadata
        self._engine = build_engine(engine)

    @override
    @property
    def url(self) -> URL:
        return self._engine.url

    @override
    async def create_database(self) -> AsyncDatabase:
        engine = await prepare_async_database(self._engine)
        async with engine.begin() as connection:
            await connection.run_sync(self._metadata.drop_all)
            await connection.run_sync(self._metadata.create_all)
        return AsyncDatabase(engine=engine, server=self)

    @override
    async def drop_database(self, name: str) -> None:
        await drop_async_database(self._engine, name)
