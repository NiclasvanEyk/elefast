from __future__ import annotations

from typing import override

from sqlalchemy import URL

from elefast_core.sync._utils import (
    CanBeTurnedIntoEngine,
    build_engine,
    prepare_database,
    wait_for_db,
)
from elefast_core.sync._utils import (
    drop_database as utils_drop_database,
)
from elefast_core.sync.abstract import Database, DatabaseServer


class BasicDatabaseServer(DatabaseServer):
    def __init__(self, engine: CanBeTurnedIntoEngine) -> None:
        self._engine = build_engine(engine)

    @override
    @property
    def url(self) -> URL:
        return self._engine.url

    @override
    def ensure_is_ready(self) -> None:
        wait_for_db(self._engine)

    @override
    def create_database(self) -> Database:
        engine = prepare_database(self._engine)
        return Database(engine=engine, server=self)

    @override
    def drop_database(self, name: str) -> None:
        utils_drop_database(self._engine, name)
