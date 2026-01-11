from __future__ import annotations
from contextlib import AbstractContextManager
from collections.abc import Callable

from abc import ABC, abstractmethod

from sqlalchemy import URL, Engine
from sqlalchemy.orm import Session, sessionmaker


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


class DatabaseServer(ABC):
    @property
    @abstractmethod
    def url(self) -> URL:
        pass

    @abstractmethod
    def ensure_is_ready(self) -> None:
        pass

    @abstractmethod
    def create_database(self) -> Database:
        pass

    @abstractmethod
    def drop_database(self, name: str) -> None:
        pass
