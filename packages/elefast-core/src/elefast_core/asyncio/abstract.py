from __future__ import annotations
from contextlib import AbstractAsyncContextManager
from collections.abc import Callable

from abc import ABC, abstractmethod

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


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


class AsyncDatabaseServer(ABC):
    @property
    @abstractmethod
    def url(self) -> URL:
        pass

    @abstractmethod
    async def create_database(self) -> AsyncDatabase:
        pass

    @abstractmethod
    async def drop_database(self, name: str) -> None:
        pass
