from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class AsyncDatabase:
    def __init__(self, engine: AsyncEngine, server: AsyncDatabaseServer) -> None:
        self.engine = engine
        self.server = server
        self.sessionmaker = async_sessionmaker(bind=self.engine)

    def session(self) -> AsyncSession:
        return self.sessionmaker()


class AsyncDatabaseServer(ABC):
    @property
    @abstractmethod
    def engine(self) -> AsyncEngine:
        pass

    @abstractmethod
    async def create_database(self) -> AsyncDatabase:
        pass
