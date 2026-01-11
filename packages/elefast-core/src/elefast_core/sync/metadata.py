from typing import override

from sqlalchemy import URL, MetaData

from elefast_core.sync._utils import (
    drop_database,
    prepare_database,
    CanBeTurnedIntoEngine,
    build_engine,
    wait_for_db,
)
from elefast_core.sync.abstract import Database, DatabaseServer


class MetaDataBasedDatabaseServer(DatabaseServer):
    def __init__(self, engine: CanBeTurnedIntoEngine, metadata: MetaData) -> None:
        self._metadata = metadata
        self._engine = build_engine(engine)
        self._template_db_name: str | None = None

    @override
    @property
    def url(self) -> URL:
        return self._engine.url

    @override
    def ensure_is_ready(self) -> None:
        wait_for_db(self._engine)

    @override
    def create_database(self) -> Database:
        template_db = self._template_db_name
        if template_db is None:
            engine = prepare_database(self._engine)
            with engine.begin() as connection:
                self._metadata.drop_all(bind=connection)
                self._metadata.create_all(bind=connection)
            engine.dispose()
            template_db = engine.url.database
            assert isinstance(template_db, str)
            self._template_db_name = template_db

        engine = prepare_database(self._engine, template=template_db)
        return Database(engine=engine, server=self)

    @override
    def drop_database(self, name: str) -> None:
        drop_database(self._engine, name)
