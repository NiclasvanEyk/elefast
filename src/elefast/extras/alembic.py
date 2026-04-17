"""
Utility functions for working with [Alembic](https://alembic.sqlalchemy.org).
"""

from os import PathLike

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

from elefast.asyncio import AsyncMigrator
from elefast.sync import Migrator


def _upgrade_head(connection: Connection, config: Config) -> None:
    config.attributes["connection"] = connection
    config.attributes["ensure_connection"] = False
    command.upgrade(config, revision="head")


class AlembicMigrator(Migrator, AsyncMigrator):
    """
    Runs your migrations to create the testing database schema.
    """

    def __init__(self, config_path: PathLike[str]) -> None:
        self._config_path = config_path

    def migrate(self, connection: Connection) -> None:
        _upgrade_head(connection, self._config())

    def _config(self) -> Config:
        return (
            Config(toml_file=self._config_path)
            if str(self._config_path).endswith(".toml")
            else Config(file_=self._config_path)
        )

    async def migrate_async(self, connection: AsyncConnection) -> None:
        await connection.run_sync(_upgrade_head, self._config())
